from __future__ import annotations

import re
from dataclasses import dataclass
from statistics import mean

from .models import DocumentPage, LayoutProductGroup, TextSpan


PART_HEADER_RE = re.compile(r"\b(?:PART(?:\s+NUMBER)?|MATERIAL|ITEM(?:\s+CODE)?|CATALOG)\b", re.IGNORECASE)
DESCRIPTION_HEADER_RE = re.compile(r"\b(?:DESCRIPTION|DESC\.?|PART\s+NAME|PRODUCT\s+NAME)\b", re.IGNORECASE)
QTY_HEADER_RE = re.compile(r"\b(?:QTY|QUANTITY|QUANTIT[ÉE])\b", re.IGNORECASE)
SERIAL_HEADER_RE = re.compile(r"(?:S/N|SERIAL|LOT/SERIAL)", re.IGNORECASE)
PART_TOKEN_RE = re.compile(r"^[A-Z0-9][A-Z0-9/#.+_-]{3,41}$", re.IGNORECASE)
SERIAL_TOKEN_RE = re.compile(r"^[A-Z0-9]{5,32}$", re.IGNORECASE)
NUMERIC_SERIAL_RE = re.compile(r"^\d{10,14}$")

EXCLUDED_SERIAL_VALUES = {
    "85043100",
    "85176200",
}


@dataclass(frozen=True)
class HeaderSchema:
    part_x: float
    description_x: float
    qty_x: float
    serial_x: float
    header_bottom: float


def _center_x(span: TextSpan) -> float:
    return (span.bbox[0] + span.bbox[2]) / 2.0


def _top(span: TextSpan) -> float:
    return span.bbox[1]


def _bottom(span: TextSpan) -> float:
    return span.bbox[3]


def group_spans_into_lines(spans: list[TextSpan], tolerance: float = 4.0) -> list[list[TextSpan]]:
    lines: list[list[TextSpan]] = []
    for span in sorted(spans, key=lambda item: (_top(item), item.bbox[0])):
        target: list[TextSpan] | None = None
        for line in reversed(lines):
            if abs(mean(_top(item) for item in line) - _top(span)) <= tolerance:
                target = line
                break
            if _top(span) - mean(_top(item) for item in line) > tolerance:
                break
        if target is None:
            target = []
            lines.append(target)
        target.append(span)
        target.sort(key=lambda item: item.bbox[0])
    return lines


def _header_candidates(spans: list[TextSpan], pattern: re.Pattern[str]) -> list[TextSpan]:
    return [span for span in spans if pattern.search(span.text)]


def find_header_schema(page: DocumentPage) -> HeaderSchema | None:
    spans = page.spans
    part_candidates = _header_candidates(spans, PART_HEADER_RE)
    description_candidates = _header_candidates(spans, DESCRIPTION_HEADER_RE)
    qty_candidates = _header_candidates(spans, QTY_HEADER_RE)
    serial_candidates = _header_candidates(spans, SERIAL_HEADER_RE)

    possible: list[tuple[float, HeaderSchema]] = []
    for part in part_candidates:
        for description in description_candidates:
            for qty in qty_candidates:
                for serial in serial_candidates:
                    tops = [_top(part), _top(description), _top(qty), _top(serial)]
                    if max(tops) - min(tops) > 28:
                        continue
                    xs = [_center_x(part), _center_x(description), _center_x(qty), _center_x(serial)]
                    if len({round(value, 1) for value in xs}) != 4:
                        continue
                    schema = HeaderSchema(
                        part_x=_center_x(part),
                        description_x=_center_x(description),
                        qty_x=_center_x(qty),
                        serial_x=_center_x(serial),
                        header_bottom=max(_bottom(part), _bottom(description), _bottom(qty), _bottom(serial)),
                    )
                    possible.append((max(tops) - min(tops), schema))
    if not possible:
        return None
    return min(possible, key=lambda item: item[0])[1]


def _cell_text(spans: list[TextSpan]) -> str:
    return " ".join(span.text.strip() for span in spans if span.text.strip()).strip()


def _dedupe_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    for token in value.split():
        cleaned = token.strip(" ,:;()[]{}").upper()
        if cleaned and cleaned not in tokens:
            tokens.append(cleaned)
    return tokens


def _part_number(value: str) -> str:
    for token in _dedupe_tokens(value):
        if not PART_TOKEN_RE.fullmatch(token):
            continue
        if token.isdigit() and len(token) < 6:
            continue
        if not any(char.isdigit() for char in token):
            continue
        return token
    return ""


def _quantity(value: str) -> int | None:
    match = re.search(r"\b(\d{1,6})\b", value)
    return int(match.group(1)) if match else None


def _normalize_serial(value: str) -> str:
    value = value.strip().strip("*,:;.()[]{}<>").upper()
    value = re.sub(r"^(?:S/N|SN)\s*:?", "", value)
    value = re.sub(r"^(FA\d{8,})SN$", r"\1", value)
    return value


def _serials(value: str) -> list[str]:
    serials: list[str] = []
    for raw in re.split(r"[\s,;]+", value):
        token = _normalize_serial(raw)
        if not token or token in EXCLUDED_SERIAL_VALUES:
            continue
        if NUMERIC_SERIAL_RE.fullmatch(token):
            serials.append(token)
            continue
        if SERIAL_TOKEN_RE.fullmatch(token) and any(char.isalpha() for char in token) and any(char.isdigit() for char in token):
            serials.append(token)
    return serials


def _column_for_x(schema: HeaderSchema, x: float) -> str:
    columns = sorted(
        (
            (schema.part_x, "part"),
            (schema.description_x, "description"),
            (schema.qty_x, "qty"),
            (schema.serial_x, "serial"),
        )
    )
    boundaries = [(columns[index][0] + columns[index + 1][0]) / 2 for index in range(3)]
    for index, boundary in enumerate(boundaries):
        if x < boundary:
            return columns[index][1]
    return columns[-1][1]


def _column_for_span(schema: HeaderSchema, span: TextSpan) -> str:
    x = _center_x(span)
    column = _column_for_x(schema, x)
    if (
        column == "qty"
        and schema.description_x < x < schema.qty_x
        and re.search(r"[A-Z]", span.text, re.IGNORECASE)
    ):
        return "description"
    return column


def _extract_page_groups(
    page: DocumentPage,
    inherited_schema: HeaderSchema | None = None,
    inherited_current: LayoutProductGroup | None = None,
) -> tuple[list[LayoutProductGroup], LayoutProductGroup | None, HeaderSchema | None]:
    detected_schema = find_header_schema(page)
    schema = detected_schema or inherited_schema
    if schema is None:
        return [], inherited_current, None

    groups: list[LayoutProductGroup] = []
    current = inherited_current
    line_tolerance = 10.0 if page.backend == "paddleocr" else 4.0
    for line in group_spans_into_lines(page.spans, tolerance=line_tolerance):
        if detected_schema is not None and max(_bottom(span) for span in line) <= schema.header_bottom + 1:
            continue
        if (
            PART_HEADER_RE.search(_cell_text(line))
            and QTY_HEADER_RE.search(_cell_text(line))
            and SERIAL_HEADER_RE.search(_cell_text(line))
        ):
            continue

        column_spans: dict[str, list[TextSpan]] = {
            "part": [],
            "description": [],
            "qty": [],
            "serial": [],
        }
        for span in line:
            column_spans[_column_for_span(schema, span)].append(span)

        part_number = _part_number(_cell_text(column_spans["part"]))
        part_name = _cell_text(column_spans["description"])
        order_qty = _quantity(_cell_text(column_spans["qty"]))
        serial_values = _serials(_cell_text(column_spans["serial"]))

        if part_number and part_name and order_qty is not None:
            confidence_values = [span.confidence for span in line]
            current = LayoutProductGroup(
                page=page.page_number,
                part_number=part_number,
                part_name=part_name,
                order_qty=order_qty,
                serials=list(serial_values),
                confidence=min(confidence_values) if confidence_values else 1.0,
                bbox=(
                    min(span.bbox[0] for span in line),
                    min(span.bbox[1] for span in line),
                    max(span.bbox[2] for span in line),
                    max(span.bbox[3] for span in line),
                ),
            )
            groups.append(current)
            continue

        if current is not None and serial_values:
            current.serials.extend(serial_values)

    return groups, current, schema


def extract_layout_groups(pages: list[DocumentPage]) -> list[LayoutProductGroup]:
    groups: list[LayoutProductGroup] = []
    schema: HeaderSchema | None = None
    current: LayoutProductGroup | None = None
    for page in pages:
        page_groups, current, schema = _extract_page_groups(
            page,
            inherited_schema=schema,
            inherited_current=current,
        )
        groups.extend(page_groups)
    return [group for group in groups if group.serials]
