# Serial Number Extractor

Local tool for extracting vendor PDF shipment data into Excel and CSV:

- `Part Number`
- `Part Name`
- `Serial Number`
- `Order Qty`
- `Serial Count`
- `Qty Check`

Current version: `2.0.1`.
Latest GitHub release: `2.0.1`.

## Workflow

Each page is processed in this order:

1. Extract native PDF text with pypdf.
2. Extract layout spans and table structure with pdfplumber.
3. If a page has no usable native text, or `--ocr force` is selected, call the local PaddleOCR sidecar.
4. Choose results by priority: explicit vendor/layout structure, generic table, marker block, restricted strong-pattern fallback.

OCR is local only. PDFs and images do not leave the machine. Low-confidence OCR candidates, ambiguous OCR text, and unanchored OCR candidates go to the `Review` sheet instead of the main output.

## GUI

Run from source:

```powershell
python -m pip install -r requirements.txt
python serial_number_extractor.py
```

1. Use `Add PDFs` or `Add Folder` to select input.
2. Select `OCR: auto/off/force`.
3. Select the output directory.
4. Click `Extract to Excel`.

When a scanned page is detected and OCR support is not installed, the GUI can prompt for online install or an offline OCR package.

## CLI

```powershell
python serial_number_extractor.py --no-gui "<PDF-or-folder>" -o "output.xlsx"
```

OCR options:

```text
--ocr auto|off|force
--ocr-min-confidence 0.90
--install-ocr
--ocr-package <offline-package.zip>
```

Version:

```powershell
python serial_number_extractor.py --version
```

## Output

- `SAP_Copy`: six-column main output.
- `Details`: source/page/method/backend/strategy/score/OCR confidence/bbox.
- `Review`: OCR candidates that were not accepted into the main output, with part context.
- `Summary`: file counts, part quantity checks, native/OCR/review counts, OCR status, and warnings.
- CSV: same semantic rows as `SAP_Copy`.

`MISMATCH` and `UNVERIFIED` do not stop export. They are shown in the main sheet, Summary, and logs.

## S/N And USI

- If S/N or Serial and USI Code both appear in the same product block, S/N or Serial wins.
- If a product block has only USI Code, the USI Code is emitted as the serial number.
- S/N and USI aliasing is scoped to the product block; it is not applied globally across the document.

## Development Tests

```powershell
python -m pip install -r requirements-dev.txt
python scripts/core_smoke.py
python -m pytest -m "not real_pdf and not ocr_integration"
```

Commercial PDFs are not committed to Git. Configure local roots before running real PDF tests:

```powershell
$env:SERIAL_EXTRACTOR_REAL_PDF_ROOTS = "<sample-dir>;<adtran-fix-dir>"
python -m pytest -m real_pdf
```

PaddleOCR integration tests:

```powershell
python -m pip install -r requirements-ocr.txt
$env:RUN_PADDLEOCR_TESTS = "1"
python -m pytest -m ocr_integration
```

More detail:

- [Test strategy](docs/TEST_STRATEGY.md)
- [Real PDF regression](docs/REAL_PDF_REGRESSION.md)
- [OCR sidecar contract](ocr_support/README.md)

## Build Release

```powershell
cmd /c build_release.cmd
```

This creates release assets under `release/v2.0.1/`:

- `SerialNumberExtractor_v2.0.1_Windows.zip`
- `SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip`
- `ocr_support_manifest.json`
- `SHA256SUMS.txt`

## Release Checklist

Before publishing a release, run fast pytest, PaddleOCR integration, coverage, the 9-file local real PDF regression, main executable smoke, and OCR support install smoke. Commercial PDFs, real extraction outputs, local dependency directories, model caches, and temporary build output are not committed.
