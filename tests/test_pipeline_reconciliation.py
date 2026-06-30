from __future__ import annotations

from serial_extractor.app import _merge_layout_records
from serial_extractor.models import SerialRecord


def record(serial: str, part: str, strategy: str) -> SerialRecord:
    return SerialRecord(
        source_file="sample.pdf",
        page=1,
        part_number=part,
        part_name=part,
        order_qty=1 if part else None,
        serial_number=serial,
        serial_count=None,
        qty_check="UNVERIFIED",
        item_hint="",
        method=strategy,
        confidence="high",
        block_key=part,
        block_source=strategy,
        strategy=strategy,
    )


def test_layout_reconciliation_upgrades_matches_and_preserves_other_records() -> None:
    legacy = [
        record("SN-A", "", "legacy"),
        record("SN-B", "NATIVE-PART", "adtran"),
    ]
    layout = [
        record("SN-A", "LAYOUT-PART", "generic_layout"),
    ]

    merged = _merge_layout_records(legacy, layout)

    assert [(item.serial_number, item.part_number, item.strategy) for item in merged] == [
        ("SN-A", "LAYOUT-PART", "generic_layout"),
        ("SN-B", "NATIVE-PART", "adtran"),
    ]


def test_layout_reconciliation_preserves_duplicate_multiplicity() -> None:
    legacy = [
        record("SN-A", "BLOCK-1", "legacy"),
        record("SN-A", "BLOCK-2", "legacy"),
    ]
    layout = [
        record("SN-A", "BLOCK-1-LAYOUT", "generic_layout"),
    ]

    merged = _merge_layout_records(legacy, layout)

    assert [item.part_number for item in merged] == ["BLOCK-1-LAYOUT", "BLOCK-2"]


def test_layout_reconciliation_drops_eci_best_effort_on_layout_pages() -> None:
    legacy = [
        record("SP260069", "LEGACY-ECI", "eci_best_effort"),
        record("3620012688", "LEGACY-ECI", "eci_best_effort"),
    ]
    layout = [
        record("3620012688", "ON324921", "generic_layout"),
    ]

    merged = _merge_layout_records(legacy, layout)

    assert [(item.serial_number, item.part_number, item.strategy) for item in merged] == [
        ("3620012688", "ON324921", "generic_layout"),
    ]
