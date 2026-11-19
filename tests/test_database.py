"""
Database and SQLite Schema Tests.
"""
import pytest
import sqlite3
from src.database import (
    get_connection, get_table_counts,
    load_atm_master, load_date_dim,
    load_daily_fact, load_forecast_fact, load_joined_analysis
)


def test_database_connection():
    con = get_connection()
    assert con is not None
    # Check FK PRAGMA is enabled
    fk_status = con.execute("PRAGMA foreign_keys").fetchone()[0]
    assert fk_status == 1
    con.close()


def test_table_row_counts():
    counts = get_table_counts()
    assert counts["atm_master"] == 50
    assert counts["date_dim"] == 730
    assert counts["atm_daily_fact"] == 250
    assert counts["atm_forecast_fact"] == 75


def test_foreign_key_integrity():
    con = get_connection()
    violations = con.execute("PRAGMA foreign_key_check").fetchall()
    assert len(violations) == 0, f"Expected 0 FK violations, got {violations}"
    con.close()


def test_data_loaders():
    atms = load_atm_master()
    assert len(atms) == 50
    assert "atm_id" in atms.columns

    dates = load_date_dim()
    assert len(dates) == 730
    assert "date_key" in dates.columns

    facts = load_daily_fact()
    assert len(facts) == 250
    assert "withdrawal_amount_inr" in facts.columns

    forecasts = load_forecast_fact()
    assert len(forecasts) == 75
    assert "predicted_withdrawal_inr" in forecasts.columns

    joined = load_joined_analysis()
    assert not joined.empty
    assert "atm_name" in joined.columns
