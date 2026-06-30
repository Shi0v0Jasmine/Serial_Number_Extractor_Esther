from __future__ import annotations

import os
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from serial_extractor.app import apply_quantity_validation, extract_pdf
from serial_extractor.models import ExtractionOptions, TextSpan
from serial_extractor.ocr_worker import recognize_pdf


pytestmark = [
    pytest.mark.ocr_integration,
    pytest.mark.skipif(
        os.environ.get("RUN_PADDLEOCR_TESTS") != "1",
        reason="Set RUN_PADDLEOCR_TESTS=1 to run the pinned PaddleOCR integration.",
    ),
]


def _font(size: int):
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    pytest.skip("No deterministic TrueType font is available.")


def make_clear_table_scan(path: Path) -> None:
    image = Image.new("RGB", (2400, 700), "white")
    draw = ImageDraw.Draw(image)
    header_font = _font(42)
    value_font = _font(48)
    columns = [80, 430, 1500, 1800]
    headers = ["MATERIAL", "DESCRIPTION", "QTY", "SERIAL"]
    values = ["PN-001", "GENERIC MODULE", "1 PCS", "FA70000000001"]
    for x, text in zip(columns, headers, strict=True):
        draw.text((x, 130), text, fill="black", font=header_font)
    for x, text in zip(columns, values, strict=True):
        draw.text((x, 280), text, fill="black", font=value_font)

    pdf = canvas.Canvas(str(path), pagesize=(2400, 700))
    pdf.drawImage(ImageReader(image), 0, 0, width=2400, height=700)
    pdf.save()


class LocalPaddleEngine:
    def recognize_pdf(self, pdf_path: Path, page_numbers: list[int]) -> list[TextSpan]:
        return [
            TextSpan(
                text=str(item["text"]),
                page=int(item["page"]),
                bbox=tuple(item["bbox"]),
                confidence=float(item["confidence"]),
                backend="paddleocr",
            )
            for item in recognize_pdf(pdf_path, page_numbers)
        ]


def test_paddleocr_clear_scan_reaches_verified_main_output(tmp_path) -> None:
    pdf_path = tmp_path / "clear-scan.pdf"
    make_clear_table_scan(pdf_path)

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="force", ocr_min_confidence=0.90),
        ocr_engine=LocalPaddleEngine(),
    )
    apply_quantity_validation(result.records, result.warnings)

    assert [
        (
            record.part_number,
            record.part_name,
            record.serial_number,
            record.order_qty,
            record.qty_check,
        )
        for record in result.records
    ] == [
        ("PN-001", "GENERIC MODULE", "FA70000000001", 1, "OK")
    ]
    assert result.review_candidates == []
