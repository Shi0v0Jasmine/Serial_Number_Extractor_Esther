from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas


ARTIFACT_DIR = Path("test_artifacts/ocr_synthetic/v2.0.0")
PAGE_SIZE = (1800, 900)


def _font(size: int):
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size)
    return ImageFont.load_default()


def _span(text: str, page: int, x0: float, top: float, confidence: float = 0.99) -> dict[str, object]:
    return {
        "text": text,
        "page": page,
        "bbox": [x0, top, x0 + max(60, len(text) * 24), top + 52],
        "confidence": confidence,
    }


def _draw_page(lines: list[tuple[int, int, str]], rotate: bool = False) -> Image.Image:
    image = Image.new("RGB", PAGE_SIZE, "white")
    draw = ImageDraw.Draw(image)
    font = _font(42)
    for x, y, text in lines:
        draw.text((x, y), text, fill="black", font=font)
    if rotate:
        return image.rotate(90, expand=True, fillcolor="white")
    return image


def _write_image_pdf(path: Path, pages: list[Image.Image]) -> None:
    pdf = canvas.Canvas(str(path), pagesize=PAGE_SIZE)
    for image in pages:
        pdf.drawImage(ImageReader(image), 0, 0, width=PAGE_SIZE[0], height=PAGE_SIZE[1])
        pdf.showPage()
    pdf.save()


def build_cross_page_table() -> dict[str, object]:
    pdf_path = ARTIFACT_DIR / "cross_page_table.pdf"
    pages = [
        _draw_page(
            [
                (80, 120, "PART NUMBER"),
                (420, 120, "PART NAME"),
                (1050, 120, "QTY"),
                (1320, 120, "S/N"),
                (80, 260, "PN-101"),
                (420, 260, "CROSS PAGE MODULE"),
                (1050, 260, "3"),
                (1320, 260, "FA70000001001"),
            ]
        ),
        _draw_page(
            [
                (1320, 160, "FA70000001002"),
                (1320, 280, "FA70000001003"),
            ]
        ),
    ]
    _write_image_pdf(pdf_path, pages)
    spans = [
        _span("PART NUMBER", 1, 80, 120),
        _span("PART NAME", 1, 420, 120),
        _span("QTY", 1, 1050, 120),
        _span("S/N", 1, 1320, 120),
        _span("PN-101", 1, 80, 260),
        _span("CROSS PAGE MODULE", 1, 420, 260),
        _span("3", 1, 1050, 260),
        _span("FA70000001001", 1, 1320, 260),
        _span("FA70000001002", 2, 1320, 160),
        _span("FA70000001003", 2, 1320, 280),
    ]
    return {"pdf": pdf_path.name, "spans": spans}


def build_marker_policy_cases() -> dict[str, object]:
    pdf_path = ARTIFACT_DIR / "marker_policy_cases.pdf"
    pages = [
        _draw_page(
            [
                (80, 100, "500 1042004437-01"),
                (80, 170, "PART-A"),
                (80, 250, "S/N:"),
                (220, 250, "FA70000002001"),
                (80, 330, "USI Code:"),
                (300, 330, "LBADVA70000002001"),
                (80, 470, "Packing List"),
                (80, 540, "SP260073"),
                (80, 610, "BIC / Swift Code: DEUTUS33"),
            ]
        ),
        _draw_page(
            [
                (80, 100, "501 1042004438-01"),
                (80, 170, "PART-B"),
                (80, 250, "USI Code:"),
                (300, 250, "LBADVA70000003001"),
            ]
        ),
    ]
    _write_image_pdf(pdf_path, pages)
    spans = [
        _span("500 1042004437-01", 1, 80, 100),
        _span("PART-A", 1, 80, 170),
        _span("S/N:", 1, 80, 250),
        _span("FA70000002001", 1, 220, 250),
        _span("USI Code:", 1, 80, 330),
        _span("LBADVA70000002001", 1, 300, 330),
        _span("Packing List", 1, 80, 470),
        _span("SP260073", 1, 80, 540),
        _span("BIC / Swift Code: DEUTUS33", 1, 80, 610),
        _span("501 1042004438-01", 2, 80, 100),
        _span("PART-B", 2, 80, 170),
        _span("USI Code:", 2, 80, 250),
        _span("LBADVA70000003001", 2, 300, 250),
    ]
    return {"pdf": pdf_path.name, "spans": spans}


def build_rotated_and_low_confidence_case() -> dict[str, object]:
    pdf_path = ARTIFACT_DIR / "rotated_low_confidence.pdf"
    page = _draw_page(
        [
            (80, 120, "PART NUMBER"),
            (420, 120, "PART NAME"),
            (1050, 120, "QTY"),
            (1320, 120, "S/N"),
            (80, 260, "PN-404"),
            (420, 260, "ROTATED MODULE"),
            (1050, 260, "1"),
            (1320, 260, "FA7O000004001"),
        ],
        rotate=True,
    )
    _write_image_pdf(pdf_path, [page])
    spans = [
        _span("PART NUMBER", 1, 80, 120),
        _span("PART NAME", 1, 420, 120),
        _span("QTY", 1, 1050, 120),
        _span("S/N", 1, 1320, 120),
        _span("PN-404", 1, 80, 260),
        _span("ROTATED MODULE", 1, 420, 260),
        _span("1", 1, 1050, 260),
        _span("FA7O000004001", 1, 1320, 260, confidence=0.72),
    ]
    return {"pdf": pdf_path.name, "spans": spans}


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": "2.0.0",
        "cases": {
            "cross_page_table": build_cross_page_table(),
            "marker_policy": build_marker_policy_cases(),
            "rotated_low_confidence": build_rotated_and_low_confidence_case(),
        },
    }
    (ARTIFACT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    print(ARTIFACT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
