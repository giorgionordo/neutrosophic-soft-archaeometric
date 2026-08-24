from __future__ import annotations

from pathlib import Path

import pandas as pd


CANONICAL_SHEETS = {
    "evidence.csv": "Evidence",
    "sources.csv": "Sources",
    "hypotheses.csv": "Hypotheses",
    "v7_evidence_base.csv": "V7_Evidence_Base",
    "v7_evidence_hypothesis_links.csv": "V7_Evidence_Hypothesis_Link",
    "v7_results.csv": "V7_Results",
    "v9_meta_components.csv": "V9_Meta_Components",
    "v9_meta_families.csv": "V9_Meta_Families",
    "v9_synthesis_results.csv": "V9_Synthesis_Results",
    "v9_weight_sensitivity.csv": "V9_Weight_Sensitivity",
    "v9_relevance_sensitivity.csv": "V9_Relevance_Sensitivity",
}


def read_canonical_csvs(data_dir: Path) -> dict[str, pd.DataFrame]:
    tables = {}
    for filename in CANONICAL_SHEETS:
        key = filename.removesuffix(".csv")
        tables[key] = pd.read_csv(data_dir / filename)
    return tables


def export_workbook_tables(workbook: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, sheet in CANONICAL_SHEETS.items():
        df = pd.read_excel(workbook, sheet_name=sheet)
        df.to_csv(output_dir / filename, index=False, encoding="utf-8")
