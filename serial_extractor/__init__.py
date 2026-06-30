"""Core package for Serial Number Extractor 2.x."""

__version__ = "2.0.1"

from .models import (
    DocumentPage,
    ExtractResult,
    ExtractionOptions,
    LayoutProductGroup,
    ProductBlock,
    ReviewCandidate,
    SerialCandidate,
    SerialRecord,
    TextSpan,
)

__all__ = [
    "DocumentPage",
    "ExtractResult",
    "ExtractionOptions",
    "LayoutProductGroup",
    "ProductBlock",
    "ReviewCandidate",
    "SerialCandidate",
    "SerialRecord",
    "TextSpan",
    "__version__",
]
