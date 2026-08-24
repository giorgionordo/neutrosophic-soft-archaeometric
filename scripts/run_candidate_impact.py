from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from riace_ivn.aggregate import aggregate_v7_results
from riace_ivn.io import read_canonical_csvs
from riace_ivn.model import compute_link_state


FORMULA_COLUMNS = [
    "Q_low",
    "Q_high",
    "T_low",
    "T_high",
    "I_low",
    "I_high",
    "F_low",
    "F_high",
    "C_low",
    "C_high",
]


def load_candidate_links(path: Path) -> pd.DataFrame:
    """Load non-canonical candidate link scores and compute IVN columns."""

    links = pd.read_csv(path)
    for idx, row in links.iterrows():
        state = compute_link_state(row)
        for key in FORMULA_COLUMNS:
            links.loc[idx, key] = state[key]
        links.loc[idx, "T_mid"] = (state["T_low"] + state["T_high"]) / 2.0
        links.loc[idx, "I_mid"] = (state["I_low"] + state["I_high"]) / 2.0
        links.loc[idx, "F_mid"] = (state["F_low"] + state["F_high"]) / 2.0
    return links


def build_candidate_impact(
    canonical_dir: Path,
    candidate_links_path: Path,
    hypothesis_id: str = "H20",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare canonical aggregation with a non-canonical candidate scenario."""

    tables = read_canonical_csvs(canonical_dir)
    canonical_links = tables["v7_evidence_hypothesis_links"]
    hypotheses = tables["hypotheses"]
    candidate_links = load_candidate_links(candidate_links_path)

    baseline = aggregate_v7_results(canonical_links, hypotheses)
    augmented = aggregate_v7_results(
        pd.concat([canonical_links, candidate_links], ignore_index=True),
        hypotheses,
    )

    baseline_row = baseline[baseline["Hypothesis_ID"] == hypothesis_id].iloc[0].copy()
    augmented_row = augmented[augmented["Hypothesis_ID"] == hypothesis_id].iloc[0].copy()
    baseline_row["Scenario"] = "canonical_baseline"
    augmented_row["Scenario"] = "with_s06_candidates"

    columns = [
        "Scenario",
        "Hypothesis_ID",
        "Directional_Link_Count",
        "Context_Link_Count",
        "Limitation_Link_Count",
        "Unique_Evidence_Count",
        "T_low",
        "T_high",
        "I_final_low",
        "I_final_high",
        "F_low",
        "F_high",
        "T_mid",
        "I_final_mid",
        "F_mid",
        "Net_mid",
    ]
    comparison = pd.DataFrame([baseline_row, augmented_row])[columns]

    deltas = comparison.set_index("Scenario")
    delta = deltas.loc["with_s06_candidates"][
        ["T_mid", "I_final_mid", "F_mid", "Net_mid"]
    ] - deltas.loc["canonical_baseline"][["T_mid", "I_final_mid", "F_mid", "Net_mid"]]
    delta_row = {column: "" for column in columns}
    delta_row.update(
        {
            "Scenario": "delta",
            "Hypothesis_ID": hypothesis_id,
            "T_mid": delta["T_mid"],
            "I_final_mid": delta["I_final_mid"],
            "F_mid": delta["F_mid"],
            "Net_mid": delta["Net_mid"],
        }
    )
    comparison = pd.concat([comparison, pd.DataFrame([delta_row])], ignore_index=True)
    return comparison, candidate_links


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a non-canonical S06 candidate-impact scenario for H20."
    )
    parser.add_argument(
        "--canonical-dir",
        type=Path,
        default=ROOT / "data" / "canonical",
    )
    parser.add_argument(
        "--candidate-links",
        type=Path,
        default=ROOT / "data" / "validation" / "v10_candidate_link_scoring.csv",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "tmp" / "v10_candidate_s06",
    )
    args = parser.parse_args()

    comparison, candidate_links = build_candidate_impact(
        args.canonical_dir,
        args.candidate_links,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    comparison.to_csv(args.output_dir / "h20_candidate_impact.csv", index=False)
    candidate_links.to_csv(args.output_dir / "candidate_links_computed.csv", index=False)
    print(comparison.to_string(index=False))


if __name__ == "__main__":
    main()
