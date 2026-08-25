# neutrosophic-soft-archaeometric

Reproducible Python support for the Riace Bronzes source-aware
interval-valued neutrosophic soft framework.

The repository follows the manuscript's non-topological scope. It validates the
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

Generate the manuscript figures from the canonical CSV outputs:

```powershell
python scripts/generate_figures.py
```

The generated vector PDFs are written to `figures/`:

- `ivn_h21_h33_profile.pdf` reports the H21/H33 interval-valued
  neutrosophic profile.
- `h21_h33_weight_sensitivity.pdf` reports the H21/H33 net midpoint under
  the domain-weight sensitivity scenarios.

Run the standard reproduction workflow from this repository root:

```powershell
.\reproduce.ps1
```

This verifies the canonical counts and formulas, runs the test suite,
regenerates the figure PDFs, and copies them to the manuscript-level
`figures/` folder. Add `-CompileLatex` to compile the manuscript PDF as part
of the same workflow, or `-ExportWorkbook` when the workbook source has been
changed intentionally and the canonical CSVs must be refreshed.

See `SUPPLEMENTARY_MATERIALS.md` for the dataset, validation, figure and
experimental-file index.

## Validation Notes

`data/validation/e001_e015_source_audit.csv` records the first source audit
pass for E001-E015. E001-E012 were checked against Lombardi and Vidale 1998
(casting cores); E013-E015 were checked against Calcagnile et al. 2010
(preliminary AMS radiocarbon study).

`data/validation/e016_e030_source_audit.csv` records the second source audit
pass. E016-E019 were checked against Calcagnile et al. 2010; E020-E030 were
checked against Quarta, Calcagnile and Vidale 2012.

`data/validation/e031_e045_source_audit.csv` records the third source audit
pass. E031-E032 were checked against Quarta, Calcagnile and Vidale 2012;
E033-E042 were checked against Jones et al. 2016; E043-E045 were checked
against the Angelini et al. Getty abstract and are therefore marked
`SOURCE-CHECKED-ABSTRACT-ONLY`.

`data/validation/e046_e062_source_audit.csv` records the fourth source audit
pass. E046 was checked against the Angelini et al. Getty abstract; E047 against
Buccolieri et al. 2015; E048-E050, E052 and E057-E062 against Cirrincione et
al. 2026; E051 and E053-E055 against Jones et al. 2016; and E056 against
Calcagnile et al. 2010.

The validation file is intentionally separate from the historical workbook so
the original dataset versions remain intact.

## Material Accession and V10 Source Triage

The manuscript-level folder `C:\Users\Giorgio\Desktop\neutrosophic_archaeometric\materiale` stores locally recovered PDFs, HTML records, and download manifests. Large or copyrighted source PDFs are not versioned in this repository.

`data/validation/v10_source_material_triage.csv` records the conservative bridge from the local material folder to the candidate dataset expansion. It identifies which sources are already active in the 62-evidence canonical matrix, which newly downloaded files can support page-level audit, and which records remain bibliographic/manual recovery targets only.

The v10 triage does not change the canonical 62 evidence records or 112 active links. It is a staging file for source-checked additions, especially patina chemistry, restoration history, and carefully separated geological measurement versus historical synthesis.
The S06 patina audit is split into two non-canonical validation files:

- `data/validation/s06_patina_page_audit.csv` records page-level checks of Buccolieri et al. 2015.
- `data/validation/v10_candidate_evidence.csv` proposes candidate E063-E066 rows for optional activation after hypothesis-link scoring.

These candidates are intentionally excluded from the canonical aggregation until their link roles, dependency groups, and support/opposition intervals are reviewed.

Candidate link scores for a first H20 scenario are stored in
`data/validation/v10_candidate_link_scoring.csv`. They can be evaluated without
altering canonical outputs with:

```powershell
python scripts/run_candidate_impact.py
```

The script writes ignored scratch outputs under
`data/tmp/v10_candidate_s06/`. In the current S06 scenario, adding candidate
patina links keeps H20 support stable but increases structured
indeterminacy, because the same surface chemistry supports a multi-phase
alteration history while also limiting direct depositional interpretation.

## Experimental Refinements

`src/riace_ivn/experimental_refinements.py` contains optional, non-baseline
helpers for optional methodological experiments. The experimental CSV schema is:

`evidence_id, bronze, meta_family, level, dependency_DAG, r_scores, m_scores, a_scores, d_scores, s_scores, o_scores, role`

Score cells contain comma-separated Delphi panel scores, for example
`"3,3,2"`. The `dependency_DAG` cell stores incoming lineage edges in compact
form, for example `E001:0.35;E004:0.20`, where each number is the beta reuse
weight for genealogic discounting.

- Delphi consensus intervals from panel scores such as `"3,3,2"`.
- Algebraic data-lineage novelty discounting.
- Interval-valued neutrosophic entropy weights.
- IVN TOPSIS ranking against positive/negative ideal states.
- Monte Carlo perturbation of the full Delphi -> DAG -> entropy -> TOPSIS
  chain.

Run the template example with:

```powershell
python scripts/run_experimental_refinements.py --input data/examples/delphi_refinement_template.csv --output-dir data/tmp/v10_example --iterations 100 --seed 20260824
```

These functions do not alter the canonical V7/V9 reproduction. They are
provided so that Delphi, entropy-weighting, TOPSIS and Monte Carlo
experiments can be run without changing the manuscript's current baseline.
By default, the experimental aggregation ranks only DIRECTIONAL rows; CONTEXT
and LIMITATION rows remain visible in the evidence-level export and can be
included explicitly with `--include-nondirectional`.

