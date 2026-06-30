from __future__ import annotations

import pytest

from serial_number_extractor import apply_quantity_validation, extract_document_records


@pytest.mark.parametrize(
    ("case_name", "lines", "expected"),
    [
        (
            "ruid_range",
            [
                "Packing list",
                "GE02-MC-BD40-3149",
                "Item code 010280-A",
                "Serial Number Range",
                "3 B2426041342001-003",
            ],
            ("010280-A", "GE02-MC-BD40-3149", 3, 3, "OK"),
        ),
        (
            "smartoptics",
            [
                "TQD013-TUNC-SO85043100 2 PCS",
                "QSFP-DD 400G OpenZR+",
                "VB000001",
                "VB000002",
            ],
            ("TQD013-TUNC-SO", "QSFP-DD 400G OpenZR+", 2, 2, "OK"),
        ),
        (
            "dtc",
            [
                "SFP 1.25G 850nm 550m",
                "ADVA",
                "0061705844-03",
                "2",
                "Serial numbers are:",
                "FA70000000001",
                "FA70000000002",
            ],
            ("0061705844-03", "SFP 1.25G 850nm 550m", 2, 2, "OK"),
        ),
        (
            "ciena",
            [
                "1 2 EA 170-5164-902",
                "5164 SFP28 QSFP-DD EXT TEMP",
                "WX00000001",
                "WX00000002",
            ],
            ("170-5164-902", "5164 SFP28 QSFP-DD EXT TEMP", 2, 2, "OK"),
        ),
        (
            "pure_it",
            [
                "SFP-25G-SR-S-PO (Quantité 2): SFP-25G-SR-S-PO",
                "PLS000001",
                "PLS000002",
            ],
            ("SFP-25G-SR-S-PO", "SFP-25G-SR-S-PO", 2, 2, "OK"),
        ),
    ],
)
def test_vendor_contracts(case_name, lines, expected, line_pages) -> None:
    records = extract_document_records(f"{case_name}.pdf", lines, line_pages(lines), set())
    warnings: list[str] = []
    apply_quantity_validation(records, warnings)

    part_number, part_name, qty, count, status = expected
    assert len(records) == count
    assert {record.part_number for record in records} == {part_number}
    assert {record.part_name for record in records} == {part_name}
    assert {record.order_qty for record in records} == {qty}
    assert {record.serial_count for record in records} == {count}
    assert {record.qty_check for record in records} == {status}
    assert warnings == []
