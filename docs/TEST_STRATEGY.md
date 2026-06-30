# Test Strategy

## TDD Cycle

Every parser change should follow Red -> Green -> Refactor:

1. Add a failing test using sanitized text, layout spans, or a runtime-generated synthetic PDF.
2. Implement the smallest rule that makes the test pass.
3. Run vendor contract and negative tests to check that the false-positive surface did not grow.
4. Refactor into the strategy/model layer only after behavior is covered.
5. Finish with the 9-file local commercial PDF semantic regression.

## Test Layers

- Unit: normalization, ranges, part detection, candidate filtering, S/N-USI aliasing, and Qty validation.
- Strategy contract: Adtran, ECI, RUID, Smartoptics, DTC, Ciena, PURE IT, and unknown generic table.
- Layout: column order changes, whitespace, repeated headers, cross-page continuation, and multiple independent Qty blocks for the same PN.
- Negative: commodity code, Activation ID, price, order number, date, page number, empty values, metadata, and payment details.
- PDF integration: native text, scanned page, force/off OCR, corrupt PDF, and encrypted PDF.
- OCR: Paddle payload adapter, confidence/Review policy, and real local Paddle synthetic scan.
- Output: CSV/SAP_Copy equivalence, Review isolation from main output, and traceable Summary warnings.
- Installer: checksum, zip traversal, offline package, network failure, repeated install, upgrade, and failed-upgrade rollback.
- Real PDF: 9 local files, total `1315`.

## Commands

```powershell
python scripts/core_smoke.py
python -m pytest -m "not real_pdf and not ocr_integration"
python -m pytest -m real_pdf
python -m pytest -m ocr_integration
python -m pytest --cov=serial_extractor --cov-report=term-missing
```

## Coverage Gates

- Parser/pipeline target: at least 90%.
- Complete project target: at least 80%.

Do not build or release if coverage is below the gate. GUI toolkit drawing code can be reported separately, but GUI orchestration must be covered through testable entrypoints.

## Fixture Policy

- Do not commit commercial PDFs, customer data, or real serial-number lists.
- Git fixtures may include only sanitized text, layout spans, synthetic image/PDF generators, and approved count baselines.
- `tests/local_real_pdfs.json` is ignored by Git for local-only regression configuration.
