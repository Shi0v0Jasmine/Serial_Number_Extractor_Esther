from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

import pytest

from serial_extractor.models import TextSpan
from serial_extractor.ocr import (
    OcrInstallError,
    OcrSupportManager,
    SidecarOcrEngine,
    partition_ocr_spans,
)


def test_low_confidence_serial_goes_to_review_without_autocorrection() -> None:
    spans = [
        TextSpan("S/N:", 1, (10, 10, 40, 20), 0.99, "paddleocr"),
        TextSpan("FA7O2612O1473", 1, (50, 10, 150, 20), 0.72, "paddleocr"),
        TextSpan("FA70261201481", 1, (50, 30, 150, 40), 0.98, "paddleocr"),
    ]

    accepted, reviews = partition_ocr_spans(
        source_file="scan.pdf",
        spans=spans,
        min_confidence=0.90,
    )

    assert [span.text for span in accepted] == ["S/N:", "FA70261201481"]
    assert len(reviews) == 1
    assert reviews[0].raw_text == "FA7O2612O1473"
    assert reviews[0].normalized_value == "FA7O2612O1473"
    assert reviews[0].reason == "ocr_confidence_below_threshold"


def test_unanchored_low_confidence_text_does_not_enter_review() -> None:
    spans = [
        TextSpan("Invoice", 1, (10, 10, 60, 20), 0.99, "paddleocr"),
        TextSpan("FA7O2612O1473", 1, (50, 80, 150, 90), 0.72, "paddleocr"),
    ]

    accepted, reviews = partition_ocr_spans("scan.pdf", spans, min_confidence=0.90)

    assert [span.text for span in accepted] == ["Invoice"]
    assert reviews == []


def create_support_package(
    path,
    *,
    worker_name: str = "ocr_worker.exe",
    version: str = "2.0.0",
    worker_bytes: bytes = b"fake worker",
) -> str:
    manifest = {
        "version": version,
        "worker": worker_name,
        "paddlepaddle": "3.2.2",
        "paddleocr": "3.7.0",
        "models": ["PP-OCRv6_small_det", "PP-OCRv6_small_rec"],
    }
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("ocr_support.json", json.dumps(manifest))
        archive.writestr(worker_name, worker_bytes)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_offline_sidecar_install_is_atomic_and_idempotent(tmp_path) -> None:
    package = tmp_path / "ocr-support.zip"
    checksum = create_support_package(package)
    manager = OcrSupportManager(tmp_path / "installed")

    installed = manager.install_from_package(package, expected_sha256=checksum)

    assert installed.version == "2.0.0"
    assert installed.worker_path.read_bytes() == b"fake worker"
    assert manager.status().installed is True
    second = manager.install_from_package(package, expected_sha256=checksum)
    assert second.worker_path == installed.worker_path
    assert not list(tmp_path.glob(".ocr-install-*"))


def test_sidecar_install_rejects_checksum_mismatch(tmp_path) -> None:
    package = tmp_path / "ocr-support.zip"
    create_support_package(package)
    manager = OcrSupportManager(tmp_path / "installed")

    with pytest.raises(OcrInstallError, match="SHA256"):
        manager.install_from_package(package, expected_sha256="0" * 64)

    assert manager.status().installed is False


def test_sidecar_install_rejects_zip_path_traversal(tmp_path) -> None:
    package = tmp_path / "ocr-support.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("ocr_support.json", json.dumps({"version": "2.0.0", "worker": "ocr_worker.exe"}))
        archive.writestr("../escape.txt", "no")
        archive.writestr("ocr_worker.exe", "worker")
    manager = OcrSupportManager(tmp_path / "installed")

    with pytest.raises(OcrInstallError, match="unsafe"):
        manager.install_from_package(package)

    assert not (tmp_path / "escape.txt").exists()


def test_sidecar_install_rejects_unsafe_manifest_worker_path(tmp_path) -> None:
    package = tmp_path / "ocr-support.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr(
            "ocr_support.json",
            json.dumps({"version": "2.0.0", "worker": "../ocr_worker.exe"}),
        )
        archive.writestr("ocr_worker.exe", "worker")
    manager = OcrSupportManager(tmp_path / "installed")

    with pytest.raises(OcrInstallError, match="unsafe worker"):
        manager.install_from_package(package)


def test_sidecar_install_rejects_missing_required_models(tmp_path) -> None:
    package = tmp_path / "ocr-support.zip"
    manifest = {
        "version": "2.0.0",
        "worker": "ocr_worker.exe",
        "models": ["PP-OCRv6_small_det"],
        "require_model_dirs": True,
    }
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("ocr_support.json", json.dumps(manifest))
        archive.writestr("ocr_worker.exe", "worker")
    manager = OcrSupportManager(tmp_path / "installed")

    with pytest.raises(OcrInstallError, match="missing model directory"):
        manager.install_from_package(package)


def test_sidecar_upgrade_replaces_previous_version(tmp_path) -> None:
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    create_support_package(first, version="1.0.0", worker_bytes=b"old")
    create_support_package(second, version="2.0.0", worker_bytes=b"new")
    manager = OcrSupportManager(tmp_path / "installed")

    manager.install_from_package(first)
    installed = manager.install_from_package(second)

    assert installed.version == "2.0.0"
    assert installed.worker_path.read_bytes() == b"new"
    assert not list(tmp_path.glob(".ocr-backup-*"))


def test_invalid_upgrade_keeps_previous_install(tmp_path) -> None:
    first = tmp_path / "first.zip"
    invalid = tmp_path / "invalid.zip"
    create_support_package(first, version="1.0.0", worker_bytes=b"old")
    with zipfile.ZipFile(invalid, "w") as archive:
        archive.writestr(
            "ocr_support.json",
            json.dumps({"version": "2.0.0", "worker": "missing.exe"}),
        )
    manager = OcrSupportManager(tmp_path / "installed")
    manager.install_from_package(first)

    with pytest.raises(OcrInstallError, match="worker not found"):
        manager.install_from_package(invalid)

    status = manager.status()
    assert status.installed is True
    assert status.version == "1.0.0"
    assert status.worker_path is not None
    assert status.worker_path.read_bytes() == b"old"


def test_interrupted_manifest_download_leaves_install_untouched(tmp_path, monkeypatch) -> None:
    manager = OcrSupportManager(tmp_path / "installed")

    def fail_download(*args, **kwargs):
        raise OSError("network interrupted")

    monkeypatch.setattr("serial_extractor.ocr.urllib.request.urlretrieve", fail_download)

    with pytest.raises(OcrInstallError, match="network interrupted"):
        manager.install_from_manifest_url("https://example.invalid/manifest.json")

    assert manager.status().installed is False
    assert not list(tmp_path.glob(".ocr-download-*"))


def test_invalid_zip_is_reported_as_install_error(tmp_path) -> None:
    package = tmp_path / "invalid.zip"
    package.write_bytes(b"not a zip")
    manager = OcrSupportManager(tmp_path / "installed")

    with pytest.raises(OcrInstallError, match="Failed to install"):
        manager.install_from_package(package)


def test_download_manifest_rejects_non_https_package_url(tmp_path, monkeypatch) -> None:
    manager = OcrSupportManager(tmp_path / "installed")

    def fake_download(url, target):
        target.write_text(
            json.dumps(
                {
                    "package_url": "http://example.test/ocr.zip",
                    "sha256": "0" * 64,
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr("serial_extractor.ocr.urllib.request.urlretrieve", fake_download)

    with pytest.raises(OcrInstallError, match="HTTPS"):
        manager.install_from_manifest_url("https://example.test/manifest.json")


def test_sidecar_engine_passes_model_home_and_parses_json(tmp_path, monkeypatch) -> None:
    worker = tmp_path / "ocr_worker.exe"
    worker.write_bytes(b"worker")
    (tmp_path / "models").mkdir()
    captured: dict[str, object] = {}

    def fake_run(command, **kwargs):
        captured["command"] = command
        captured["env"] = kwargs["env"]
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(
                {
                    "spans": [
                        {
                            "text": "FA70000000001",
                            "page": 2,
                            "bbox": [1, 2, 3, 4],
                            "confidence": 0.98,
                        }
                    ]
                }
            ),
            stderr="",
        )

    monkeypatch.setattr("serial_extractor.ocr.subprocess.run", fake_run)

    spans = SidecarOcrEngine(worker).recognize_pdf(Path("input.pdf"), [2])

    assert captured["command"][-4:] == ["--input", "input.pdf", "--pages", "2"]
    assert captured["env"]["SERIAL_EXTRACTOR_OCR_MODEL_HOME"] == str(tmp_path / "models")
    assert spans == [
        TextSpan("FA70000000001", 2, (1.0, 2.0, 3.0, 4.0), 0.98, "paddleocr")
    ]


def test_sidecar_engine_ignores_stdout_noise_before_json(tmp_path, monkeypatch) -> None:
    worker = tmp_path / "ocr_worker.exe"
    worker.write_bytes(b"worker")

    def fake_run(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=(
                "ReduceMeanCheckIfOneDNNSupport\n"
                '{"spans": [{"text": "FA70000000001", "page": 1, '
                '"bbox": [1, 2, 3, 4], "confidence": 0.98}]}'
            ),
            stderr="Creating model: ('PP-OCRv6_small_det', None, None)\n",
        )

    monkeypatch.setattr("serial_extractor.ocr.subprocess.run", fake_run)

    spans = SidecarOcrEngine(worker).recognize_pdf(Path("input.pdf"), [1])

    assert spans == [
        TextSpan("FA70000000001", 1, (1.0, 2.0, 3.0, 4.0), 0.98, "paddleocr")
    ]
