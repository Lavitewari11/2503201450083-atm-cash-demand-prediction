"""
Core Analytics & Statistical Analysis Module.
Satisfies BR-01 to BR-05, BR-08, BR-09 (OQ-01 to OQ-05, OQ-08, OQ-09).
"""
from typing import Optional, Dict, Any, List, Union
from datetime import date
import numpy as np
import pandas as pd

from src.utils import safe_divide

WEEKDAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]
SEASON_ORDER = ["Summer", "Monsoon", "Winter", "Other"]


def get_historical_summary(df: pd.DataFrame, calendar_days: Optional[int] = None) -> Dict[str, Any]:
    """
    Computes total and average historical metrics (BR-01, BR-02).
    """
    if df.empty:
        return {
            "total_withdrawn": 0.0,
            "observed_days": 0,
            "calendar_days": calendar_days or 0,
            "avg_daily_observed": 0.0,
            "avg_daily_calendar": 0.0,
            "min_daily": 0.0,
            "median_daily": 0.0,
            "max_daily": 0.0,
            "std_daily": 0.0,
            "total_transactions": 0,
            "total_replenished": 0.0
        }

    total_withdrawn = float(df["withdrawal_amount_inr"].sum())
    observed_days = len(df)
    c_days = calendar_days if calendar_days and calendar_days >= observed_days else observed_days

    avg_observed = total_withdrawn / observed_days if observed_days > 0 else 0.0
    avg_calendar = total_withdrawn / c_days if c_days > 0 else 0.0

    tx_series = df["transaction_count"].dropna()
    total_tx = int(tx_series.sum()) if not tx_series.empty else 0

    rep_series = df["replenished_amount_inr"].dropna()
    total_rep = float(rep_series.sum()) if not rep_series.empty else 0.0

    return {
        "total_withdrawn": total_withdrawn,
        "observed_days": observed_days,
        "calendar_days": c_days,
        "avg_daily_observed": avg_observed,
        "avg_daily_calendar": avg_calendar,
        "min_daily": float(df["withdrawal_amount_inr"].min()),
        "median_daily": float(df["withdrawal_amount_inr"].median()),
        "max_daily": float(df["withdrawal_amount_inr"].max()),
        "std_daily": float(df["withdrawal_amount_inr"].std(ddof=1)) if observed_days > 1 else 0.0,
        "total_transactions": total_tx,
        "total_replenished": total_rep
    }


def get_weekday_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate demand by day of week across all 7 days (BR-03, OQ-03).
    Ensures all 7 weekdays are represented and totals reconcile to source.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "day_of_week_name", "day_of_week_num", "total_withdrawn",
            "avg_daily_withdrawal", "observation_count", "pct_of_total"
        ])

    grouped = df.groupby(["day_of_week_num", "day_of_week_name"]).agg(
        total_withdrawn=("withdrawal_amount_inr", "sum"),
        avg_daily_withdrawal=("withdrawal_amount_inr", "mean"),
        observation_count=("withdrawal_amount_inr", "count"),
        total_tx=("transaction_count", "sum")
    ).reset_index()

    # Reindex to ensure all 7 days appear in proper Monday-Sunday order
    lookup = {row["day_of_week_name"]: row for _, row in grouped.iterrows()}
    rows = []
    total_all = df["withdrawal_amount_inr"].sum()

    for idx, day_name in enumerate(WEEKDAY_ORDER, 1):
        if day_name in lookup:
            r = lookup[day_name]
            tot = float(r["total_withdrawn"])
            avg = float(r["avg_daily_withdrawal"])
            cnt = int(r["observation_count"])
            tx = int(r["total_tx"]) if pd.notna(r["total_tx"]) else 0
        else:
            tot, avg, cnt, tx = 0.0, 0.0, 0, 0

        pct = (tot / total_all * 100) if total_all > 0 else 0.0
        rows.append({
            "day_of_week_num": idx,
            "day_of_week_name": day_name,
            "total_withdrawn": round(tot, 2),
            "avg_daily_withdrawal": round(avg, 2),
            "observation_count": cnt,
            "total_transactions": tx,
            "pct_of_total": round(pct, 2)
        })

    result_df = pd.DataFrame(rows)
    return result_df


def get_monthly_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate demand by calendar month (BR-04, OQ-04).
    """
    if df.empty:
        return pd.DataFrame()

    grouped = df.groupby(["month_num", "month_name"]).agg(
        total_withdrawn=("withdrawal_amount_inr", "sum"),
        avg_daily_withdrawal=("withdrawal_amount_inr", "mean"),
        observation_count=("withdrawal_amount_inr", "count")
    ).reset_index().sort_values("month_num")

    total_all = df["withdrawal_amount_inr"].sum()
    grouped["pct_of_total"] = (grouped["total_withdrawn"] / total_all * 100).round(2)
    return grouped


def get_seasonal_distribution(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate demand by configured season: Summer, Monsoon, Winter, Other (BR-04, OQ-04).
    """
    if df.empty:
        return pd.DataFrame()

    df_clean = df.copy()
    df_clean["season_name"] = df_clean["season_name"].fillna("Other")

    grouped = df_clean.groupby("season_name").agg(
        total_withdrawn=("withdrawal_amount_inr", "sum"),
        avg_daily_withdrawal=("withdrawal_amount_inr", "mean"),
        observation_count=("withdrawal_amount_inr", "count")
    ).reset_index()

    # Reorder by standard season order
    grouped["sort_idx"] = grouped["season_name"].map(lambda x: SEASON_ORDER.index(x) if x in SEASON_ORDER else 99)
    grouped = grouped.sort_values("sort_idx").drop(columns=["sort_idx"])

    total_all = df["withdrawal_amount_inr"].sum()
    grouped["pct_of_total"] = (grouped["total_withdrawn"] / total_all * 100).round(2)
    return grouped


def get_atm_rankings(
    df: pd.DataFrame,
    df_atms: Optional[pd.DataFrame] = None,
    sort_by: str = "total_withdrawn",
    ascending: bool = False
) -> pd.DataFrame:
    """
    Rank ATMs by historical cash usage (BR-05, OQ-05).
    Sort by 'total_withdrawn' or 'avg_daily_withdrawal'.
    """
    if df.empty:
        return pd.DataFrame()

    agg_df = df.groupby("atm_id").agg(
        total_withdrawn=("withdrawal_amount_inr", "sum"),
        avg_daily_withdrawal=("withdrawal_amount_inr", "mean"),
        min_daily=("withdrawal_amount_inr", "min"),
        max_daily=("withdrawal_amount_inr", "max"),
        observation_count=("withdrawal_amount_inr", "count"),
        total_replenished=("replenished_amount_inr", "sum"),
        total_transactions=("transaction_count", "sum")
    ).reset_index()

    if df_atms is not None and not df_atms.empty:
        agg_df = agg_df.merge(
            df_atms[["atm_id", "atm_name", "area_name", "site_type", "is_active"]],
            on="atm_id",
            how="left"
        )

    if sort_by not in agg_df.columns:
        sort_by = "total_withdrawn"

    agg_df = agg_df.sort_values(sort_by, ascending=ascending).reset_index(drop=True)
    agg_df["rank"] = agg_df.index + 1
    return agg_df


def detect_demand_anomalies(
    df: pd.DataFrame,
    method: str = "zscore",
    threshold: float = 2.0,
    scope: str = "network"
) -> pd.DataFrame:
    """
    Identifies unusually high or low demand ATM-days (BR-08, OQ-08, BRULE-10).
    Methods supported: 'zscore' or 'iqr'.
    Scope supported: 'network' (across all ATMs, recommended for N=250) or 'atm' (within each ATM).
    Flags records as candidate exceptions for investigation.
    """
    if df.empty:
        return pd.DataFrame()

    df_out = df.copy()
    anomalies = []

    if scope == "network":
        withdrawals = df_out["withdrawal_amount_inr"].values
        mean_val = float(np.mean(withdrawals))
        std_val = float(np.std(withdrawals, ddof=1)) if len(withdrawals) > 1 else 0.0

        if method == "zscore":
            if std_val > 0:
                for idx, row in df_out.iterrows():
                    val = float(row["withdrawal_amount_inr"])
                    z = (val - mean_val) / std_val
                    if abs(z) >= threshold:
                        direction = "Unusually High Demand" if z > 0 else "Unusually Low Demand"
                        anomalies.append({
                            "atm_id": row["atm_id"],
                            "atm_name": row.get("atm_name", ""),
                            "date_value": row["date_value"],
                            "day_of_week_name": row.get("day_of_week_name", ""),
                            "observed_withdrawal_inr": round(val, 2),
                            "baseline_mean_inr": round(mean_val, 2),
                            "baseline_std_inr": round(std_val, 2),
                            "score": round(z, 2),
                            "threshold_used": f"Network |Z| >= {threshold}",
                            "anomaly_type": direction,
                            "note": "Analytical exception candidate; investigate operational context."
                        })
        elif method == "iqr":
            q1 = float(np.percentile(withdrawals, 25))
            q3 = float(np.percentile(withdrawals, 75))
            iqr = q3 - q1
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr

            for idx, row in df_out.iterrows():
                val = float(row["withdrawal_amount_inr"])
                if val > upper_bound or val < lower_bound:
                    direction = "Unusually High Demand" if val > upper_bound else "Unusually Low Demand"
                    anomalies.append({
                        "atm_id": row["atm_id"],
                        "atm_name": row.get("atm_name", ""),
                        "date_value": row["date_value"],
                        "day_of_week_name": row.get("day_of_week_name", ""),
                        "observed_withdrawal_inr": round(val, 2),
                        "baseline_mean_inr": round(mean_val, 2),
                        "baseline_std_inr": round(std_val, 2),
                        "score": round(val - mean_val, 2),
                        "threshold_used": f"Network IQR multiplier = {threshold}",
                        "anomaly_type": direction,
                        "note": "Analytical exception candidate; investigate operational context."
                    })
    else:
        # Detect per ATM
        for atm_id, group in df_out.groupby("atm_id"):
            n = len(group)
            if n < 3:
                continue

            withdrawals = group["withdrawal_amount_inr"].values
            mean_val = float(np.mean(withdrawals))
            std_val = float(np.std(withdrawals, ddof=1)) if n > 1 else 0.0

            # Adjust threshold for small sample size if default was 2.0
            eff_thresh = min(threshold, 1.5) if n < 10 and threshold >= 2.0 else threshold

            if method == "zscore":
                if std_val > 0:
                    for idx, row in group.iterrows():
                        val = float(row["withdrawal_amount_inr"])
                        z = (val - mean_val) / std_val
                        if abs(z) >= eff_thresh:
                            direction = "Unusually High Demand" if z > 0 else "Unusually Low Demand"
                            anomalies.append({
                                "atm_id": row["atm_id"],
                                "atm_name": row.get("atm_name", ""),
                                "date_value": row["date_value"],
                                "day_of_week_name": row.get("day_of_week_name", ""),
                                "observed_withdrawal_inr": round(val, 2),
                                "baseline_mean_inr": round(mean_val, 2),
                                "baseline_std_inr": round(std_val, 2),
                                "score": round(z, 2),
                                "threshold_used": f"ATM-level |Z| >= {eff_thresh}",
                                "anomaly_type": direction,
                                "note": "Analytical exception candidate; investigate operational context."
                            })
            elif method == "iqr":
                q1 = float(np.percentile(withdrawals, 25))
                q3 = float(np.percentile(withdrawals, 75))
                iqr = q3 - q1
                lower_bound = q1 - eff_thresh * iqr
                upper_bound = q3 + eff_thresh * iqr

                for idx, row in group.iterrows():
                    val = float(row["withdrawal_amount_inr"])
                    if val > upper_bound or val < lower_bound:
                        direction = "Unusually High Demand" if val > upper_bound else "Unusually Low Demand"
                        anomalies.append({
                            "atm_id": row["atm_id"],
                            "atm_name": row.get("atm_name", ""),
                            "date_value": row["date_value"],
                            "day_of_week_name": row.get("day_of_week_name", ""),
                            "observed_withdrawal_inr": round(val, 2),
                            "baseline_mean_inr": round(mean_val, 2),
                            "baseline_std_inr": round(std_val, 2),
                            "score": round(val - mean_val, 2),
                            "threshold_used": f"ATM-level IQR multiplier = {eff_thresh}",
                            "anomaly_type": direction,
                            "note": "Analytical exception candidate; investigate operational context."
                        })

    return pd.DataFrame(anomalies)


def compare_replenishment_vs_withdrawal(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare cash replenished with cash withdrawn (BR-09, OQ-09, BRULE-11).
    """
    if df.empty:
        return {
            "total_withdrawn": 0.0,
            "total_replenished": 0.0,
            "net_difference": 0.0,
            "replenishment_ratio_pct": 0.0,
            "daily_comparison_df": pd.DataFrame()
        }

    valid_df = df.dropna(subset=["replenished_amount_inr"]).copy()
    tot_withdrawn = float(valid_df["withdrawal_amount_inr"].sum())
    tot_replenished = float(valid_df["replenished_amount_inr"].sum())
    net_diff = tot_replenished - tot_withdrawn
    ratio = (tot_replenished / tot_withdrawn * 100) if tot_withdrawn > 0 else 0.0

    daily = valid_df[[
        "atm_id", "date_value", "day_of_week_name",
        "withdrawal_amount_inr", "replenished_amount_inr",
        "opening_balance_inr", "closing_balance_inr"
    ]].copy()
    daily["net_daily_flow"] = daily["replenished_amount_inr"] - daily["withdrawal_amount_inr"]

    return {
        "total_withdrawn": tot_withdrawn,
        "total_replenished": tot_replenished,
        "net_difference": net_diff,
        "replenishment_ratio_pct": round(ratio, 2),
        "daily_comparison_df": daily
    }
