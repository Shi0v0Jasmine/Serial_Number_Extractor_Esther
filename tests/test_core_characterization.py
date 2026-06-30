from __future__ import annotations

import pytest
from hypothesis import given, strategies as st

from serial_number_extractor import (
    apply_quantity_validation,
    expand_serial_range,
    extract_document_records,
    is_part_number_like,
    normalize_serial,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (" SN:FA70261201473 ", "FA70261201473"),
        ("FA70261201473SN", "FA70261201473"),
        ("*VB000001*", "VB000001"),
        ("s/n:vk000001", "VK000001"),
    ],
)
def test_normalize_serial_characterization(raw: str, expected: str) -> None:
    assert normalize_serial(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("B2426041342001-003", ["B2426041342001", "B2426041342002", "B2426041342003"]),
        ("B0000000098-102", ["B0000000098", "B0000000099", "B0000000100", "B0000000101", "B0000000102"]),
        ("B0000000001-0000", []),
    ],
)
def test_expand_serial_range_characterization(raw: str, expected: list[str]) -> None:
    assert expand_serial_range(raw) == expected


def test_serial_range_enforces_5000_item_limit() -> None:
    assert len(expand_serial_range("B0000000001-5000")) == 5000
    assert expand_serial_range("B0000000001-5001") == []


@given(
    start=st.integers(min_value=1, max_value=999_900),
    count=st.integers(min_value=1, max_value=50),
)
def test_expanded_ranges_are_contiguous_and_unique(start: int, count: int) -> None:
    end = start + count - 1
    width = 10
    raw = f"B{start:0{width}d}-{end:0{width}d}"
    expanded = expand_serial_range(raw)
    assert len(expanded) == count
    assert len(set(expanded)) == count
    assert expanded[0] == f"B{start:0{width}d}"
    assert expanded[-1] == f"B{end:0{width}d}"


def test_adtran_parent_part_and_position_qty(line_pages) -> None:
    serials = [f"FA7000000{value:04d}" for value in range(1, 14)]
    lines = [
        "500 BC00000647",
        "F7/9TCE-PCN-10GU+10G&1P-L",
        "Data Trans. Card (TCE)",
        "This Position Line Contains:",
        "Qty Material Mat. Desc. / Custmer Mat. Desc.",
        "13 1063707680-11 F7/9TCE-PCN-10GU+10G",
        "SN:" + serials[0],
        *serials[1:],
        "13 13 0 782.28 10,169.64",
    ]

    records = extract_document_records("adtran.pdf", lines, line_pages(lines), set())
    warnings: list[str] = []
    apply_quantity_validation(records, warnings)

    assert len(records) == 13
    assert {record.part_number for record in records} == {"BC00000647"}
    assert {record.part_name for record in records} == {"F7/9TCE-PCN-10GU+10G&1P-L"}
    assert {record.order_qty for record in records} == {13}
    assert {record.qty_check for record in records} == {"OK"}
    assert warnings == []


def test_sn_wins_over_usi_in_same_document(line_pages) -> None:
    lines = [
        "1 1042004437-01",
        "F150/ADV/XG120PRO/FAN-EXH",
        "SN:",
        "FA70000000001",
        "USI Code:",
        "LBADVA70000000001",
        "1 1 0 10.00 10.00",
    ]

    records = extract_document_records("adtran.pdf", lines, line_pages(lines), set())

    assert [record.serial_number for record in records] == ["FA70000000001"]


def test_usi_is_used_when_no_primary_serial_marker(line_pages) -> None:
    lines = [
        "1 1042004437-01",
        "F150/ADV/XG120PRO/FAN-EXH",
        "USI Code:",
        "LBADVA70000000001",
        "1 1 0 10.00 10.00",
    ]

    records = extract_document_records("adtran.pdf", lines, line_pages(lines), set())

    assert [record.serial_number for record in records] == ["LBADVA70000000001"]


def test_sn_priority_is_scoped_to_the_same_product_block(line_pages) -> None:
    lines = [
        "1 1042004437-01",
        "F150/ADV/XG120PRO/FAN-EXH",
        "S/N:",
        "FA70000000001",
        "USI Code:",
        "LBADVA70000000001",
        "1 1 0 10.00 10.00",
        "2 1042004438-01",
        "F150/ADV/XG120PRO/FAN-INT",
        "USI Code:",
        "LBADVA70000000002",
        "1 1 0 10.00 10.00",
    ]

    records = extract_document_records("adtran.pdf", lines, line_pages(lines), set())

    assert [record.serial_number for record in records] == [
        "FA70000000001",
        "LBADVA70000000002",
    ]


def test_generic_serial_marker_accepts_unknown_alphanumeric_format(line_pages) -> None:
    lines = [
        "Packing list",
        "S/N:",
        "ZX9A001",
    ]

    records = extract_document_records("unknown.pdf", lines, line_pages(lines), set())

    assert [record.serial_number for record in records] == ["ZX9A001"]
    assert records[0].method == "marker_alphanumeric"


def test_marker_context_rejects_business_identifiers(line_pages) -> None:
    lines = [
        "S/N:",
        "Commodity Code: 85176200",
        "Activation ID: ABC12345",
        "Order Number: 990183217",
        "Total Price: 12345.67",
    ]

    records = extract_document_records("unknown.pdf", lines, line_pages(lines), set())

    assert records == []


@pytest.mark.parametrize(
    "marker",
    ["S/N:", "s/n", "Serial No.", "Serial number:", "LOT/SERIAL"],
)
def test_generic_marker_variants(marker, line_pages) -> None:
    lines = [marker, "ZX9A001"]

    records = extract_document_records("marker.pdf", lines, line_pages(lines), set())

    assert [record.serial_number for record in records] == ["ZX9A001"]


def test_quantity_mismatch_is_exportable_and_warned(line_pages) -> None:
    lines = [
        "SFP 1.25G 850nm 550m",
        "ADVA",
        "0061705844-03",
        "2",
        "Serial numbers are:",
        "FA70000000001",
    ]
    records = extract_document_records("mismatch.pdf", lines, line_pages(lines), set())
    warnings: list[str] = []

    apply_quantity_validation(records, warnings)

    assert len(records) == 1
    assert records[0].serial_count == 1
    assert records[0].qty_check == "MISMATCH"
    assert warnings == [
        "mismatch.pdf: 0061705844-03 / SFP 1.25G 850nm 550m: order qty 2, serial count 1"
    ]


def test_same_part_number_in_independent_blocks_validates_separately(line_pages) -> None:
    lines = [
        "PART-A (Quantité 1): MODULE-A",
        "PLS000001",
        "PART-A (Quantité 2): MODULE-A",
        "PLS000002",
        "PLS000003",
    ]
    records = extract_document_records("blocks.pdf", lines, line_pages(lines), set())
    warnings: list[str] = []

    apply_quantity_validation(records, warnings)

    assert [record.serial_count for record in records] == [1, 2, 2]
    assert {record.qty_check for record in records} == {"OK"}
    assert warnings == []


def test_restricted_ocr_page_accepts_explicit_vendor_block_without_marker(line_pages) -> None:
    lines = [
        "TQD013-TUNC-SO85043100 2 PCS",
        "QSFP-DD 400G OpenZR+",
        "VB000001",
        "VB000002",
    ]

    records = extract_document_records(
        "smartoptics-scan.pdf",
        lines,
        line_pages(lines),
        set(),
        restricted_pages={1},
    )

    assert [record.serial_number for record in records] == ["VB000001", "VB000002"]


def test_marker_context_stops_before_packing_list_metadata(line_pages) -> None:
    lines = [
        "ADVA 100G line Card (2 slot TCE) + CFP + SFP optics",
        "ADVA",
        "1063700071-02",
        "2",
        "Serial numbers are: FA72170707254, FA72171000841",
        "Packing List",
        "SP260073",
        "Our Ref",
        "20621",
    ]

    records = extract_document_records("dtc.pdf", lines, line_pages(lines), set())

    assert [record.serial_number for record in records] == [
        "FA72170707254",
        "FA72171000841",
    ]


def test_marker_context_stops_before_payment_metadata(line_pages) -> None:
    lines = [
        "500 1040904057-01",
        "F150/ADV/XG120PRO/PSA/240V",
        "4 4 0 10.00 40.00",
        "S/N:",
        "LBADVAJU254401566",
        "LBADVAJU254401569",
        "BIC / Swift Code: DEUTUS33",
        "Account",
        "200601288N",
    ]

    records = extract_document_records("adtran.pdf", lines, line_pages(lines), set())

    assert [record.serial_number for record in records] == [
        "LBADVAJU254401566",
        "LBADVAJU254401569",
    ]


def test_duplicate_serial_text_is_only_deduplicated_within_same_block(line_pages) -> None:
    lines = [
        "PART-A (Quantité 1): MODULE-A",
        "PLS000001",
        "PLS000001",
        "PART-B (Quantité 1): MODULE-B",
        "PLS000001",
    ]

    records = extract_document_records("blocks.pdf", lines, line_pages(lines), set())

    assert [record.part_number for record in records] == ["PART-A", "PART-B"]
    assert [record.serial_number for record in records] == ["PLS000001", "PLS000001"]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("BC00000647", True),
        ("1042004437-01", True),
        ("010280-A", True),
        ("85043100", True),
        ("PACKING", False),
        ("FA70000000001", False),
    ],
)
def test_part_number_heuristic_characterization(value: str, expected: bool) -> None:
    assert is_part_number_like(value) is expected
