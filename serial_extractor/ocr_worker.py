from __future__ import annotations

import argparse
import json
import os
import tempfile
import traceback
from collections.abc import Iterable, Mapping
from numbers import Real
from pathlib import Path
from typing import Any


DETECTION_MODEL = "PP-OCRv6_small_det"
RECOGNITION_MODEL = "PP-OCRv6_small_rec"


def _as_payload(result: object) -> Mapping[str, Any]:
    if isinstance(result, Mapping):
        payload: object = result
    else:
        payload = getattr(result, "json", None)
        if callable(payload):
            payload = payload()
        if payload is None:
            to_json = getattr(result, "to_json", None)
            payload = to_json() if callable(to_json) else {}
    if isinstance(payload, str):
        payload = json.loads(payload)
    if not isinstance(payload, Mapping):
        return {}
    nested = payload.get("res")
    return nested if isinstance(nested, Mapping) else payload


def _bbox_from_value(value: object) -> tuple[float, float, float, float] | None:
    tolist = getattr(value, "tolist", None)
    if callable(tolist):
        value = tolist()
    if not isinstance(value, (list, tuple)):
        return None
    if len(value) >= 4 and all(isinstance(item, Real) for item in value[:4]):
        x0, y0, x1, y1 = (float(item) for item in value[:4])
        return x0, y0, x1, y1
    points = []
    for raw_point in value:
        point_tolist = getattr(raw_point, "tolist", None)
        point = point_tolist() if callable(point_tolist) else raw_point
        if (
            isinstance(point, (list, tuple))
            and len(point) >= 2
            and isinstance(point[0], Real)
            and isinstance(point[1], Real)
        ):
            points.append(point)
    if not points:
        return None
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def parse_paddle_result(result: object, page_number: int) -> list[dict[str, object]]:
    payload = _as_payload(result)
    def as_list(value: object) -> list[object]:
        tolist = getattr(value, "tolist", None)
        if callable(tolist):
            value = tolist()
        return list(value) if isinstance(value, (list, tuple)) else []

    texts = as_list(payload.get("rec_texts", []))
    scores = as_list(payload.get("rec_scores", []))
    boxes = as_list(payload.get("rec_boxes", []))
    polygons = as_list(payload.get("rec_polys", payload.get("dt_polys", [])))
    if not isinstance(texts, (list, tuple)):
        return []

    spans: list[dict[str, object]] = []
    for index, raw_text in enumerate(texts):
        text = str(raw_text).strip()
        if not text:
            continue
        score = float(scores[index]) if index < len(scores) else 0.0
        raw_bbox: object = None
        if index < len(boxes):
            raw_bbox = boxes[index]
        if raw_bbox is None and index < len(polygons):
            raw_bbox = polygons[index]
        bbox = _bbox_from_value(raw_bbox) or (0.0, 0.0, 0.0, 0.0)
        spans.append(
            {
                "text": text,
                "page": page_number,
                "bbox": list(bbox),
                "confidence": score,
            }
        )
    return spans


def _parse_pages(raw: str, page_count: int) -> list[int]:
    requested: list[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        page = int(item)
        if page < 1 or page > page_count:
            raise ValueError(f"Page {page} is outside 1..{page_count}.")
        if page not in requested:
            requested.append(page)
    return requested


def _build_engine():
    from paddleocr import PaddleOCR  # type: ignore

    kwargs: dict[str, object] = {
        "text_detection_model_name": DETECTION_MODEL,
        "text_recognition_model_name": RECOGNITION_MODEL,
        "use_doc_orientation_classify": False,
        "use_doc_unwarping": False,
        "use_textline_orientation": False,
    }
    model_home = os.environ.get("SERIAL_EXTRACTOR_OCR_MODEL_HOME")
    if model_home:
        root = Path(model_home)
        detection_dir = root / DETECTION_MODEL
        recognition_dir = root / RECOGNITION_MODEL
        if detection_dir.is_dir():
            kwargs["text_detection_model_dir"] = str(detection_dir)
        if recognition_dir.is_dir():
            kwargs["text_recognition_model_dir"] = str(recognition_dir)
    return PaddleOCR(**kwargs)


def recognize_pdf(pdf_path: Path, page_numbers: list[int]) -> list[dict[str, object]]:
    from pypdf import PdfReader, PdfWriter  # type: ignore

    reader = PdfReader(str(pdf_path))
    engine = _build_engine()
    spans: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="serial-ocr-") as temp_dir:
        for page_number in page_numbers:
            page_pdf = Path(temp_dir) / f"page-{page_number}.pdf"
            writer = PdfWriter()
            writer.add_page(reader.pages[page_number - 1])
            with page_pdf.open("wb") as handle:
                writer.write(handle)
            results: Iterable[object] = engine.predict(input=str(page_pdf))
            for result in results:
                spans.extend(parse_paddle_result(result, page_number))
    return spans


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Local PaddleOCR worker for Serial Number Extractor.")
    parser.add_argument("--input", required=True, help="Input PDF.")
    parser.add_argument("--pages", required=True, help="Comma-separated 1-based page numbers.")
    args = parser.parse_args(argv)

    try:
        from pypdf import PdfReader  # type: ignore

        pdf_path = Path(args.input)
        page_count = len(PdfReader(str(pdf_path)).pages)
        pages = _parse_pages(args.pages, page_count)
        spans = recognize_pdf(pdf_path, pages)
        print(json.dumps({"spans": spans}, ensure_ascii=True))
        return 0
    except Exception as exc:
        traceback.print_exception(type(exc), exc, exc.__traceback__, file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
