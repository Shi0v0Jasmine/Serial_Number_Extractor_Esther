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
                "Product QuantitySerial number EU customs ref.no:",
                "TQD013-TUNC-SO115080 2 PCS85176200",
                "QSFP-DD 400G OpenZR+ 100GE 1310nm",
                "TQD013-TUNC-SO",
                "VB000001",
                "VB000002",
            ],
            ("115080", "TQD013-TUNC-SO", 2, 2, "OK"),
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


def test_smartoptics_product_rows_and_cross_page_continuations() -> None:
    lines = [
        "Product QuantitySerial number EU customs ref.no:",
        "112917 3 PCSDCP-2-FB/HW 85176200",
        "Base HW, 1RU, 2-slot chassis, mgt board",
        "*K1000DCP00001*K1000DCP00001",
        "*K1000DCP00002*K1000DCP00002",
        "Product QuantitySerial number EU customs ref.no:",
        "*K1000DCP00003*K1000DCP00003",
        "100719 DCP-2-PSU-AC-FB 85043100 2 PCS",
        "AC Power Supply for DCP platform",
        "*G1000001NA000000001*G1000001NA000000001",
        "Product QuantitySerial number EU customs ref.no:",
        "*G1000001NA000000002*G1000001NA000000002",
    ]
    pages = [1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 3, 3]

    records = extract_document_records("smartoptics-packing-slip.pdf", lines, pages, set())
    warnings: list[str] = []
    apply_quantity_validation(records, warnings)

    assert len(records) == 5
    assert not {"85043100", "85176200", "100GE", "1310NM"}.intersection(
        record.serial_number for record in records
    )

    first_part = [record for record in records if record.part_number == "112917"]
    second_part = [record for record in records if record.part_number == "100719"]

    assert [record.serial_number for record in first_part] == [
        "K1000DCP00001",
        "K1000DCP00002",
        "K1000DCP00003",
    ]
    assert {record.part_name for record in first_part} == {"DCP-2-FB/HW"}
    assert {record.order_qty for record in first_part} == {3}
    assert {record.serial_count for record in first_part} == {3}
    assert {record.qty_check for record in first_part} == {"OK"}

    assert [record.serial_number for record in second_part] == [
        "G1000001NA000000001",
        "G1000001NA000000002",
    ]
    assert {record.part_name for record in second_part} == {"DCP-2-PSU-AC-FB"}
    assert {record.order_qty for record in second_part} == {2}
    assert {record.serial_count for record in second_part} == {2}
    assert {record.qty_check for record in second_part} == {"OK"}
    assert warnings == []
