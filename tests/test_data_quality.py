"""
Data Quality & Audit Rules Tests (satisfies BR-11, SC-02).
"""
import pytest
from src.database import get_connection
from src.data_quality import (
    audit_row_counts, audit_foreign_keys,
    audit_missing_values, audit_range_and_business_rules,
    audit_quarantined_duplicates, run_full_data_audit
)


def test_audit_row_counts():
    con = get_connection()
    df = audit_row_counts(con)
    con.close()
    assert (df["Status"] == "PASS").all()


def test_audit_foreign_keys():
    con = get_connection()
    res = audit_foreign_keys(con)
    con.close()
    assert res["status"] == "PASS"
    assert res["violations_count"] == 0


def test_audit_range_and_business_rules():
    con = get_connection()
    df = audit_range_and_business_rules(con)
    con.close()
    # All defined rule checks must pass
    assert (df["Status"] == "PASS").all()


def test_audit_missing_values_strict():
    con = get_connection()
    df = audit_missing_values(con)
    con.close()
    # Mandatory columns must have zero nulls
    unplanned_nulls = df[(df["Is Nullable"] == "No") & (df["Null Count"] > 0)]
    assert len(unplanned_nulls) == 0


def test_quarantined_duplicates():
    df = audit_quarantined_duplicates()
    assert len(df) == 3
    assert "qa_issue" in df.columns


def test_full_data_audit():
    summary = run_full_data_audit()
    assert summary["overall_health_pct"] == 100.0
    assert summary["fk_status"] == "PASS"
