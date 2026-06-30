from __future__ import annotations

from pathlib import Path

import serial_extractor.app as app
from serial_extractor.models import ExtractionOptions
from serial_extractor.ocr import InstalledOcrSupport, OcrInstallError, OcrSupportRequired


def test_cli_passes_ocr_options_to_pipeline(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(input_paths, output_xlsx, log, options):
        captured["inputs"] = input_paths
        captured["output"] = output_xlsx
        captured["options"] = options
        return output_xlsx, output_xlsx.with_suffix(".csv"), 0, []

    monkeypatch.setattr(app, "run_extraction", fake_run)
    output = tmp_path / "result.xlsx"

    exit_code = app.main(
        [
            "--no-gui",
            "scan.pdf",
            "--output",
            str(output),
            "--ocr",
            "force",
            "--ocr-min-confidence",
            "0.94",
        ]
    )

    assert exit_code == 0
    assert captured["inputs"] == [Path("scan.pdf")]
    assert captured["output"] == output
    assert captured["options"] == ExtractionOptions(
        ocr_mode="force",
        ocr_min_confidence=0.94,
    )


def test_cli_reports_missing_ocr_support_without_native_failure(tmp_path, monkeypatch) -> None:
    def fake_run(*args, **kwargs):
        raise OcrSupportRequired("not installed")

    monkeypatch.setattr(app, "run_extraction", fake_run)

    exit_code = app.main(
        [
            "--no-gui",
            "scan.pdf",
            "--output",
            str(tmp_path / "result.xlsx"),
        ]
    )

    assert exit_code == 3


def test_cli_can_install_offline_ocr_package(tmp_path, monkeypatch) -> None:
    package = tmp_path / "ocr.zip"
    package.write_bytes(b"placeholder")
    worker = tmp_path / "installed" / "ocr_worker.exe"
    captured: dict[str, Path] = {}

    def fake_install(self, package_path):
        captured["package"] = package_path
        return InstalledOcrSupport("2.0.0", worker, ("det", "rec"))

    monkeypatch.setattr(app.OcrSupportManager, "install_from_package", fake_install)

    assert app.main(["--ocr-package", str(package)]) == 0
    assert captured["package"] == package


def test_cli_returns_install_error_code(tmp_path, monkeypatch) -> None:
    package = tmp_path / "bad.zip"
    package.write_bytes(b"bad")

    def fake_install(self, package_path):
        raise OcrInstallError("checksum mismatch")

    monkeypatch.setattr(app.OcrSupportManager, "install_from_package", fake_install)

    assert app.main(["--ocr-package", str(package)]) == 2


def test_gui_job_orchestration_uses_timestamped_output(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_run(input_paths, output_xlsx, log, options):
        captured["inputs"] = input_paths
        captured["output"] = output_xlsx
        captured["options"] = options
        return output_xlsx, output_xlsx.with_suffix(".csv"), 4, []

    monkeypatch.setattr(app, "run_extraction", fake_run)
    options = ExtractionOptions(ocr_mode="auto")

    xlsx, csv_path, count, warnings = app.execute_extraction_job(
        [Path("sample.pdf")],
        tmp_path,
        options,
    )

    assert xlsx.parent == tmp_path
    assert xlsx.name.startswith("serial_numbers_")
    assert csv_path == xlsx.with_suffix(".csv")
    assert count == 4
    assert warnings == []
    assert captured["inputs"] == [Path("sample.pdf")]
    assert captured["options"] == options
