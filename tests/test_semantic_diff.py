from __future__ import annotations

import csv

from scripts.compare_semantic_csv import SEMANTIC_COLUMNS, compare_csv


def write_rows(path, rows) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(SEMANTIC_COLUMNS)
        writer.writerows(rows)


def test_semantic_diff_ignores_row_order_and_reports_real_changes(tmp_path) -> None:
    row_a = ("PN-1", "Part A", "SN001", "1", "1", "OK")
    row_b = ("PN-2", "Part B", "SN002", "", "1", "UNVERIFIED")
    row_b_fixed = ("PN-2", "Part B", "SN002", "1", "1", "OK")
    before = tmp_path / "before.csv"
    reordered = tmp_path / "reordered.csv"
    changed = tmp_path / "changed.csv"
    write_rows(before, [row_a, row_b])
    write_rows(reordered, [row_b, row_a])
    write_rows(changed, [row_a, row_b_fixed])

    assert compare_csv(before, reordered)["added_count"] == 0
    result = compare_csv(before, changed)
    assert result["removed"] == [row_b]
    assert result["added"] == [row_b_fixed]
