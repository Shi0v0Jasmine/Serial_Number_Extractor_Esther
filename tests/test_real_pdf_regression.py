from __future__ import annotations

import os
import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

import pytest

from serial_number_extractor import apply_quantity_validation, extract_pdf


BASELINE_PATH = Path(__file__).parent / "fixtures" / "real_pdf_baseline.json"


def load_baseline() -> dict[str, object]:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def configured_real_roots() -> list[Path]:
    value = os.environ.get("SERIAL_EXTRACTOR_REAL_PDF_ROOTS", "")
    return [Path(item) for item in value.split(os.pathsep) if item]


def configured_root(index: int) -> Path:
    roots = configured_real_roots()
    if len(roots) <= index:
        pytest.skip("Local commercial PDF roots are not configured.")
    root = roots[index]
    if not root.is_dir():
        pytest.skip(f"Configured commercial PDF root does not exist: {root}")
    return root


def pdfs_in_root(root: Path) -> list[Path]:
    paths = sorted({*root.glob("*.pdf"), *root.glob("*.PDF")})
    if not paths:
        pytest.skip(f"No PDFs found in configured root: {root}")
    return paths


@lru_cache(maxsize=None)
def extract_records_for_path(path: str):
    result = extract_pdf(Path(path))
    apply_quantity_validation(result.records, result.warnings)
    return tuple(result.records)


def extract_records_for_paths(paths: list[Path]):
    records = []
    warnings: list[str] = []
    for path in paths:
        result = extract_pdf(path)
        records.extend(result.records)
        warnings.extend(result.warnings)
    apply_quantity_validation(records, warnings)
    return records, warnings


def all_configured_pdfs() -> list[Path]:
    paths: list[Path] = []
    for root in configured_real_roots():
        if root.is_dir():
            paths.extend(pdfs_in_root(root))
    if not paths:
        pytest.skip("Local commercial PDF roots are not configured.")
    return paths


@pytest.mark.real_pdf
def test_eci_real_pdf_is_layout_mapped_and_verified() -> None:
    baseline = load_baseline()
    expected_groups = {tuple(item) for item in baseline["eci_blocks"]}
    for path in all_configured_pdfs():
        records = list(extract_records_for_path(str(path)))
        groups = Counter(
            (
                record.part_number,
                record.part_name,
                record.order_qty,
                record.serial_count,
                record.qty_check,
            )
            for record in records
        )
        if set(groups) == expected_groups:
            assert len(records) == 15
            assert Counter(record.qty_check for record in records) == {"OK": 15}
            assert {record.block_source for record in records} == {"generic_layout"}
            return
    pytest.fail("ECI layout-mapped commercial PDF was not found in configured roots.")


@pytest.mark.real_pdf
def test_original_sample_root_matches_approved_total() -> None:
    baseline = load_baseline()
    paths = pdfs_in_root(configured_root(0))
    records, _ = extract_records_for_paths(paths)

    assert len(paths) == baseline["base_pdf_count"]
    assert len(records) == baseline["base_total"]
    assert Counter(record.qty_check for record in records) == {"OK": baseline["base_total"]}


@pytest.mark.real_pdf
def test_adtran_fix_root_matches_approved_total() -> None:
    baseline = load_baseline()
    paths = pdfs_in_root(configured_root(1))
    records, _ = extract_records_for_paths(paths)

    assert len(paths) == baseline["adtran_fix_pdf_count"]
    assert len(records) == baseline["adtran_fix_total"]
    assert Counter(record.qty_check for record in records) == {"OK": baseline["adtran_fix_total"]}


@pytest.mark.real_pdf
def test_all_nine_commercial_pdfs_match_v2_semantic_baseline() -> None:
    baseline = load_baseline()
    paths = [*pdfs_in_root(configured_root(0)), *pdfs_in_root(configured_root(1))]
    records, _ = extract_records_for_paths(paths)

    assert len(records) == baseline["grand_total"]
    assert Counter(record.qty_check for record in records) == {"OK": baseline["grand_total"]}
    assert not {
        record.part_number
        for record in records
    }.intersection(baseline["forbidden_part_numbers"])
    assert not [record.serial_number for record in records if record.serial_number.endswith("SN")]
