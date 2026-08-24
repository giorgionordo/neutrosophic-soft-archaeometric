# neutrosophic-soft-archaeometric

Reproducible Python support for Paper I of the Riace Bronzes
source-aware interval-valued neutrosophic soft framework.

The repository intentionally keeps Paper I non-topological. It validates the
sparse Evidence x Hypothesis layer, role-aware DIRECTIONAL/CONTEXT/LIMITATION
coding, dependency groups, evidence families, hierarchical aggregation, and the
second-order H21/H33 synthesis used in the LaTeX manuscript.

## Current Canonical Dataset

The current workbook source is:

`C:\Users\Giorgio\Desktop\neutrosophic_archaeometric\datasets\Riace_Bronzes_Evidence_Dataset_v9_H21_synthesis.xlsx`

The canonical exported CSV tables are stored under `data/canonical/`.

Key audited counts:

- `V7_Evidence_Base`: 62 atomic evidence records.
- `V7_Evidence_Hypothesis_Link`: 112 active evidence-hypothesis links.
- Link roles: 71 DIRECTIONAL, 26 LIMITATION, 15 CONTEXT.
- `V9_Synthesis_Results`: H21 and H33 second-order synthesis.

## Quick Start

Install runtime dependencies in your preferred environment:

```powershell
python -m pip install pandas openpyxl numpy
```

Export the canonical CSVs from the workbook:

```powershell
python scripts/export_from_workbook.py --workbook "C:\Users\Giorgio\Desktop\neutrosophic_archaeometric\datasets\Riace_Bronzes_Evidence_Dataset_v9_H21_synthesis.xlsx"
```

Verify formulas, aggregation, counts, and H21/H33 manuscript numbers:

```powershell
python scripts/verify_results.py --latex "C:\Users\Giorgio\Desktop\neutrosophic_archaeometric\neutrosophic_soft_archeometric.tex"
python -m unittest discover -s tests
```

## Validation Notes

`data/validation/e001_e015_source_audit.csv` records the first source audit
pass for E001-E015. E001-E012 were checked against Lombardi and Vidale 1998
(casting cores); E013-E015 were checked against Calcagnile et al. 2010
(preliminary AMS radiocarbon study).

The validation file is intentionally separate from the historical workbook so
the original dataset versions remain intact.
