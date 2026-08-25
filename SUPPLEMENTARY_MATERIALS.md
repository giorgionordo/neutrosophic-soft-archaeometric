# Supplementary Materials Index

This repository contains the reproducible computational package for the paper.
The paper remains non-topological and uses the source-aware interval-valued
neutrosophic soft baseline described in the paper.

## Canonical Data

- `data/canonical/evidence.csv`: exported evidence table.
- `data/canonical/hypotheses.csv`: hypothesis catalogue.
- `data/canonical/sources.csv`: bibliographic source catalogue.
- `data/canonical/v7_evidence_base.csv`: 62 atomic evidence records.
- `data/canonical/v7_evidence_hypothesis_links.csv`: 112 active
  evidence-hypothesis links.
- `data/canonical/v7_results.csv`: role-aware dependency/family aggregation.
- `data/canonical/v9_meta_components.csv`: H21/H33 second-order components.
- `data/canonical/v9_meta_families.csv`: H21/H33 meta-family weights.
- `data/canonical/v9_synthesis_results.csv`: H21/H33 synthesis.
- `data/canonical/v9_weight_sensitivity.csv`: domain-weight scenarios.
- `data/canonical/v9_relevance_sensitivity.csv`: meta-relevance scenarios.

## Source Validation

- `data/validation/e001_e015_source_audit.csv`
- `data/validation/e016_e030_source_audit.csv`
- `data/validation/e031_e045_source_audit.csv`
- `data/validation/e046_e062_source_audit.csv`

The audit files record the staged source check of all 62 evidence records.
Records based only on an available conference abstract are explicitly marked as
abstract-only.

## Reproduction Scripts

- `scripts/verify_results.py`: verifies counts, link formulas, V7 aggregation,
  V9 synthesis and the rounded paper values.
- `scripts/generate_figures.py`: regenerates the vector PDF figures used by
  the paper.
- `scripts/export_from_workbook.py`: re-exports canonical CSVs from the
  workbook source when needed.
- `reproduce.ps1`: runs the standard reproduction workflow and copies the
  generated figures to the paper-level `figures/` directory.

## Figures

- `figures/ivn_h21_h33_profile.pdf`
- `figures/h21_h33_weight_sensitivity.pdf`

These figures are generated from the canonical CSV outputs and should not be
edited manually.

## Experimental, Non-Baseline Material

- `src/riace_ivn/experimental_refinements.py`
- `scripts/run_experimental_refinements.py`
- `data/examples/delphi_refinement_template.csv`

These files support optional Delphi, lineage-discounting, entropy-weighting,
IVN TOPSIS and Monte Carlo experiments. They do not alter the baseline V7/V9
results reported in the paper.

## V10 Source-Material Triage

- `data/validation/v10_source_material_triage.csv` maps the locally recovered `materiale/` sources to conservative candidate dataset actions. It is intentionally non-canonical and does not alter the 62 evidence records or 112 active links used in the current paper results.

## S06 Patina Audit and Candidate Evidence

- `data/validation/s06_patina_page_audit.csv` records a page-level audit of Buccolieri et al. 2015, focused on patina composition, corrosion indicators, restoration residues and A/B surface-patina discrimination.
- `data/validation/v10_candidate_evidence.csv` lists candidate E063-E066 rows. These rows are not part of the canonical aggregation until their IVN link scores and roles are explicitly assigned.
- `data/validation/v10_candidate_link_scoring.csv` assigns provisional non-canonical H20 links and IVN score intervals to E063-E066.
- `scripts/run_candidate_impact.py` compares the canonical H20 aggregation with the non-canonical S06 candidate scenario and writes ignored scratch outputs under `data/tmp/v10_candidate_s06/`.

