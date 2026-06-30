# Local Real PDF Regression

Real commercial PDFs are tested only on the local machine. They are not copied into the repository.

## Configure

```powershell
$env:SERIAL_EXTRACTOR_REAL_PDF_ROOTS = "C:\path\original-7-sample-dir;C:\path\adtran-fix-2-sample-dir"
```

## Run

```powershell
python -m pytest -m real_pdf
```

## Approved Baseline

| Scope | Expected |
| --- | ---: |
| Original 7 samples | 1073 |
| Adtran fix samples | 242 |
| Total | 1315 |
| Qty Check OK | 1315 |
| Part `1063707680-11` | 0 |
| Serial ending in `SN` | 0 |

ECI additionally requires `1/1`, `12/12`, and `2/2` for its three product blocks:

- `ON324921 / OTR100Q28_LR4 / 1`
- `ON324921 / OTR100Q28_LR4 / 12`
- `X66706 / TM400ENB INCLUDING FIPS KIT / 2`

Any semantic difference must be reviewed before updating `tests/fixtures/real_pdf_baseline.json`.

To compare a previous release CSV with the v2 CSV:

```powershell
python scripts/compare_semantic_csv.py "<v1.csv>" "<v2.csv>"
```

Only approved ECI Qty/Qty Check mapping changes and new diagnostics are expected to differ.
