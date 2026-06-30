from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol
from urllib.parse import urlparse

from .models import ReviewCandidate, SerialCandidate, TextSpan


OCR_SUPPORT_MANIFEST = "ocr_support.json"
DEFAULT_OCR_MANIFEST_URL = (
    "https://github.com/Shi0v0Jasmine/Serial_Number_Extractor_Esther/"
    "releases/latest/download/ocr_support_manifest.json"
)


class OcrInstallError(RuntimeError):
    pass


class OcrSupportRequired(RuntimeError):
    pass


class OcrEngine(Protocol):
    def recognize_pdf(self, pdf_path: Path, page_numbers: list[int]) -> list[TextSpan]:
        ...


@dataclass(frozen=True)
class OcrSupportStatus:
    installed: bool
    version: str = ""
    worker_path: Path | None = None
    models: tuple[str, ...] = ()


@dataclass(frozen=True)
class InstalledOcrSupport:
    version: str
    worker_path: Path
    models: tuple[str, ...]


def default_ocr_home() -> Path:
    local_app_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
    return root / "Apeiro" / "SerialNumberExtractor" / "ocr"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_member(name: str) -> bool:
    member = PurePosixPath(name.replace("\\", "/"))
    return not member.is_absolute() and ".." not in member.parts


def _normalize_candidate(value: str) -> str:
    return value.strip().strip("*,:;.()[]{}<>").upper()


def _looks_like_review_candidate(value: str) -> bool:
    normalized = _normalize_candidate(value)
    if len(normalized) < 5 or len(normalized) > 32:
        return False
    return any(char.isalpha() for char in normalized) and any(char.isdigit() for char in normalized)


def _load_worker_payload(stdout: str) -> dict[str, object]:
    decoder = json.JSONDecoder()
    for index, character in enumerate(stdout):
        if character != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(stdout[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload
    raise json.JSONDecodeError("No JSON object found in OCR worker stdout", stdout, 0)


def _is_near_serial_anchor(span: TextSpan, spans: list[TextSpan]) -> bool:
    for anchor in spans:
        if anchor.page != span.page:
            continue
        anchor_text = anchor.text.upper().replace(" ", "")
        if not (
            "S/N" in anchor_text
            or "SERIAL" in anchor_text
            or "LOT/SERIAL" in anchor_text
        ):
            continue
        same_row = abs(span.bbox[1] - anchor.bbox[1]) <= 24 and span.bbox[0] >= anchor.bbox[0] - 12
        below_column = (
            0 <= span.bbox[1] - anchor.bbox[3] <= 360
            and span.bbox[0] >= anchor.bbox[0] - 40
        )
        if same_row or below_column:
            return True
    return False


def partition_ocr_spans(
    source_file: str,
    spans: list[TextSpan],
    min_confidence: float,
) -> tuple[list[TextSpan], list[ReviewCandidate]]:
    accepted: list[TextSpan] = []
    reviews: list[ReviewCandidate] = []
    for span in spans:
        anchored = _is_near_serial_anchor(span, spans)
        format_valid = _looks_like_review_candidate(span.text)
        candidate = SerialCandidate(
            raw_text=span.text,
            normalized_value=_normalize_candidate(span.text),
            page=span.page,
            bbox=span.bbox,
            confidence=span.confidence,
            backend="paddleocr",
            strategy="ocr_candidate_filter",
            anchored=anchored,
            format_valid=format_valid,
            score=span.confidence * (1.0 if anchored else 0.5),
        )
        if span.confidence >= min_confidence:
            accepted.append(span)
            continue
        if candidate.format_valid and candidate.anchored:
            reviews.append(
                ReviewCandidate(
                    source_file=source_file,
                    page=span.page,
                    candidate_type="serial",
                    raw_text=span.text,
                    normalized_value=candidate.normalized_value,
                    confidence=candidate.confidence,
                    reason="ocr_confidence_below_threshold",
                    bbox=span.bbox,
                    backend="paddleocr",
                    strategy="ocr_candidate_filter",
                )
            )
    return accepted, reviews


class OcrSupportManager:
    def __init__(self, install_dir: Path | None = None) -> None:
        self.install_dir = install_dir or default_ocr_home()

    @property
    def manifest_path(self) -> Path:
        return self.install_dir / OCR_SUPPORT_MANIFEST

    def _read_manifest(self, directory: Path) -> dict[str, object]:
        path = directory / OCR_SUPPORT_MANIFEST
        if not path.exists():
            raise OcrInstallError(f"OCR package is missing {OCR_SUPPORT_MANIFEST}.")
        try:
            data = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError) as exc:
            raise OcrInstallError(f"Invalid OCR support manifest: {exc}") from exc
        if not isinstance(data, dict) or not data.get("version") or not data.get("worker"):
            raise OcrInstallError("OCR support manifest must define version and worker.")
        worker = Path(str(data["worker"]))
        if worker.is_absolute() or ".." in worker.parts:
            raise OcrInstallError("OCR support manifest contains an unsafe worker path.")
        return data

    def status(self) -> OcrSupportStatus:
        if not self.manifest_path.exists():
            return OcrSupportStatus(installed=False)
        try:
            data = self._read_manifest(self.install_dir)
            worker = self.install_dir / str(data["worker"])
            if not worker.is_file():
                return OcrSupportStatus(installed=False)
            models = tuple(str(value) for value in data.get("models", []))
            if data.get("require_model_dirs") and any(
                not (self.install_dir / "models" / model).is_dir()
                for model in models
            ):
                return OcrSupportStatus(installed=False)
            return OcrSupportStatus(
                installed=True,
                version=str(data["version"]),
                worker_path=worker,
                models=models,
            )
        except OcrInstallError:
            return OcrSupportStatus(installed=False)

    def install_from_package(
        self,
        package_path: Path,
        expected_sha256: str | None = None,
    ) -> InstalledOcrSupport:
        package_path = package_path.resolve()
        if not package_path.is_file():
            raise OcrInstallError(f"OCR support package not found: {package_path}")
        if expected_sha256:
            actual = sha256_file(package_path)
            if actual.lower() != expected_sha256.lower():
                raise OcrInstallError(
                    f"OCR support package SHA256 mismatch: expected {expected_sha256}, got {actual}."
                )

        existing = self.status()
        parent = self.install_dir.parent
        parent.mkdir(parents=True, exist_ok=True)
        temp_dir = Path(tempfile.mkdtemp(prefix=".ocr-install-", dir=parent))
        backup_dir: Path | None = None
        try:
            with zipfile.ZipFile(package_path) as archive:
                unsafe = [info.filename for info in archive.infolist() if not _safe_member(info.filename)]
                if unsafe:
                    raise OcrInstallError(f"OCR package contains unsafe path: {unsafe[0]}")
                archive.extractall(temp_dir)

            data = self._read_manifest(temp_dir)
            worker = temp_dir / str(data["worker"])
            if not worker.is_file():
                raise OcrInstallError(f"OCR worker not found: {data['worker']}")
            models = tuple(str(value) for value in data.get("models", []))
            if data.get("require_model_dirs"):
                missing_models = [
                    model
                    for model in models
                    if not (temp_dir / "models" / model).is_dir()
                ]
                if missing_models:
                    raise OcrInstallError(
                        f"OCR package is missing model directory: {missing_models[0]}"
                    )

            if existing.installed and existing.version == str(data["version"]):
                shutil.rmtree(temp_dir, ignore_errors=True)
                assert existing.worker_path is not None
                return InstalledOcrSupport(existing.version, existing.worker_path, existing.models)

            if self.install_dir.exists():
                backup_dir = parent / f".ocr-backup-{uuid.uuid4().hex}"
                os.replace(self.install_dir, backup_dir)
            os.replace(temp_dir, self.install_dir)
            if backup_dir is not None:
                shutil.rmtree(backup_dir, ignore_errors=True)

            installed = self.status()
            if not installed.installed or installed.worker_path is None:
                raise OcrInstallError("OCR support installation did not produce a valid worker.")
            return InstalledOcrSupport(installed.version, installed.worker_path, installed.models)
        except Exception as exc:
            if backup_dir is not None and backup_dir.exists():
                if self.install_dir.exists():
                    shutil.rmtree(self.install_dir, ignore_errors=True)
                os.replace(backup_dir, self.install_dir)
            if isinstance(exc, OcrInstallError):
                raise
            raise OcrInstallError(f"Failed to install OCR support: {exc}") from exc
        finally:
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def install_from_manifest_url(self, manifest_url: str = DEFAULT_OCR_MANIFEST_URL) -> InstalledOcrSupport:
        parent = self.install_dir.parent
        parent.mkdir(parents=True, exist_ok=True)
        download_dir = Path(tempfile.mkdtemp(prefix=".ocr-download-", dir=parent))
        try:
            manifest_path = download_dir / "download_manifest.json"
            urllib.request.urlretrieve(manifest_url, manifest_path)
            data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            package_url = str(data.get("package_url", ""))
            checksum = str(data.get("sha256", ""))
            if not package_url or not checksum:
                raise OcrInstallError("OCR download manifest must define package_url and sha256.")
            if urlparse(package_url).scheme.lower() != "https":
                raise OcrInstallError("OCR package URL must use HTTPS.")
            if len(checksum) != 64 or any(character not in "0123456789abcdefABCDEF" for character in checksum):
                raise OcrInstallError("OCR download manifest contains an invalid SHA256.")
            package_path = download_dir / "ocr-support.zip"
            urllib.request.urlretrieve(package_url, package_path)
            return self.install_from_package(package_path, expected_sha256=checksum)
        except OcrInstallError:
            raise
        except Exception as exc:
            raise OcrInstallError(f"Failed to download OCR support: {exc}") from exc
        finally:
            shutil.rmtree(download_dir, ignore_errors=True)


class SidecarOcrEngine:
    def __init__(self, worker_path: Path) -> None:
        self.worker_path = worker_path

    def recognize_pdf(self, pdf_path: Path, page_numbers: list[int]) -> list[TextSpan]:
        launcher = [str(self.worker_path)]
        if self.worker_path.suffix.lower() == ".py":
            launcher = [sys.executable, str(self.worker_path)]
        command = launcher + [
            "--input",
            str(pdf_path),
            "--pages",
            ",".join(str(page) for page in page_numbers),
        ]
        environment = os.environ.copy()
        models_dir = self.worker_path.parent / "models"
        if models_dir.is_dir():
            environment["SERIAL_EXTRACTOR_OCR_MODEL_HOME"] = str(models_dir)
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=environment,
                timeout=1800,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("OCR worker timed out after 30 minutes.") from exc
        if completed.returncode != 0:
            stderr = completed.stderr or ""
            stdout = completed.stdout or ""
            message = stderr.strip() or stdout.strip() or "unknown OCR worker error"
            raise RuntimeError(f"OCR worker failed: {message}")
        try:
            payload = _load_worker_payload(completed.stdout or "")
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"OCR worker returned invalid JSON: {exc}") from exc
        spans: list[TextSpan] = []
        for item in payload.get("spans", []):
            bbox = item.get("bbox", [0, 0, 0, 0])
            spans.append(
                TextSpan(
                    text=str(item.get("text", "")),
                    page=int(item.get("page", 1)),
                    bbox=tuple(float(value) for value in bbox[:4]),  # type: ignore[arg-type]
                    confidence=float(item.get("confidence", 0.0)),
                    backend="paddleocr",
                )
            )
        return spans


def discover_ocr_engine(manager: OcrSupportManager | None = None) -> SidecarOcrEngine:
    manager = manager or OcrSupportManager()
    status = manager.status()
    if not status.installed or status.worker_path is None:
        raise OcrSupportRequired(
            "PaddleOCR support is required. Install it from the GUI or run with --install-ocr."
        )
    return SidecarOcrEngine(status.worker_path)
