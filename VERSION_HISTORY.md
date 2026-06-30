# Serial Number Extractor Version History

Version format: `MAJOR.MINOR.PATCH`. Update this file and `references/versioning.md` before each release.

## Current State

- Current source version: `2.0.0`.
- Latest released version: `2.0.0`.

## `2.0.0` - 2026-06-29

Reason for MAJOR: adds scanned-PDF/OCR support and splits the former monolithic script into a testable extraction package.

### Added

- New `serial_extractor` package with unified models: `DocumentPage`, `TextSpan`, `ProductBlock`, `SerialRecord`, and `ReviewCandidate`.
- pdfplumber layout-table extraction with header synonyms, column order changes, repeated headers, and cross-page serial continuation.
- ECI layout mapping for:
  - `ON324921 / OTR100Q28_LR4 / 1`
  - `ON324921 / OTR100Q28_LR4 / 12`
  - `X66706 / TM400ENB INCLUDING FIPS KIT / 2`
- Optional local PaddleOCR sidecar pinned to `paddlepaddle==3.2.2`, `paddleocr==3.7.0`, `PP-OCRv6_small_det`, and `PP-OCRv6_small_rec`.
- CLI options: `--ocr`, `--ocr-min-confidence`, `--install-ocr`, `--ocr-package`, and `--version`.
- New `Review` sheet. `Details` and `Summary` now include backend, strategy, score, OCR confidence, bbox, and OCR status diagnostics.
- pytest/Hypothesis tests covering synthetic PDFs, installer behavior, CLI, output schema, vendor contracts, real PDF regression, and PaddleOCR integration.
- Windows/Linux GitHub Actions fast tests and a Windows PaddleOCR integration job.
- Release packaging script for GUI/CLI executables, OCR support zip, SHA256 checksums, and OCR download manifest.

### Changed

- Parser priority is now explicit vendor/layout structure, generic table, marker block, then restricted strong-pattern fallback.
- OCR candidates must be in a serial column or marker area and meet the confidence threshold before entering the main output.
- Low-confidence OCR candidates keep the raw text and do not auto-correct ambiguous characters such as `O/0`, `I/1`, or `S/5`.
- S/N priority is scoped to one product block. If only USI Code exists in that block, USI Code is still emitted.
- Removed broad ECI full-document numeric fallback to avoid order numbers, prices, commodity codes, and document metadata.
- Marker fallback now stops at obvious document metadata boundaries such as `Packing List`, bank/payment lines, and account details.
- OCR layout grouping is more tolerant for PaddleOCR bbox jitter while keeping native PDF layout grouping unchanged.
- The local Windows CPU OCR runtime uses `paddlepaddle==3.2.2`; `3.3.1` hit a oneDNN/PIR runtime error on the tested Windows machine.

### Acceptance Baseline

- Original 7 samples: `1073` records, including ECI `15/15 OK`.
- Two Adtran fix samples: `242` records, all `OK`.
- Total: `1315` records.
- `Part Number = 1063707680-11`: `0`.
- Serial ending in `SN`: `0`.
- Raw commercial PDFs are not committed to Git.

### Release Status

Release package includes Windows GUI/CLI executables plus an optional offline OCR support package and download manifest. The release gate is fast pytest, PaddleOCR integration, coverage, the local 9-PDF regression, executable smoke, and OCR support install smoke.

## `1.0.2` - 2026-06-16

- Fixed Adtran `This Position Line Contains`: the row contributes only Qty; Part Number and Part Name stay on the parent product block.
- Added `BC########` Part Number recognition.
- Fixed `SN:FA...` being extracted as `FA...SN`.
- Clarified S/N priority and USI fallback behavior.
- Released as GitHub `v1.0.2`.

Verification at that time: two Adtran fix samples had `242` records, all `OK`; original 7 samples had `1073` records, with ECI still `UNVERIFIED`.

## `1.0.1` - 2026-06-16

- Fixed Adtran mismatch caused by S/N and USI appearing together.
- Released as GitHub `v1.0.1`.

## `1.0.0` - 2026-06-16

- First GUI/CLI release with Excel/CSV output, Part/Serial extraction, and Qty validation.
- Verified against Esther's original 7 samples with `1073` records.
