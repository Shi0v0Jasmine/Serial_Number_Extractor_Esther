from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path


VERSION = "2.0.0"
TAG = f"v{VERSION}"
REPOSITORY_URL = "https://github.com/Shi0v0Jasmine/Serial_Number_Extractor_Esther"
MODELS = ("PP-OCRv6_small_det", "PP-OCRv6_small_rec")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_zip(zip_path: Path, files: list[tuple[Path, str]]) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, arcname in files:
            archive.write(source, arcname)


def collect_tree(root: Path, prefix: str) -> list[tuple[Path, str]]:
    return [
        (path, str(Path(prefix) / path.relative_to(root)).replace("\\", "/"))
        for path in sorted(root.rglob("*"))
        if path.is_file()
    ]


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def require_dir(path: Path) -> Path:
    if not path.is_dir():
        raise FileNotFoundError(path)
    return path


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    dist = root / "dist"
    release_dir = root / "release" / TAG
    release_dir.mkdir(parents=True, exist_ok=True)

    main_zip = release_dir / f"SerialNumberExtractor_{TAG}_Windows.zip"
    ocr_zip = release_dir / f"SerialNumberExtractor_OCRSupport_{TAG}_Windows.zip"
    manifest_path = release_dir / "ocr_support_manifest.json"
    checksums_path = release_dir / "SHA256SUMS.txt"

    write_zip(
        main_zip,
        [
            (require_file(dist / "SerialNumberExtractor.exe"), "SerialNumberExtractor.exe"),
            (require_file(dist / "SerialNumberExtractorCLI.exe"), "SerialNumberExtractorCLI.exe"),
            (require_file(root / "README.md"), "README.md"),
        ],
    )

    model_root = Path.home() / ".paddlex" / "official_models"
    with tempfile.TemporaryDirectory(prefix="serial-ocr-package-") as temp:
        temp_root = Path(temp)
        package_root = temp_root / "ocr_support"
        package_root.mkdir()
        shutil.copy2(require_file(dist / "ocr_worker.exe"), package_root / "ocr_worker.exe")
        (package_root / "ocr_support.json").write_text(
            json.dumps(
                {
                    "version": VERSION,
                    "worker": "ocr_worker.exe",
                    "paddlepaddle": "3.2.2",
                    "paddleocr": "3.7.0",
                    "require_model_dirs": True,
                    "models": list(MODELS),
                },
                indent=2,
                ensure_ascii=True,
            ),
            encoding="utf-8",
        )
        for model in MODELS:
            shutil.copytree(require_dir(model_root / model), package_root / "models" / model)
        write_zip(ocr_zip, collect_tree(package_root, ""))

    ocr_sha = sha256_file(ocr_zip)
    manifest_path.write_text(
        json.dumps(
            {
                "version": VERSION,
                "package_url": f"{REPOSITORY_URL}/releases/download/{TAG}/{ocr_zip.name}",
                "sha256": ocr_sha,
            },
            indent=2,
            ensure_ascii=True,
        ),
        encoding="utf-8",
    )

    checksums = {
        main_zip.name: sha256_file(main_zip),
        ocr_zip.name: ocr_sha,
        manifest_path.name: sha256_file(manifest_path),
    }
    checksums_path.write_text(
        "".join(f"{digest}  {name}\n" for name, digest in checksums.items()),
        encoding="utf-8",
    )
    print(release_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
