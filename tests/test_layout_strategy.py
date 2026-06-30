from __future__ import annotations

from serial_extractor.layout import extract_layout_groups
from serial_extractor.models import DocumentPage, TextSpan


def span(text: str, page: int, x0: float, top: float, x1: float | None = None) -> TextSpan:
    width = max(20.0, len(text) * 6.0)
    return TextSpan(
        text=text,
        page=page,
        bbox=(x0, top, x1 if x1 is not None else x0 + width, top + 10.0),
        backend="native_layout",
    )


def test_eci_layout_produces_three_verified_blocks() -> None:
    page1_spans = [
        span("CATALOG", 1, 10, 100),
        span("DESCRIPTION", 1, 210, 100),
        span("QTY", 1, 500, 100),
        span("LOT/SERIAL NO.", 1, 620, 100),
        span("ON324921", 1, 10, 130),
        span("ON324921", 1, 105, 130),
        span("OTR100Q28_LR4", 1, 210, 130),
        span("1", 1, 500, 130),
        span("3620012688", 1, 620, 130),
        span("ON324921", 1, 10, 150),
        span("ON324921", 1, 105, 150),
        span("OTR100Q28_LR4", 1, 210, 150),
        span("12", 1, 500, 150),
        span("3620012714", 1, 620, 150),
        *[span(str(3620013200 + index), 1, 620, 170 + index * 12) for index in range(11)],
    ]
    page2_spans = [
        span("CATALOG", 2, 10, 100),
        span("DESCRIPTION", 2, 210, 100),
        span("QTY", 2, 500, 100),
        span("LOT/SERIAL NO.", 2, 620, 100),
        span("X66706", 2, 10, 130),
        span("X66706", 2, 105, 130),
        span("TM400ENB INCLUDING FIPS KIT", 2, 210, 130),
        span("2", 2, 500, 130),
        span("5504279835", 2, 620, 130),
        span("5504279834", 2, 620, 150),
    ]
    pages = [
        DocumentPage(page_number=1, text="", lines=[], spans=page1_spans),
        DocumentPage(page_number=2, text="", lines=[], spans=page2_spans),
    ]

    groups = extract_layout_groups(pages)

    assert [
        (group.part_number, group.part_name, group.order_qty, len(group.serials))
        for group in groups
    ] == [
        ("ON324921", "OTR100Q28_LR4", 1, 1),
        ("ON324921", "OTR100Q28_LR4", 12, 12),
        ("X66706", "TM400ENB INCLUDING FIPS KIT", 2, 2),
    ]


def test_description_tokens_between_description_and_qty_stay_in_description() -> None:
    spans = [
        span("CATALOG", 1, 18, 100),
        span("DESCRIPTION", 1, 212, 100),
        span("QTY", 1, 346, 100),
        span("LOT/SERIAL NO.", 1, 440, 100),
        span("X66706", 1, 18, 130),
        span("X66706", 1, 81, 130),
        span("TM400ENB", 1, 212, 130),
        span("INCLUDING", 1, 256, 130),
        span("FIPS", 1, 302, 130),
        span("KIT", 1, 322, 130),
        span("2", 1, 348, 130),
        span("5504279835", 1, 440, 130),
        span("5504279834", 1, 440, 150),
    ]

    groups = extract_layout_groups(
        [DocumentPage(page_number=1, text="", lines=[], spans=spans)]
    )

    assert [
        (group.part_number, group.part_name, group.order_qty, group.serials)
        for group in groups
    ] == [("X66706", "TM400ENB INCLUDING FIPS KIT", 2, ["5504279835", "5504279834"])]


def test_unknown_vendor_uses_header_synonyms_and_ignores_nonserial_columns() -> None:
    spans = [
        span("Part Number", 1, 10, 100),
        span("Part Name", 1, 180, 100),
        span("Quantity", 1, 470, 100),
        span("S/N", 1, 600, 100),
        span("PN-001", 1, 10, 130),
        span("Generic Optical Module", 1, 180, 130),
        span("2", 1, 470, 130),
        span("FA70000000001", 1, 600, 130),
        span("Commodity Code", 1, 180, 150),
        span("85176200", 1, 300, 150),
        span("FA70000000002", 1, 600, 150),
    ]
    pages = [DocumentPage(page_number=1, text="", lines=[], spans=spans)]

    groups = extract_layout_groups(pages)

    assert len(groups) == 1
    assert groups[0].part_number == "PN-001"
    assert groups[0].part_name == "Generic Optical Module"
    assert groups[0].order_qty == 2
    assert groups[0].serials == ["FA70000000001", "FA70000000002"]


def test_generic_table_rejects_eight_digit_numeric_business_values() -> None:
    spans = [
        span("Part", 1, 10, 100),
        span("Description", 1, 180, 100),
        span("Qty", 1, 470, 100),
        span("Serial", 1, 600, 100),
        span("PN-003", 1, 10, 130),
        span("Generic Module", 1, 180, 130),
        span("1", 1, 470, 130),
        span("85176200", 1, 600, 130),
    ]

    groups = extract_layout_groups(
        [DocumentPage(page_number=1, text="", lines=[], spans=spans)]
    )

    assert groups == []


def test_generic_table_supports_changed_column_order() -> None:
    spans = [
        span("S/N", 1, 10, 100),
        span("Part Number", 1, 180, 100),
        span("Qty", 1, 380, 100),
        span("Description", 1, 470, 100),
        span("ZX9A001", 1, 10, 130),
        span("PN-001", 1, 180, 130),
        span("1", 1, 380, 130),
        span("Generic Module", 1, 470, 130),
    ]

    groups = extract_layout_groups(
        [DocumentPage(page_number=1, text="", lines=[], spans=spans)]
    )

    assert [
        (group.part_number, group.part_name, group.order_qty, group.serials)
        for group in groups
    ] == [("PN-001", "Generic Module", 1, ["ZX9A001"])]


def test_generic_table_continues_serials_on_headerless_next_page() -> None:
    page1 = [
        span("Part", 1, 10, 100),
        span("Description", 1, 180, 100),
        span("Qty", 1, 470, 100),
        span("Serial", 1, 600, 100),
        span("PN-002", 1, 10, 130),
        span("Cross Page Module", 1, 180, 130),
        span("2", 1, 470, 130),
        span("ZX9A001", 1, 600, 130),
    ]
    page2 = [
        span("ZX9A002", 2, 600, 80),
    ]

    groups = extract_layout_groups(
        [
            DocumentPage(page_number=1, text="", lines=[], spans=page1),
            DocumentPage(page_number=2, text="", lines=[], spans=page2),
        ]
    )

    assert len(groups) == 1
    assert groups[0].serials == ["ZX9A001", "ZX9A002"]
