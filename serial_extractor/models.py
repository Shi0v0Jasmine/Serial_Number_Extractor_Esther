from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal


BBox = tuple[float, float, float, float]
OcrMode = Literal["auto", "off", "force"]


@dataclass(frozen=True)
class TextSpan:
    text: str
    page: int
    bbox: BBox
    confidence: float = 1.0
    backend: str = "native_layout"


@dataclass
class DocumentPage:
    page_number: int
    text: str
    lines: list[str]
    spans: list[TextSpan] = field(default_factory=list)
    backend: str = "native"
    scanned: bool = False


@dataclass(frozen=True)
class ExtractionOptions:
    ocr_mode: OcrMode = "auto"
    ocr_min_confidence: float = 0.90

    def __post_init__(self) -> None:
        if self.ocr_mode not in {"auto", "off", "force"}:
            raise ValueError(f"Unsupported OCR mode: {self.ocr_mode}")
        if not 0.0 <= self.ocr_min_confidence <= 1.0:
            raise ValueError("OCR minimum confidence must be between 0 and 1.")


@dataclass
class LayoutProductGroup:
    page: int
    part_number: str
    part_name: str
    order_qty: int
    serials: list[str]
    strategy: str = "generic_layout"
    confidence: float = 0.95
    bbox: BBox | None = None


@dataclass(frozen=True)
class SerialCandidate:
    raw_text: str
    normalized_value: str
    page: int
    bbox: BBox | None
    confidence: float
    backend: str
    strategy: str
    anchored: bool
    format_valid: bool
    score: float


@dataclass
class ReviewCandidate:
    source_file: str
    page: int
    candidate_type: str
    raw_text: str
    normalized_value: str
    confidence: float
    reason: str
    part_number: str = ""
    part_name: str = ""
    order_qty: int | None = None
    bbox: BBox | None = None
    backend: str = ""
    strategy: str = ""


@dataclass
class ProductBlock:
    part_number: str
    part_name: str
    order_qty: int | None
    start_line: int
    end_line: int
    block_key: str
    source: str
    page: int | None = None
    bbox: BBox | None = None
    confidence: float = 1.0


@dataclass
class SerialRecord:
    source_file: str
    page: int
    part_number: str
    part_name: str
    order_qty: int | None
    serial_number: str
    serial_count: int | None
    qty_check: str
    item_hint: str
    method: str
    confidence: str
    block_key: str
    block_source: str
    backend: str = "native"
    strategy: str = "legacy"
    candidate_score: float = 1.0
    ocr_confidence: float | None = None
    bbox: BBox | None = None


@dataclass
class ExtractResult:
    records: list[SerialRecord]
    warnings: list[str]
    review_candidates: list[ReviewCandidate] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
