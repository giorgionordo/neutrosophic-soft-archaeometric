from __future__ import annotations

from dataclasses import dataclass
from math import prod
from typing import Mapping


@dataclass(frozen=True)
class Interval:
    low: float
    high: float

    @property
    def mid(self) -> float:
        return (self.low + self.high) / 2.0


def _f(row: Mapping[str, object], key: str) -> float:
    value = row[key]
    if value == "" or value is None:
        return 0.0
    return float(value)


def quality_interval(row: Mapping[str, object]) -> Interval:
    """Compute Q=[(R*M*A*D)^(1/4)] from a link row."""

    q_low = prod(_f(row, k) for k in ("R_low", "M_low", "A_low", "D_low")) ** 0.25
    q_high = prod(_f(row, k) for k in ("R_high", "M_high", "A_high", "D_high")) ** 0.25
    return Interval(q_low, q_high)


def compute_link_state(row: Mapping[str, object]) -> dict[str, float]:
    """Compute link-level Q, T, I, F and contradiction C.

    DIRECTIONAL links contribute support/opposition. LIMITATION and CONTEXT
    links may carry stored Lambda or audit information, but their T/F state is
    still computed from the explicit S/O columns for formula validation.
    """

    q = quality_interval(row)
    s_low, s_high = _f(row, "S_low"), _f(row, "S_high")
    o_low, o_high = _f(row, "O_low"), _f(row, "O_high")

    t_low = q.low * s_low
    t_high = q.high * s_high
    f_low = q.low * o_low
    f_high = q.high * o_high
    i_low = 1.0 - q.high * max(s_high, o_high)
    i_high = 1.0 - q.low * max(s_low, o_low)
    c_low = min(t_low, f_low)
    c_high = min(t_high, f_high)

    return {
        "Q_low": q.low,
        "Q_high": q.high,
        "T_low": t_low,
        "T_high": t_high,
        "I_low": i_low,
        "I_high": i_high,
        "F_low": f_low,
        "F_high": f_high,
        "C_low": c_low,
        "C_high": c_high,
    }
