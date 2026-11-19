"""
Validation Pipeline (conforms strictly to BUILD-03, BR-11, and Step 8/9 rules).
Performs deterministic, auditable checks across schema, keys, nulls, and ranges.
"""
from typing import Dict, Any, List
import sqlite3
import pandas as pd
from src.data_loader import get_connection, DATA_DIR


def validate_foreign_keys(con: sqlite3.Connection) -> Dict[str, Any]:
    """Execute PRAGMA foreign_key_check to verify relational integrity."""
    violations = con.execute("PRAGMA foreign_key_check").fetchall()
    passed = len(violations) == 0
    return {
        "status": "PASS" if passed else "FAIL",
        "violations_count": len(violations),
        "details": violations
    }


def validate_table_counts(con: sqlite3.Connection) -> Dict[str, int]:
    """Return dictionary of row counts for all base tables."""
    tables = ["atm_master", "date_dim", "atm_daily_fact", "atm_forecast_fact"]
    return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables}


def validate_schema_rules(con: sqlite3.Connection) -> pd.DataFrame:
    """Execute rule-based queries against SQLite tables."""
    checks = [
        (
            "withdrawal_nonnegative",
            "SELECT COUNT(*) FROM atm_daily_fact WHERE withdrawal_amount_inr < 0",
            0,
            "Daily withdrawals must be >= 0 INR"
        ),
        (
            "replenishment_nonnegative",
            "SELECT COUNT(*) FROM atm_daily_fact WHERE replenished_amount_inr < 0",
            0,
            "Replenished amounts must be >= 0 INR when present"
        ),
        (
            "forecast_nonnegative",
            "SELECT COUNT(*) FROM atm_forecast_fact WHERE predicted_withdrawal_inr < 0",
            0,
            "Forecast amounts must be >= 0 INR"
        ),
        (
            "allowed_site_types",
            "SELECT COUNT(*) FROM atm_master WHERE site_type NOT IN ('Branch','Market','Transit','Residential','Office')",
            0,
            "Site types must belong to allowed categories"
        ),
        (
            "date_key_matches_date",
            "SELECT COUNT(*) FROM date_dim WHERE date_key != CAST(REPLACE(date_value,'-','') AS INTEGER)",
            0,
            "date_key must equal integer YYYYMMDD of date_value"
        ),
        (
            "unique_daily_grain",
            "SELECT COUNT(*) FROM (SELECT atm_id, date_key, COUNT(*) c FROM atm_daily_fact GROUP BY atm_id, date_key HAVING c > 1)",
            0,
            "Composite primary key (atm_id, date_key) must be strictly unique"
        ),
        (
            "atm_id_foreign_key",
            "SELECT COUNT(*) FROM atm_daily_fact WHERE atm_id NOT IN (SELECT atm_id FROM atm_master)",
            0,
            "Every daily fact must reference an existing registered ATM"
        )
    ]

    results = []
    for check_name, query, expected, desc in checks:
        violations = con.execute(query).fetchone()[0]
        results.append({
            "check_name": check_name,
            "violations": violations,
            "expected": expected,
            "status": "PASS" if violations == expected else "FAIL",
            "description": desc
        })
    return pd.DataFrame(results)


def validate_missing_values(con: sqlite3.Connection) -> pd.DataFrame:
    """Audit missing values across all base tables."""
    tables = ["atm_master", "date_dim", "atm_daily_fact", "atm_forecast_fact"]
    results = []
    for tbl in tables:
        df = pd.read_sql_query(f"SELECT * FROM {tbl}", con)
        total_rows = len(df)
        for col in df.columns:
            null_count = int(df[col].isna().sum())
            null_pct = (null_count / total_rows * 100) if total_rows > 0 else 0.0
            is_nullable = col in [
                "install_date", "season_name", "is_holiday",
                "replenished_amount_inr", "transaction_count",
                "opening_balance_inr", "closing_balance_inr",
                "source_batch_id", "training_start_key", "training_end_key", "evaluation_split"
            ]
            results.append({
                "table_name": tbl,
                "column_name": col,
                "total_rows": total_rows,
                "null_count": null_count,
                "null_pct": round(null_pct, 2),
                "is_nullable": is_nullable,
                "status": "PASS" if (is_nullable or null_count == 0) else "UNPLANNED_NULL"
            })
    return pd.DataFrame(results)


def get_quarantined_duplicates() -> pd.DataFrame:
    """Read duplicate candidates intentionally isolated in QA quarantine."""
    dup_file = DATA_DIR / "duplicate_candidates_for_cleaning.csv"
    if dup_file.exists():
        return pd.read_csv(dup_file)
    return pd.DataFrame()


def run_validation_pipeline() -> Dict[str, Any]:
    """Execute complete validation pipeline and return structured audit report."""
    con = get_connection()
    try:
        counts = validate_table_counts(con)
        fk_audit = validate_foreign_keys(con)
        rules_df = validate_schema_rules(con)
        nulls_df = validate_missing_values(con)
        quarantine_df = get_quarantined_duplicates()

        all_rules_pass = (rules_df["status"] == "PASS").all()
        fk_pass = fk_audit["status"] == "PASS"
        no_unplanned_nulls = (nulls_df["status"] == "PASS").all()

        return {
            "overall_status": "PASS" if (all_rules_pass and fk_pass and no_unplanned_nulls) else "FAIL",
            "row_counts": counts,
            "foreign_key_audit": fk_audit,
            "schema_rules_df": rules_df,
            "missing_values_df": nulls_df,
            "quarantined_duplicates_df": quarantine_df
        }
    finally:
        con.close()
