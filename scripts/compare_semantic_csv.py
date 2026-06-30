from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


SEMANTIC_COLUMNS = (
    "Part Number",
    "Part Name",
    "Serial Number",
    "Order Qty",
    "Serial Count",
    "Qty Check",
)


def semantic_rows(path: Path) -> Counter[tuple[str, ...]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in SEMANTIC_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(missing)}")
        return Counter(
            tuple((row.get(column) or "").strip() for column in SEMANTIC_COLUMNS)
            for row in reader
        )


def compare_csv(before: Path, after: Path) -> dict[str, object]:
    before_rows = semantic_rows(before)
    after_rows = semantic_rows(after)
    removed = list((before_rows - after_rows).elements())
    added = list((after_rows - before_rows).elements())
    return {
        "before_count": sum(before_rows.values()),
        "after_count": sum(after_rows.values()),
        "removed_count": len(removed),
        "added_count": len(added),
        "removed": removed,
        "added": added,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare two extractor CSV files semantically.")
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    args = parser.parse_args(argv)
    result = compare_csv(args.before, args.after)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 1 if result["removed_count"] or result["added_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
