"""
Data Quality & Completeness Audit Module (satisfies BR-11).
Audits missing values, duplicates, foreign keys, schema constraints, and quarantined records.
"""
from pathlib import Path
import sqlite3
from typing import Dict, Any, List
import pandas as pd

from src.database import get_connection, DATA_DIR


def audit_row_counts(con: sqlite3.Connection) -> pd.DataFrame:
    """Audit table row counts against design targets."""
    targets = {
        "atm_master": (50, "Master entity of ~50 ATMs"),
        "date_dim": (730, "2-year daily calendar (2024-2025)"),
        "atm_daily_fact": (250, "Sampled daily withdrawal/replenishment facts"),
        "atm_forecast_fact": (75, "Benchmark baseline forecasts (15 dates x 5 ATMs)")
    }
    rows = []
    for tbl, (expected, desc) in targets.items():
        actual = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
        status = "PASS" if actual >= expected else "WARNING"
        rows.append({
            "Table": tbl,
            "Actual Rows": actual,
            "Target / Expected": expected,
            "Status": status,
            "Description": desc
        })
    return pd.DataFrame(rows)


def audit_foreign_keys(con: sqlite3.Connection) -> Dict[str, Any]:
    """Execute PRAGMA foreign_key_check to verify relational integrity."""
    violations = con.execute("PRAGMA foreign_key_check").fetchall()
    passed = len(violations) == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "violations_count": len(violations),
        "details": violations,
        "message": "All foreign key constraints are strictly satisfied." if passed else f"Found {len(violations)} FK violations."
    }


def audit_missing_values(con: sqlite3.Connection) -> pd.DataFrame:
    """Analyze null / missing values across all base tables."""
    tables = ["atm_master", "date_dim", "atm_daily_fact", "atm_forecast_fact"]
    results = []
    for tbl in tables:
        df = pd.read_sql_query(f"SELECT * FROM {tbl}", con)
        total_rows = len(df)
        for col in df.columns:
            null_count = df[col].isna().sum()
            null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0
            results.append({
                "Table": tbl,
                "Column": col,
                "Total Rows": total_rows,
                "Null Count": int(null_count),
                "Null Pct (%)": round(null_pct, 2),
                "Is Nullable": "Yes" if col in [
                    "install_date", "season_name", "is_holiday",
                    "replenished_amount_inr", "transaction_count",
                    "opening_balance_inr", "closing_balance_inr",
                    "source_batch_id", "training_start_key", "training_end_key", "evaluation_split"
                ] else "No"
            })
    return pd.DataFrame(results)


def audit_range_and_business_rules(con: sqlite3.Connection) -> pd.DataFrame:
    """Verify range, sign, domain, and consistency business rules."""
    checks = [
        (
            "BRULE-01: Withdrawal Non-Negative",
            "SELECT COUNT(*) FROM atm_daily_fact WHERE withdrawal_amount_inr < 0",
            0,
            "Withdrawals must be >= 0 INR"
        ),
        (
            "Replenishment Non-Negative",
            "SELECT COUNT(*) FROM atm_daily_fact WHERE replenished_amount_inr < 0",
            0,
            "Replenished amounts must be >= 0 INR when present"
        ),
        (
            "BRULE-02: ATM Foreign Key Validity",
            "SELECT COUNT(*) FROM atm_daily_fact WHERE atm_id NOT IN (SELECT atm_id FROM atm_master)",
            0,
            "Every daily fact must link to a valid registered ATM"
        ),
        (
            "Allowed ATM Site Types",
            "SELECT COUNT(*) FROM atm_master WHERE site_type NOT IN ('Branch','Market','Transit','Residential','Office')",
            0,
            "Site types must belong to allowed categories"
        ),
        (
            "Date Key Alignment",
            "SELECT COUNT(*) FROM date_dim WHERE date_key != CAST(REPLACE(date_value,'-','') AS INTEGER)",
            0,
            "date_key must equal integer YYYYMMDD of date_value"
        ),
        (
            "Calendar Day of Week Alignment",
            "SELECT COUNT(*) FROM date_dim WHERE day_of_week_num NOT BETWEEN 1 AND 7",
            0,
            "day_of_week_num must be between 1 (Monday) and 7 (Sunday)"
        ),
        (
            "Forecast Non-Negative",
            "SELECT COUNT(*) FROM atm_forecast_fact WHERE predicted_withdrawal_inr < 0",
            0,
            "Predicted withdrawal amounts must be >= 0 INR"
        ),
        (
            "Primary Grain Uniqueness (atm_id, date_key)",
            "SELECT COUNT(*) FROM (SELECT atm_id, date_key, COUNT(*) c FROM atm_daily_fact GROUP BY atm_id, date_key HAVING c > 1)",
            0,
            "No duplicate daily records for the same ATM on the same date"
        )
    ]

    rows = []
    for rule_name, query, expected, desc in checks:
        actual = con.execute(query).fetchone()[0]
        status = "PASS" if actual == expected else "FAIL"
        rows.append({
            "Check Name": rule_name,
            "Violations Found": actual,
            "Expected": expected,
            "Status": status,
            "Rule Description": desc
        })
    return pd.DataFrame(rows)


def audit_quarantined_duplicates() -> pd.DataFrame:
    """Inspect duplicate candidates intentionally isolated in QA quarantine."""
    dup_file = DATA_DIR / "duplicate_candidates_for_cleaning.csv"
    if dup_file.exists():
        df = pd.read_csv(dup_file)
        return df
    return pd.DataFrame()


def run_full_data_audit() -> Dict[str, Any]:
    """Execute complete data audit and compile summary metrics."""
    con = get_connection()
    try:
        counts_df = audit_row_counts(con)
        fk_result = audit_foreign_keys(con)
        missing_df = audit_missing_values(con)
        rules_df = audit_range_and_business_rules(con)
        quarantine_df = audit_quarantined_duplicates()

        # Overall summary KPIs
        total_checks = len(rules_df) + 1  # rules + FK check
        passed_checks = (rules_df["Status"] == "PASS").sum() + (1 if fk_result["status"] == "PASS" else 0)
        overall_health = (passed_checks / total_checks) * 100

        unplanned_nulls = missing_df[
            (missing_df["Is Nullable"] == "No") & (missing_df["Null Count"] > 0)
        ]

        summary = {
            "overall_health_pct": round(overall_health, 1),
            "passed_checks": int(passed_checks),
            "total_checks": int(total_checks),
            "fk_status": fk_result["status"],
            "unplanned_null_cols": len(unplanned_nulls),
            "quarantined_duplicates_count": len(quarantine_df),
            "counts_df": counts_df,
            "fk_result": fk_result,
            "missing_df": missing_df,
            "rules_df": rules_df,
            "quarantine_df": quarantine_df
        }
        return summary
    finally:
        con.close()
