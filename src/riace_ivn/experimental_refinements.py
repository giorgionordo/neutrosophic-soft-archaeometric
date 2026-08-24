from __future__ import annotations

from dataclasses import dataclass
from math import prod, sqrt
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


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
