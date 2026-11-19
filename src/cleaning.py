"""
Data Cleaning & Governance Pipeline (satisfies BUILD-03, US-01, US-13).
Deterministic, auditable cleaning preserving source provenance and reporting all transformations.
"""
from typing import Tuple, Dict, Any, List
import pandas as pd
import numpy as np


def clean_daily_facts(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Cleans daily facts DataFrame deterministically:
    1. Checks for and removes exact composite key duplicates (atm_id, date_key).
    2. Validates non-negative constraints (withdrawal_amount_inr >= 0).
    3. Preserves NULL replenishment amounts as None / NaN (never coerced to 0).
    4. Reports audit summary of actions taken.
    """
    if df.empty:
        return df, {"rows_in": 0, "rows_out": 0, "duplicates_removed": 0, "negatives_clipped": 0}

    df_cleaned = df.copy()
    rows_initial = len(df_cleaned)

    # 1. Deduplication by composite grain (atm_id, date_key)
    dup_mask = df_cleaned.duplicated(subset=["atm_id", "date_key"], keep="first")
    duplicates_count = int(dup_mask.sum())
    if duplicates_count > 0:
        df_cleaned = df_cleaned[~dup_mask].copy()

    # 2. Non-negative validation on withdrawal amount
    neg_mask = df_cleaned["withdrawal_amount_inr"] < 0
    negatives_count = int(neg_mask.sum())
    if negatives_count > 0:
        df_cleaned.loc[neg_mask, "withdrawal_amount_inr"] = 0.0

    # 3. Replenishment non-negative validation (when present)
    rep_neg_mask = (df_cleaned["replenished_amount_inr"].notna()) & (df_cleaned["replenished_amount_inr"] < 0)
    rep_neg_count = int(rep_neg_mask.sum())
    if rep_neg_count > 0:
        df_cleaned.loc[rep_neg_mask, "replenished_amount_inr"] = 0.0

    # 4. Compile audit log
    audit_report = {
        "rows_in": rows_initial,
        "rows_out": len(df_cleaned),
        "duplicates_removed": duplicates_count,
        "negative_withdrawals_handled": negatives_count,
        "negative_replenishments_handled": rep_neg_count,
        "null_replenishments_preserved": int(df_cleaned["replenished_amount_inr"].isna().sum())
    }

    return df_cleaned, audit_report
