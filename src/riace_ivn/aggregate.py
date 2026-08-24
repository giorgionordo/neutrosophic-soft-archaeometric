from __future__ import annotations

from math import prod

import numpy as np
import pandas as pd


def _as_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _weighted_conorm(values: pd.Series, weights: pd.Series) -> float:
    values = _as_float(values).clip(lower=0.0, upper=1.0)
    weights = _as_float(weights)
    total = float(weights.sum())
    if total <= 0:
        return 0.0
    weights = weights / total
    return 1.0 - float(np.prod(np.power(1.0 - values, weights)))


def _weighted_geom(values: pd.Series, weights: pd.Series) -> float:
    values = _as_float(values).clip(lower=0.0, upper=1.0)
    weights = _as_float(weights)
    total = float(weights.sum())
    if total <= 0:
        return 1.0
    weights = weights / total
    return float(np.prod(np.power(values, weights)))


def _plain_conorm(values: pd.Series) -> float:
    values = _as_float(values).clip(lower=0.0, upper=1.0)
    if values.empty:
        return 0.0
    return 1.0 - float(np.prod(1.0 - values))


def _plain_geom(values: pd.Series) -> float:
    values = _as_float(values).clip(lower=0.0, upper=1.0)
    if values.empty:
        return 1.0
    return float(np.prod(values))


def _group_directional(group: pd.DataFrame) -> dict[str, object]:
    weights = (_as_float(group["Q_low"]) + _as_float(group["Q_high"])) / 2.0
    return {
        "Hypothesis_ID": group["Hypothesis_ID"].iloc[0],
        "Evidence_Family": group["Evidence_Family"].iloc[0],
        "Revised_Dependency_Group": group["Revised_Dependency_Group"].iloc[0],
        "T_low": _weighted_conorm(group["T_low"], weights),
        "T_high": _weighted_conorm(group["T_high"], weights),
        "I_dir_low": _weighted_geom(group["I_low"], weights),
        "I_dir_high": _weighted_geom(group["I_high"], weights),
        "F_low": _weighted_conorm(group["F_low"], weights),
        "F_high": _weighted_conorm(group["F_high"], weights),
        "Link_Count": len(group),
    }


def _group_limitation(group: pd.DataFrame) -> dict[str, object]:
    weights = (_as_float(group["Q_low"]) + _as_float(group["Q_high"])) / 2.0
    return {
        "Hypothesis_ID": group["Hypothesis_ID"].iloc[0],
        "Evidence_Family": group["Evidence_Family"].iloc[0],
        "Revised_Dependency_Group": group["Revised_Dependency_Group"].iloc[0],
        "Lambda_low": _weighted_conorm(group["Lambda_low"], weights),
        "Lambda_high": _weighted_conorm(group["Lambda_high"], weights),
        "Link_Count": len(group),
    }


def aggregate_v7_results(links: pd.DataFrame, hypotheses: pd.DataFrame) -> pd.DataFrame:
    """Reproduce V7 role-aware dependency/family/hypothesis aggregation."""

    records: list[dict[str, object]] = []
    active_hypotheses = sorted(str(h) for h in links["Hypothesis_ID"].dropna().unique())
    hyp = hypotheses.set_index("Hypothesis_ID")

    directional = links[links["Role"] == "DIRECTIONAL"].copy()
    limitation = links[links["Role"] == "LIMITATION"].copy()

    group_keys = ["Hypothesis_ID", "Evidence_Family", "Revised_Dependency_Group"]
    dir_groups = (
        pd.DataFrame([_group_directional(g) for _, g in directional.groupby(group_keys)])
        if not directional.empty
        else pd.DataFrame()
    )
    lim_groups = (
        pd.DataFrame([_group_limitation(g) for _, g in limitation.groupby(group_keys)])
        if not limitation.empty
        else pd.DataFrame()
    )

    for hid in active_hypotheses:
        hlinks = links[links["Hypothesis_ID"] == hid]
        hdir = dir_groups[dir_groups["Hypothesis_ID"] == hid] if not dir_groups.empty else pd.DataFrame()
        hlim = lim_groups[lim_groups["Hypothesis_ID"] == hid] if not lim_groups.empty else pd.DataFrame()

        if hdir.empty:
            t_low = t_high = f_low = f_high = 0.0
            i_low = i_high = 1.0
        else:
            families = []
            for family, fg in hdir.groupby("Evidence_Family"):
                families.append(
                    {
                        "Evidence_Family": family,
                        "T_low": float(fg["T_low"].max()),
                        "T_high": float(fg["T_high"].max()),
                        "I_dir_low": float(fg["I_dir_low"].min()),
                        "I_dir_high": float(fg["I_dir_high"].min()),
                        "F_low": float(fg["F_low"].max()),
                        "F_high": float(fg["F_high"].max()),
                    }
                )
            fam = pd.DataFrame(families)
            t_low = _plain_conorm(fam["T_low"])
            t_high = _plain_conorm(fam["T_high"])
            i_low = _plain_geom(fam["I_dir_low"])
            i_high = _plain_geom(fam["I_dir_high"])
            f_low = _plain_conorm(fam["F_low"])
            f_high = _plain_conorm(fam["F_high"])

        if hlim.empty:
            lam_low = lam_high = 0.0
        else:
            lim_fam = hlim.groupby("Evidence_Family", as_index=False).agg(
                Lambda_low=("Lambda_low", "max"),
                Lambda_high=("Lambda_high", "max"),
            )
            lam_low = _plain_conorm(lim_fam["Lambda_low"])
            lam_high = _plain_conorm(lim_fam["Lambda_high"])

        i_final_low = 1.0 - (1.0 - i_low) * (1.0 - lam_low)
        i_final_high = 1.0 - (1.0 - i_high) * (1.0 - lam_high)
        c_low = min(t_low, f_low)
        c_high = min(t_high, f_high)

        hrow = hyp.loc[hid] if hid in hyp.index else {}
        records.append(
            {
                "Hypothesis_ID": hid,
                "Hypothesis": hrow.get("Hypothesis", ""),
                "Tier": hrow.get("Tier", ""),
                "Domain": hrow.get("Domain", ""),
                "Directional_Link_Count": int((hlinks["Role"] == "DIRECTIONAL").sum()),
                "Context_Link_Count": int((hlinks["Role"] == "CONTEXT").sum()),
                "Limitation_Link_Count": int((hlinks["Role"] == "LIMITATION").sum()),
                "Unique_Evidence_Count": int(hlinks["Evidence_ID"].nunique()),
                "T_low": t_low,
                "T_high": t_high,
                "I_dir_low": i_low,
                "I_dir_high": i_high,
                "Lambda_low": lam_low,
                "Lambda_high": lam_high,
                "I_final_low": i_final_low,
                "I_final_high": i_final_high,
                "F_low": f_low,
                "F_high": f_high,
                "C_low": c_low,
                "C_high": c_high,
                "T_mid": (t_low + t_high) / 2.0,
                "I_final_mid": (i_final_low + i_final_high) / 2.0,
                "F_mid": (f_low + f_high) / 2.0,
                "Net_mid": ((t_low + t_high) - (f_low + f_high)) / 2.0,
            }
        )

    return pd.DataFrame(records)


def aggregate_v9_synthesis(meta_components: pd.DataFrame, meta_families: pd.DataFrame) -> pd.DataFrame:
    """Reproduce V9 H21/H33 second-order synthesis from meta-components."""

    out = []
    fam = meta_families.set_index("Family")
    for target in ("H21", "H33"):
        family_rows = []
        for family, group in meta_components.groupby("Family"):
            prefix = f"{target}_"
            family_rows.append(
                {
                    "Family": family,
                    "Weight": float(fam.loc[family, f"{target}_Weight"]),
                    "T_low": float(group[f"{prefix}T_low"].max()),
                    "T_high": float(group[f"{prefix}T_high"].max()),
                    "I_low": float(group[f"{prefix}I_low"].min()),
                    "I_high": float(group[f"{prefix}I_high"].min()),
                    "F_low": float(group[f"{prefix}F_low"].max()),
                    "F_high": float(group[f"{prefix}F_high"].max()),
                    "Lambda_low": float(group[f"{prefix}Lambda_low"].max()),
                    "Lambda_high": float(group[f"{prefix}Lambda_high"].max()),
                }
            )
        fdf = pd.DataFrame(family_rows)
        fdf["I_final_low"] = 1.0 - (1.0 - fdf["I_low"]) * (1.0 - fdf["Lambda_low"])
        fdf["I_final_high"] = 1.0 - (1.0 - fdf["I_high"]) * (1.0 - fdf["Lambda_high"])
        weights = fdf["Weight"]
        t_low = _weighted_conorm(fdf["T_low"], weights)
        t_high = _weighted_conorm(fdf["T_high"], weights)
        i_low = _weighted_geom(fdf["I_final_low"], weights)
        i_high = _weighted_geom(fdf["I_final_high"], weights)
        f_low = _weighted_conorm(fdf["F_low"], weights)
        f_high = _weighted_conorm(fdf["F_high"], weights)
        out.append(
            {
                "Hypothesis_ID": target,
                "T_low": t_low,
                "T_high": t_high,
                "I_low": i_low,
                "I_high": i_high,
                "F_low": f_low,
                "F_high": f_high,
                "C_low": min(t_low, f_low),
                "C_high": min(t_high, f_high),
                "T_mid": (t_low + t_high) / 2.0,
                "I_mid": (i_low + i_high) / 2.0,
                "F_mid": (f_low + f_high) / 2.0,
                "Net_mid": ((t_low + t_high) - (f_low + f_high)) / 2.0,
            }
        )
    return pd.DataFrame(out)
