# Changelog

## 2026-08-24

- Audited the local manuscript and v9 workbook alignment.
- Confirmed the canonical workbook contains 62 evidence records and 112 active
  evidence-hypothesis links.
- Added reproducible Python code for link-level IVN formulas, V7 role-aware
  hierarchical aggregation, and V9 second-order H21/H33 synthesis.
- Added canonical CSV export workflow from the v9 workbook.
- Added source validation notes for E001-E015 against the S01/S02 primary PDFs.
- Added `unittest` coverage for dataset integrity, link formulas, V7
  aggregation, V9 synthesis, and LaTeX/result consistency.
- Added source validation notes for E016-E030 against the S02/S03 primary PDFs.
- Added optional experimental helpers for Delphi consensus intervals,
  data-lineage novelty discounting, IVN entropy weights, IVN TOPSIS, and
  Monte Carlo Delphi perturbation. These do not alter canonical V7/V9 results.
- Added a reproducible V10-style experimental refinement pipeline and CLI for
  the requested Delphi score schema, compact lineage DAG cells, entropy
  meta-family weighting, TOPSIS ranking, and Monte Carlo RC confidence samples.
- Added `data/examples/delphi_refinement_template.csv` and tests covering the
  new schema, DAG parsing, genealogic discounting, full pipeline outputs, and
  Monte Carlo confidence tables.
- Added source validation notes for E031-E045 against the S03, S04 and S05
  PDFs, including explicit abstract-only status for E043-E045.
- Added source validation notes for E046-E062 against the S02, S04, S05, S06
  and S07 PDFs, completing the staged audit of all 62 evidence records.
- Added `scripts/generate_figures.py` and reproducible vector PDF figures for
  the H21/H33 IVN profile and weight-sensitivity comparison.
