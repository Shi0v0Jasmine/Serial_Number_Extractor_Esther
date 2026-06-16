# Versioning

Current version: `1.0.2`.

Latest released version: `1.0.2`.

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

`1.0.x` covers:

- local PDF text extraction without OCR;
- GUI and CLI operation;
- Excel / CSV output;
- `Part Number`, `Part Name`, `Serial Number`, `Order Qty`, `Serial Count`, and `Qty Check`;
- vendor-specific parsing for the currently verified Esther samples;
- warnings instead of hard failure for quantity mismatch or unverified counts.
