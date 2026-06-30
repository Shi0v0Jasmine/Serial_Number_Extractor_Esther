from __future__ import annotations

import re
from pathlib import Path

from .models import DocumentPage, TextSpan


def clean_lines(text: str) -> list[str]:
    return [re.sub(r"\s+", " ", line).strip() for line in text.splitlines() if line.strip()]


def extract_layout_pages(pdf_path: Path) -> list[DocumentPage]:
    try:
        import pdfplumber  # type: ignore
    except ImportError:
        return []

    pages: list[DocumentPage] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(layout=True) or ""
            words = page.extract_words(
                x_tolerance=2,
                y_tolerance=3,
                keep_blank_chars=False,
                use_text_flow=False,
            )
            spans = [
                TextSpan(
                    text=str(word.get("text", "")).strip(),
                    page=page_number,
                    bbox=(
                        float(word.get("x0", 0.0)),
                        float(word.get("top", 0.0)),
                        float(word.get("x1", 0.0)),
                        float(word.get("bottom", 0.0)),
                    ),
                    confidence=1.0,
                    backend="native_layout",
                )
                for word in words
                if str(word.get("text", "")).strip()
            ]
            pages.append(
                DocumentPage(
                    page_number=page_number,
                    text=text,
                    lines=clean_lines(text),
                    spans=spans,
                    backend="native_layout",
                    scanned=not bool(text.strip()),
                )
            )
    return pages
