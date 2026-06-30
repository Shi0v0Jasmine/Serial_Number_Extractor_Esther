# Serial Number Extractor v2.0.1

## Fixes

- Fixed `OCR: force` so all selected pages use PaddleOCR results instead of
  silently keeping usable native PDF text.
- Added Smartoptics product-row support for native PDF and PaddleOCR reading
  orders, including cross-page serial continuation.
- Corrected legacy Smartoptics mapping: the numeric `Product` value is
  `Part Number`, and the short model is `Part Name`.
- Restricted Smartoptics `K...` and `G...` serial patterns to confirmed product
  blocks, excluding customs codes and description tokens.
- Added the bilingual `OCR_USAGE_GUIDE_CN_EN.md` to the main Windows package.

## Validation

- Fast test suite: 85 passed.
- Commercial PDF regression: 9 PDFs, 1315 records, all `OK`.
- PaddleOCR integration: passed.
- Coverage: `serial_extractor/app.py` 90%; overall 87%.
- Packaged CLI native regression: 1315 records, all `OK`.
- Packaged OCR force smoke: 128 Smartoptics records, all from `paddleocr`, all
  `OK`, with zero semantic difference from the approved native result.
- Forbidden Part Number `1063707680-11`: 0.
- Serial values ending in `SN`: 0.

## Windows Assets

- `SerialNumberExtractor_v2.0.1_Windows.zip`: GUI, CLI, README, and bilingual
  OCR usage guide.
- `SerialNumberExtractor_OCRSupport_v2.0.1_Windows.zip`: local PaddleOCR CPU
  runtime and models.
- `ocr_support_manifest.json`: online OCR installer manifest with SHA256.

Docker and a separate Python installation are not required.
