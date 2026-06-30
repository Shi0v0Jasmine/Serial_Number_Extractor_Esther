# Versioning

Current source version: `2.0.0`.

Latest released version: `2.0.0`.

Use semantic versioning:

```text
MAJOR.MINOR.PATCH
```

## Major

Increase the first number when a new main workflow is added.

Examples:

- Add OCR/scanned-PDF workflow.
- Add a non-PDF input workflow that changes the tool boundary materially.

## Minor

Increase the second number when support expands while the main workflow stays the same.

Examples:

- Add a major new vendor adapter.
- Add a new output mode or broad extraction capability.
- Add structured configuration for vendor rules.

## Patch

Increase the third number for fixes.

Examples:

- Correct a vendor-specific parsing rule.
- Fix quantity validation or duplicate handling.
- Fix S/N vs USI Code priority.
- Update documentation or packaging metadata.

## Current Scope

`2.0.0` adds:

- a testable `serial_extractor` core package;
- native text, layout-table, marker, and optional local PaddleOCR backends;
- confidence-gated OCR output and a separate `Review` worksheet;
- local sidecar installation with checksum verification and atomic upgrades;
- automated tests and CI gates.

Do not tag or release a new version until the local commercial PDF regression, fast
pytest suite, PaddleOCR integration test, coverage gate, executable smoke, and OCR
support install smoke have passed.
