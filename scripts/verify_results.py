from __future__ import annotations

import argparse
import re
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riace_ivn.aggregate import aggregate_v7_results, aggregate_v9_synthesis
from riace_ivn.io import read_canonical_csvs
from riace_ivn.model import compute_link_state


def _assert_close(name: str, actual: float, expected: float, tolerance: float = 1e-9) -> None:
    if abs(float(actual) - float(expected)) > tolerance:
        raise AssertionError(f"{name}: actual={actual} expected={expected}")


def verify_link_formulas(links: pd.DataFrame) -> None:
    for _, row in links.iterrows():
        computed = compute_link_state(row)
        for key, value in computed.items():
            _assert_close(f"{row['Link_ID']} {key}", value, row[key], 2e-9)


def verify_v7(tables: dict[str, pd.DataFrame]) -> None:
    computed = aggregate_v7_results(tables["v7_evidence_hypothesis_links"], tables["hypotheses"])
    expected = tables["v7_results"].dropna(subset=["T_mid"]).copy()
    merged = expected.merge(computed, on="Hypothesis_ID", suffixes=("_expected", "_computed"))
    for _, row in merged.iterrows():
        for key in ("T_mid", "I_final_mid", "F_mid", "Net_mid"):
            _assert_close(f"{row['Hypothesis_ID']} {key}", row[f"{key}_computed"], row[f"{key}_expected"], 2e-9)


def verify_v9(tables: dict[str, pd.DataFrame]) -> None:
    computed = aggregate_v9_synthesis(tables["v9_meta_components"], tables["v9_meta_families"])
    expected = tables["v9_synthesis_results"]
    merged = expected.merge(computed, on="Hypothesis_ID", suffixes=("_expected", "_computed"))
    for _, row in merged.iterrows():
        for key in ("T_mid", "I_mid", "F_mid", "Net_mid"):
            _assert_close(f"{row['Hypothesis_ID']} {key}", row[f"{key}_computed"], row[f"{key}_expected"], 2e-9)


def verify_latex(latex: Path | None, tables: dict[str, pd.DataFrame]) -> None:
    if latex is None:
        return
    text = latex.read_text(encoding="utf-8")
    if "62 atomic evidence records and 112 active evidence--hypothesis links" not in text:
        raise AssertionError("LaTeX manuscript does not declare the audited 62/112 dataset counts.")
    for _, row in tables["v9_synthesis_results"].iterrows():
        hid = row["Hypothesis_ID"]
        for key, latex_key in (("T_mid", "T"), ("I_mid", "I"), ("F_mid", "F")):
            rounded = f"{row[key]:.3f}"
            pattern = rf"{latex_key}_\{{{hid[-2:]},\\mathrm\{{mid\}}\}}={rounded}"
            if hid == "H21":
                token = rounded
            else:
                token = rounded
            if token not in text:
                raise AssertionError(f"LaTeX manuscript missing rounded {hid} {key}={rounded}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify Riace IVN dataset and manuscript results.")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "canonical")
    parser.add_argument("--latex", type=Path)
    args = parser.parse_args()

    tables = read_canonical_csvs(args.data_dir)
    evidence_count = len(tables["v7_evidence_base"])
    link_count = len(tables["v7_evidence_hypothesis_links"])
    roles = tables["v7_evidence_hypothesis_links"]["Role"].value_counts().to_dict()
    if evidence_count != 62 or link_count != 112:
        raise AssertionError(f"Unexpected counts: evidence={evidence_count}, links={link_count}")
    if roles != {"DIRECTIONAL": 71, "LIMITATION": 26, "CONTEXT": 15}:
        raise AssertionError(f"Unexpected role counts: {roles}")

    verify_link_formulas(tables["v7_evidence_hypothesis_links"])
    verify_v7(tables)
    verify_v9(tables)
    verify_latex(args.latex, tables)

    print("Verification passed: counts, link formulas, V7 aggregation, V9 synthesis, and LaTeX checks.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
