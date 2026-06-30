from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter

from serial_extractor.models import ExtractionOptions, TextSpan
from serial_number_extractor import apply_quantity_validation, extract_pdf


class FakeOcrEngine:
    def __init__(self, spans: list[TextSpan]) -> None:
        self.spans = spans
        self.calls: list[tuple[Path, list[int]]] = []

    def recognize_pdf(self, pdf_path: Path, page_numbers: list[int]) -> list[TextSpan]:
        self.calls.append((pdf_path, page_numbers))
        return self.spans


def make_scanned_pdf(path: Path) -> None:
    image = Image.new("RGB", (800, 400), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 20), "scanned packing list", fill="black")
    pdf = canvas.Canvas(str(path), pagesize=(800, 400))
    pdf.drawImage(ImageReader(image), 0, 0, width=800, height=400)
    pdf.save()


def make_native_pdf(path: Path) -> None:
    pdf = canvas.Canvas(str(path), pagesize=(800, 400))
    pdf.drawString(20, 350, "Native packing list with selectable text")
    pdf.save()


def ocr_table_spans(serial_confidence: float = 0.99, page: int = 1) -> list[TextSpan]:
    def make(text: str, x0: float, top: float, confidence: float = 0.99) -> TextSpan:
        return TextSpan(text, page, (x0, top, x0 + max(30, len(text) * 6), top + 12), confidence, "paddleocr")

    return [
        make("Part Number", 10, 100),
        make("Part Name", 180, 100),
        make("Quantity", 470, 100),
        make("S/N", 600, 100),
        make("PN-001", 10, 130),
        make("Generic Optical Module", 180, 130),
        make("1", 470, 130),
        make("FA70000000001", 600, 130, serial_confidence),
    ]


def test_auto_ocr_extracts_scanned_page_with_fake_engine(tmp_path) -> None:
    pdf_path = tmp_path / "scan.pdf"
    make_scanned_pdf(pdf_path)
    engine = FakeOcrEngine(ocr_table_spans())

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="auto"),
        ocr_engine=engine,
    )
    apply_quantity_validation(result.records, result.warnings)

    assert engine.calls == [(pdf_path, [1])]
    assert len(result.records) == 1
    assert result.records[0].part_number == "PN-001"
    assert result.records[0].serial_number == "FA70000000001"
    assert result.records[0].qty_check == "OK"
    assert result.records[0].backend == "paddleocr"
    assert result.review_candidates == []


def test_low_confidence_ocr_serial_stays_out_of_main_output(tmp_path) -> None:
    pdf_path = tmp_path / "scan.pdf"
    make_scanned_pdf(pdf_path)
    engine = FakeOcrEngine(ocr_table_spans(serial_confidence=0.70))

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="auto", ocr_min_confidence=0.90),
        ocr_engine=engine,
    )

    assert result.records == []
    assert len(result.review_candidates) == 1
    assert result.review_candidates[0].normalized_value == "FA70000000001"
    assert result.review_candidates[0].reason == "ocr_confidence_below_threshold"
    assert result.review_candidates[0].part_number == "PN-001"
    assert result.review_candidates[0].part_name == "Generic Optical Module"
    assert result.review_candidates[0].order_qty == 1


def test_ocr_off_reports_scanned_page_without_calling_engine(tmp_path) -> None:
    pdf_path = tmp_path / "scan.pdf"
    make_scanned_pdf(pdf_path)
    engine = FakeOcrEngine(ocr_table_spans())

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="off"),
        ocr_engine=engine,
    )

    assert engine.calls == []
    assert result.records == []
    assert any("OCR is disabled" in warning for warning in result.warnings)


def test_force_ocr_processes_page_with_native_text(tmp_path) -> None:
    pdf_path = tmp_path / "native.pdf"
    make_native_pdf(pdf_path)
    engine = FakeOcrEngine(ocr_table_spans())

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="force"),
        ocr_engine=engine,
    )

    assert engine.calls == [(pdf_path, [1])]
    assert [record.serial_number for record in result.records] == ["FA70000000001"]


def test_force_ocr_keeps_usable_native_serials_as_fallback(tmp_path) -> None:
    pdf_path = tmp_path / "native-serial.pdf"
    pdf = canvas.Canvas(str(pdf_path), pagesize=(800, 400))
    pdf.drawString(20, 350, "S/N: FA70000000002")
    pdf.save()
    engine = FakeOcrEngine(ocr_table_spans())

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="force"),
        ocr_engine=engine,
    )

    assert engine.calls == [(pdf_path, [1])]
    assert [record.serial_number for record in result.records] == ["FA70000000002"]
    assert result.records[0].backend == "native"


def test_corrupt_pdf_returns_warning_instead_of_raising(tmp_path) -> None:
    pdf_path = tmp_path / "corrupt.pdf"
    pdf_path.write_bytes(b"not a pdf")

    result = extract_pdf(pdf_path, options=ExtractionOptions(ocr_mode="off"))

    assert result.records == []
    assert any("failed to open PDF" in warning for warning in result.warnings)


def test_password_encrypted_pdf_returns_actionable_warning(tmp_path) -> None:
    source = tmp_path / "source.pdf"
    encrypted = tmp_path / "encrypted.pdf"
    make_native_pdf(source)
    reader = PdfReader(source)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt("secret")
    with encrypted.open("wb") as handle:
        writer.write(handle)

    result = extract_pdf(encrypted, options=ExtractionOptions(ocr_mode="off"))

    assert result.records == []
    assert any("requires a password" in warning for warning in result.warnings)


def test_auto_ocr_only_processes_scanned_page_in_mixed_pdf(tmp_path) -> None:
    image = Image.new("RGB", (800, 400), "white")
    draw = ImageDraw.Draw(image)
    draw.text((20, 20), "scanned second page", fill="black")
    pdf_path = tmp_path / "mixed.pdf"
    pdf = canvas.Canvas(str(pdf_path), pagesize=(800, 400))
    pdf.drawString(20, 350, "S/N: FA70000000002")
    pdf.showPage()
    pdf.drawImage(ImageReader(image), 0, 0, width=800, height=400)
    pdf.save()
    engine = FakeOcrEngine(ocr_table_spans(page=2))

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="auto"),
        ocr_engine=engine,
    )

    assert engine.calls == [(pdf_path, [2])]
    assert {record.serial_number for record in result.records} == {
        "FA70000000001",
        "FA70000000002",
    }
    assert {
        record.serial_number: record.backend for record in result.records
    } == {
        "FA70000000001": "paddleocr",
        "FA70000000002": "native",
    }
    ocr_record = next(
        record for record in result.records if record.serial_number == "FA70000000001"
    )
    assert (ocr_record.part_number, ocr_record.part_name, ocr_record.order_qty) == (
        "PN-001",
        "Generic Optical Module",
        1,
    )


def test_rotated_native_page_remains_extractable(tmp_path) -> None:
    source = tmp_path / "source.pdf"
    rotated = tmp_path / "rotated.pdf"
    pdf = canvas.Canvas(str(source), pagesize=(800, 400))
    pdf.drawString(20, 350, "S/N: FA70000000003")
    pdf.save()
    reader = PdfReader(source)
    writer = PdfWriter()
    writer.add_page(reader.pages[0].rotate(90))
    with rotated.open("wb") as handle:
        writer.write(handle)

    result = extract_pdf(rotated, options=ExtractionOptions(ocr_mode="off"))

    assert [record.serial_number for record in result.records] == ["FA70000000003"]
