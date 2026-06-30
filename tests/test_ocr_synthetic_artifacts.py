from __future__ import annotations

import json
from pathlib import Path

from serial_extractor.app import apply_quantity_validation, extract_pdf
from serial_extractor.models import ExtractionOptions, TextSpan


ARTIFACT_DIR = Path("test_artifacts/ocr_synthetic/v2.0.0")


class FixtureOcrEngine:
    def __init__(self, spans: list[dict[str, object]]) -> None:
        self.spans = [
            TextSpan(
                text=str(item["text"]),
                page=int(item["page"]),
                bbox=tuple(float(value) for value in item["bbox"]),
                confidence=float(item["confidence"]),
                backend="paddleocr",
            )
            for item in spans
        ]
        self.calls: list[tuple[Path, list[int]]] = []

    def recognize_pdf(self, pdf_path: Path, page_numbers: list[int]) -> list[TextSpan]:
        self.calls.append((pdf_path, page_numbers))
        wanted = set(page_numbers)
        return [span for span in self.spans if span.page in wanted]


def load_case(name: str) -> tuple[Path, FixtureOcrEngine]:
    manifest_path = ARTIFACT_DIR / "manifest.json"
    assert manifest_path.exists(), "Run scripts/generate_ocr_synthetic_artifacts.py first."
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    case = manifest["cases"][name]
    return ARTIFACT_DIR / case["pdf"], FixtureOcrEngine(case["spans"])


def test_cross_page_ocr_table_continuation_artifact() -> None:
    pdf_path, engine = load_case("cross_page_table")

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="force", ocr_min_confidence=0.90),
        ocr_engine=engine,
    )
    apply_quantity_validation(result.records, result.warnings)

    assert engine.calls == [(pdf_path, [1, 2])]
    assert [
        (record.part_number, record.part_name, record.serial_number, record.order_qty, record.qty_check)
        for record in result.records
    ] == [
        ("PN-101", "CROSS PAGE MODULE", "FA70000001001", 3, "OK"),
        ("PN-101", "CROSS PAGE MODULE", "FA70000001002", 3, "OK"),
        ("PN-101", "CROSS PAGE MODULE", "FA70000001003", 3, "OK"),
    ]


def test_ocr_marker_policy_artifact_s_n_wins_and_metadata_is_excluded() -> None:
    pdf_path, engine = load_case("marker_policy")

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="force", ocr_min_confidence=0.90),
        ocr_engine=engine,
    )

    assert [record.serial_number for record in result.records] == [
        "FA70000002001",
        "LBADVA70000003001",
    ]
    assert "LBADVA70000002001" not in {record.serial_number for record in result.records}
    assert "SP260073" not in {record.serial_number for record in result.records}
    assert all("DEUTUS33" not in record.serial_number for record in result.records)


def test_low_confidence_ocr_artifact_goes_to_review_with_part_context() -> None:
    pdf_path, engine = load_case("rotated_low_confidence")

    result = extract_pdf(
        pdf_path,
        options=ExtractionOptions(ocr_mode="force", ocr_min_confidence=0.90),
        ocr_engine=engine,
    )

    assert result.records == []
    assert len(result.review_candidates) == 1
    review = result.review_candidates[0]
    assert review.raw_text == "FA7O000004001"
    assert review.normalized_value == "FA7O000004001"
    assert review.part_number == "PN-404"
    assert review.part_name == "ROTATED MODULE"
    assert review.order_qty == 1
