"""
Insights Generation Layer (satisfies BUILD-16, US-06 to US-14).
Generates evidence-based, caveated business interpretations from computed data.
"""
from typing import Dict, Any, List
import pandas as pd
from src.utils import format_inr


def generate_weekday_insight(weekday_df: pd.DataFrame) -> Dict[str, str]:
    """Generate evidence-backed weekday demand insight."""
    if weekday_df.empty:
        return {"finding": "Insufficient data to establish weekday patterns.", "evidence": "", "caveat": ""}

    sorted_df = weekday_df.sort_values("avg_daily_withdrawal", ascending=False)
    top_day = sorted_df.iloc[0]["day_of_week_name"]
    top_val = sorted_df.iloc[0]["avg_daily_withdrawal"]
    low_day = sorted_df.iloc[-1]["day_of_week_name"]
    low_val = sorted_df.iloc[-1]["avg_daily_withdrawal"]

    finding = f"Peak demand occurs on {top_day}s, while {low_day}s exhibit the lowest average withdrawal volume."
    evidence = f"{top_day} average is {format_inr(top_val)}, compared with {format_inr(low_val)} on {low_day}."
    caveat = "Patterns reflect the synthetic dataset's embedded weekly seasonality and may differ in live operations."
    return {"finding": finding, "evidence": evidence, "caveat": caveat}


def generate_ranking_insight(ranked_df: pd.DataFrame) -> Dict[str, str]:
    """Generate ATM concentration insight."""
    if ranked_df.empty:
        return {"finding": "No ATM usage data available.", "evidence": "", "caveat": ""}

    top_atm = ranked_df.iloc[0]
    total_net = ranked_df["total_withdrawn"].sum()
    top_pct = (top_atm["total_withdrawn"] / total_net * 100) if total_net > 0 else 0

    finding = f"Top-performing ATM is {top_atm.get('atm_name', top_atm['atm_id'])} ({top_atm.get('site_type', 'N/A')})."
    evidence = f"Accounts for {top_pct:.1f}% ({format_inr(top_atm['total_withdrawn'])}) of total demand in selected scope."
    caveat = "Ranking is evaluated over the filtered time window; newly deployed machines may have fewer observations."
    return {"finding": finding, "evidence": evidence, "caveat": caveat}


def generate_replenishment_insight(replenishment_summary: Dict[str, Any]) -> Dict[str, str]:
    """Generate replenishment vs withdrawal alignment insight."""
    withdrawn = replenishment_summary.get("total_withdrawn", 0.0)
    replenished = replenishment_summary.get("total_replenished", 0.0)
    ratio = replenishment_summary.get("replenishment_ratio_pct", 0.0)

    if withdrawn == 0:
        return {"finding": "No withdrawal activity recorded in selected window.", "evidence": "", "caveat": ""}

    if ratio > 105:
        finding = "Cash replenishment exceeds withdrawal volume, indicating potential inventory build-up."
    elif ratio < 95:
        finding = "Cash replenishment is lower than withdrawal volume, indicating net cash drain."
    else:
        finding = "Cash loading is broadly in equilibrium with historical cash withdrawals."

    evidence = f"Replenished: {format_inr(replenished)} vs Withdrawn: {format_inr(withdrawn)} (Ratio: {ratio:.1f}%)."
    caveat = "Directional indicator only; exact cash levels require opening/closing balance and transit timing reconciliations."
    return {"finding": finding, "evidence": evidence, "caveat": caveat}
