from __future__ import annotations

from dataclasses import dataclass
from math import prod, sqrt
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

SCORE_PREFIXES = ("r", "m", "a", "d", "s", "o")
SCORE_COLUMNS = tuple(f"{key}_scores" for key in SCORE_PREFIXES)
REQUIRED_EXPERIMENTAL_COLUMNS = (
    "evidence_id",
    "bronze",
    "meta_family",
    "level",
    "dependency_DAG",
    *SCORE_COLUMNS,
    "role",
)


@dataclass(frozen=True)
class IVNState:
    t_low: float
    t_high: float
    i_low: float
    i_high: float
    f_low: float
    f_high: float

    @property
    def i_mid(self) -> float:
        return (self.i_low + self.i_high) / 2.0


def parse_panel_scores(value: object) -> np.ndarray:
    """Parse comma-separated Delphi scores in {0,1,2,3,4}."""

    if isinstance(value, str):
        parts = [p.strip() for p in value.split(",") if p.strip()]
        scores = np.array([float(p) for p in parts], dtype=float)
    else:
        scores = np.array(list(value), dtype=float)
    if scores.size < 2:
        raise ValueError("At least two panel scores are required.")
    if np.any(scores < 0) or np.any(scores > 4):
        raise ValueError("Panel scores must lie in [0, 4].")
    return scores


def validate_experimental_input(frame: pd.DataFrame) -> None:
    """Validate the CSV schema used by the optional V10 refinement pipeline."""

    missing = [column for column in REQUIRED_EXPERIMENTAL_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"Missing required experimental columns: {', '.join(missing)}")
    for column in SCORE_COLUMNS:
        for value in frame[column]:
            parse_panel_scores(value)


def delphi_interval(scores: Sequence[float] | str) -> tuple[float, float]:
    """Return [mu-sigma, mu+sigma] from normalized panel scores."""

    raw = parse_panel_scores(scores)
    normalized = raw / 4.0
    mu = float(normalized.mean())
    sigma = float(normalized.std(ddof=1))
    return max(0.0, mu - sigma), min(1.0, mu + sigma)


def delphi_intervals_from_row(row: Mapping[str, object]) -> dict[str, tuple[float, float]]:
    """Compute Delphi intervals for r/m/a/d/s/o score columns."""

    out: dict[str, tuple[float, float]] = {}
    for key in ("r", "m", "a", "d", "s", "o"):
        out[key.upper()] = delphi_interval(row[f"{key}_scores"])
    return out


def parse_dependency_dag_cell(evidence_id: str, value: object) -> list[tuple[str, str, float]]:
    """Parse incoming lineage edges stored in one CSV cell.

    Accepted cell forms are ``parent:beta; parent2:beta``, ``parent=beta``, or
    ``parent->child:beta``. In the first two forms the destination is the row's
    own evidence_id.
    """

    if value is None or (isinstance(value, float) and np.isnan(value)):
        return []
    text = str(value).strip()
    if not text:
        return []

    edges: list[tuple[str, str, float]] = []
    for item in text.split(";"):
        spec = item.strip()
        if not spec:
            continue
        if "->" in spec:
            left, right = spec.split("->", 1)
            if ":" in right:
                dst, beta_text = right.split(":", 1)
            elif "=" in right:
                dst, beta_text = right.split("=", 1)
            else:
                raise ValueError(f"Lineage edge lacks beta weight: {spec}")
            src = left.strip()
            dst = dst.strip()
        elif ":" in spec:
            src, beta_text = spec.split(":", 1)
            dst = evidence_id
        elif "=" in spec:
            src, beta_text = spec.split("=", 1)
            dst = evidence_id
        else:
            raise ValueError(f"Lineage edge lacks beta weight: {spec}")

        beta = float(beta_text.strip())
        if beta < 0.0 or beta > 1.0:
            raise ValueError("Lineage reuse weights beta must lie in [0, 1].")
        edges.append((src.strip(), dst.strip(), beta))
    return edges


def lineage_edges_from_frame(frame: pd.DataFrame) -> list[tuple[str, str, float]]:
    edges: list[tuple[str, str, float]] = []
    for row in frame.to_dict(orient="records"):
        edges.extend(parse_dependency_dag_cell(str(row["evidence_id"]), row.get("dependency_DAG")))
    return edges


def epistemic_novelty(
    evidence_id: str,
    lineage_edges: Iterable[tuple[str, str, float]],
) -> float:
    """Compute eta(e)=prod(1-beta) over incoming lineage edges."""

    incoming = [float(beta) for _, dst, beta in lineage_edges if dst == evidence_id]
    if not incoming:
        return 1.0
    if any(beta < 0.0 or beta > 1.0 for beta in incoming):
        raise ValueError("Lineage reuse weights beta must lie in [0, 1].")
    return prod(1.0 - beta for beta in incoming)


def apply_novelty_discount(q_low: float, q_high: float, eta: float) -> tuple[float, float]:
    if eta < 0.0 or eta > 1.0:
        raise ValueError("Novelty eta must lie in [0, 1].")
    return q_low * eta, q_high * eta


def quality_from_intervals(intervals: Mapping[str, tuple[float, float]]) -> tuple[float, float]:
    q_low = prod(intervals[key][0] for key in ("R", "M", "A", "D")) ** 0.25
    q_high = prod(intervals[key][1] for key in ("R", "M", "A", "D")) ** 0.25
    return q_low, q_high


def ivn_state_from_intervals(
    intervals: Mapping[str, tuple[float, float]],
    eta: float = 1.0,
) -> tuple[IVNState, tuple[float, float], tuple[float, float]]:
    """Compute discounted Q and the corresponding link-level IVN state."""

    q = quality_from_intervals(intervals)
    q_discounted = apply_novelty_discount(q[0], q[1], eta)
    s_low, s_high = intervals["S"]
    o_low, o_high = intervals["O"]
    t_low = q_discounted[0] * s_low
    t_high = q_discounted[1] * s_high
    f_low = q_discounted[0] * o_low
    f_high = q_discounted[1] * o_high
    i_low = 1.0 - q_discounted[1] * max(s_high, o_high)
    i_high = 1.0 - q_discounted[0] * max(s_low, o_low)
    return IVNState(t_low, t_high, i_low, i_high, f_low, f_high), q, q_discounted


def delphi_states_from_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert experimental score rows into Delphi intervals and IVN states."""

    validate_experimental_input(frame)
    edges = lineage_edges_from_frame(frame)
    rows: list[dict[str, object]] = []
    for row in frame.to_dict(orient="records"):
        evidence_id = str(row["evidence_id"])
        intervals = delphi_intervals_from_row(row)
        eta = epistemic_novelty(evidence_id, edges)
        state, q, q_discounted = ivn_state_from_intervals(intervals, eta=eta)
        record: dict[str, object] = {
            "evidence_id": evidence_id,
            "bronze": row["bronze"],
            "meta_family": row["meta_family"],
            "level": row["level"],
            "role": str(row["role"]).upper(),
            "eta": eta,
            "Q_low": q[0],
            "Q_high": q[1],
            "Q_discounted_low": q_discounted[0],
            "Q_discounted_high": q_discounted[1],
            "T_low": state.t_low,
            "T_high": state.t_high,
            "I_low": state.i_low,
            "I_high": state.i_high,
            "F_low": state.f_low,
            "F_high": state.f_high,
        }
        for key, (low, high) in intervals.items():
            record[f"{key}_low"] = low
            record[f"{key}_high"] = high
        rows.append(record)
    return pd.DataFrame(rows)


def ivn_entropy(state: IVNState) -> float:
    """Shannon-inspired IVN uncertainty proxy from interval width and I_mid."""

    width = ((state.t_high - state.t_low) + (state.i_high - state.i_low) + (state.f_high - state.f_low)) / 3.0
    return float(width + state.i_mid)


def entropy_weights(states: Mapping[str, IVNState]) -> dict[str, float]:
    """Normalize inverse IVN entropy, clipping negative certainty to zero."""

    certainty = {key: max(0.0, 1.0 - ivn_entropy(state)) for key, state in states.items()}
    total = sum(certainty.values())
    if total == 0.0:
        equal = 1.0 / len(certainty)
        return {key: equal for key in certainty}
    return {key: value / total for key, value in certainty.items()}


def weighted_mean_state(states: Sequence[IVNState], weights: Sequence[float] | None = None) -> IVNState:
    if not states:
        raise ValueError("At least one IVN state is required.")
    if weights is None:
        weights_array = np.ones(len(states), dtype=float) / len(states)
    else:
        weights_array = np.array(weights, dtype=float)
        if weights_array.size != len(states):
            raise ValueError("The number of weights must match the number of states.")
        total = float(weights_array.sum())
        if total <= 0.0:
            raise ValueError("Weights must have a positive total.")
        weights_array = weights_array / total
    matrix = np.array(
        [[s.t_low, s.t_high, s.i_low, s.i_high, s.f_low, s.f_high] for s in states],
        dtype=float,
    )
    values = weights_array @ matrix
    return IVNState(*[float(value) for value in values])


def state_from_record(row: Mapping[str, object]) -> IVNState:
    return IVNState(
        float(row["T_low"]),
        float(row["T_high"]),
        float(row["I_low"]),
        float(row["I_high"]),
        float(row["F_low"]),
        float(row["F_high"]),
    )


def aggregate_experimental_pipeline(
    frame: pd.DataFrame,
    group_by: str = "bronze",
    directional_only: bool = True,
) -> dict[str, pd.DataFrame]:
    """Run Delphi -> DAG discount -> entropy weighting -> IVN TOPSIS.

    The default aggregation uses only DIRECTIONAL rows for ranking. CONTEXT and
    LIMITATION rows are preserved in the evidence-level export so that the
    source-aware coding remains visible without silently turning context into
    support or falsity.
    """

    evidence = delphi_states_from_frame(frame)
    if group_by not in evidence.columns:
        raise ValueError(f"Unknown grouping column: {group_by}")

    working = evidence.copy()
    if directional_only:
        working = working[working["role"] == "DIRECTIONAL"].copy()
    if working.empty:
        raise ValueError("No rows are available for experimental aggregation.")

    meta_rows: list[dict[str, object]] = []
    for (group, meta_family), group_frame in working.groupby([group_by, "meta_family"], dropna=False):
        states = [state_from_record(row) for row in group_frame.to_dict(orient="records")]
        state = weighted_mean_state(states)
        meta_rows.append(
            {
                group_by: group,
                "meta_family": meta_family,
                "n_evidence": len(states),
                "T_low": state.t_low,
                "T_high": state.t_high,
                "I_low": state.i_low,
                "I_high": state.i_high,
                "F_low": state.f_low,
                "F_high": state.f_high,
                "entropy": ivn_entropy(state),
            }
        )
    meta_family_states = pd.DataFrame(meta_rows)

    weight_rows: list[dict[str, object]] = []
    final_states: dict[str, IVNState] = {}
    for group, group_frame in meta_family_states.groupby(group_by, dropna=False):
        states = {
            str(row["meta_family"]): state_from_record(row)
            for row in group_frame.to_dict(orient="records")
        }
        weights = entropy_weights(states)
        ordered_states = [states[key] for key in states]
        ordered_weights = [weights[key] for key in states]
        final_states[str(group)] = weighted_mean_state(ordered_states, ordered_weights)
        for key, weight in weights.items():
            weight_rows.append({group_by: group, "meta_family": key, "entropy_weight": weight})
    ranking = topsis_rank(final_states).rename(columns={"Hypothesis_ID": group_by})

    return {
        "evidence_states": evidence,
        "meta_family_states": meta_family_states,
        "entropy_weights": pd.DataFrame(weight_rows),
        "topsis_ranking": ranking,
    }


def ivn_distance(x: IVNState, y: IVNState) -> float:
    diffs = (
        x.t_low - y.t_low,
        x.t_high - y.t_high,
        x.i_low - y.i_low,
        x.i_high - y.i_high,
        x.f_low - y.f_low,
        x.f_high - y.f_high,
    )
    return sqrt(sum(d * d for d in diffs) / 6.0)


def topsis_rank(states: Mapping[str, IVNState]) -> pd.DataFrame:
    """Rank IVN states by relative closeness to the positive ideal."""

    positive = IVNState(1.0, 1.0, 0.0, 0.0, 0.0, 0.0)
    negative = IVNState(0.0, 0.0, 1.0, 1.0, 1.0, 1.0)
    rows = []
    for key, state in states.items():
        d_pos = ivn_distance(state, positive)
        d_neg = ivn_distance(state, negative)
        rc = d_neg / (d_pos + d_neg) if (d_pos + d_neg) else 0.0
        rows.append({"Hypothesis_ID": key, "d_positive": d_pos, "d_negative": d_neg, "RC": rc})
    return pd.DataFrame(rows).sort_values(["RC", "Hypothesis_ID"], ascending=[False, True]).reset_index(drop=True)


def perturb_panel_scores(
    scores: Sequence[float] | str,
    rng: np.random.Generator,
    sigma: float = 0.5,
) -> np.ndarray:
    raw = parse_panel_scores(scores)
    return np.clip(raw + rng.normal(0.0, sigma, size=raw.shape), 0.0, 4.0)


def monte_carlo_delphi_intervals(
    row: Mapping[str, object],
    iterations: int = 10_000,
    sigma: float = 0.5,
    seed: int | None = None,
) -> pd.DataFrame:
    """Perturb one row of Delphi scores and return interval samples."""

    rng = np.random.default_rng(seed)
    records = []
    for iteration in range(iterations):
        record: dict[str, float | int] = {"iteration": iteration}
        for key in ("r", "m", "a", "d", "s", "o"):
            low, high = delphi_interval(perturb_panel_scores(row[f"{key}_scores"], rng, sigma=sigma))
            record[f"{key}_low"] = low
            record[f"{key}_high"] = high
        records.append(record)
    return pd.DataFrame(records)


def perturb_score_frame(
    frame: pd.DataFrame,
    rng: np.random.Generator,
    sigma: float = 0.5,
) -> pd.DataFrame:
    perturbed = frame.copy()
    for column in SCORE_COLUMNS:
        perturbed[column] = [
            ",".join(f"{score:.6f}" for score in perturb_panel_scores(value, rng, sigma=sigma))
            for value in perturbed[column]
        ]
    return perturbed


def monte_carlo_experimental_pipeline(
    frame: pd.DataFrame,
    iterations: int = 10_000,
    sigma: float = 0.5,
    seed: int | None = None,
    group_by: str = "bronze",
) -> dict[str, pd.DataFrame]:
    """Monte Carlo robustness for the optional experimental pipeline."""

    rng = np.random.default_rng(seed)
    rc_records: list[dict[str, object]] = []
    for iteration in range(iterations):
        perturbed = perturb_score_frame(frame, rng, sigma=sigma)
        ranking = aggregate_experimental_pipeline(perturbed, group_by=group_by)["topsis_ranking"]
        for row in ranking.to_dict(orient="records"):
            rc_records.append(
                {
                    "iteration": iteration,
                    group_by: row[group_by],
                    "RC": row["RC"],
                    "rank": int(ranking.index[ranking[group_by] == row[group_by]][0]) + 1,
                }
            )
    rc_samples = pd.DataFrame(rc_records)

    comparison_rows: list[dict[str, object]] = []
    groups = sorted(str(value) for value in rc_samples[group_by].unique())
    pivot = rc_samples.pivot(index="iteration", columns=group_by, values="RC")
    for left in groups:
        for right in groups:
            if left == right:
                continue
            comparison_rows.append(
                {
                    "comparison": f"{left}>{right}",
                    "confidence": float((pivot[left] > pivot[right]).mean()),
                }
            )

    return {
        "rc_samples": rc_samples,
        "pairwise_confidence": pd.DataFrame(comparison_rows),
    }


def read_experimental_csv(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str).fillna("")
    validate_experimental_input(frame)
    return frame
