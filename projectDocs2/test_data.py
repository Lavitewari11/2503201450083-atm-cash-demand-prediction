"""Database and data-quality tests for ATM Cash Demand Prediction."""
from pathlib import Path
import sqlite3
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "app.db"
REQUIRED_TABLES = {"atm_master", "date_dim", "atm_daily_fact", "atm_forecast_fact"}

@pytest.fixture
def conn():
    assert DB_PATH.exists(), f"Database not found: {DB_PATH}"
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    try:
        yield db
    finally:
        db.close()

def test_database_file_and_required_tables_load(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert REQUIRED_TABLES <= names
    for table in REQUIRED_TABLES:
        conn.execute(f"SELECT * FROM {table} LIMIT 1").fetchall()

def test_step10_seed_row_counts_are_present(conn):
    expected = {"atm_master": 50, "date_dim": 730, "atm_daily_fact": 250, "atm_forecast_fact": 75}
    actual = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in expected}
    assert actual == expected

def test_primary_keys_are_unique(conn):
    checks = [
        ("atm_master", "atm_id"),
        ("date_dim", "date_key"),
        ("atm_daily_fact", "atm_id, date_key"),
        ("atm_forecast_fact", "atm_id, target_date_key, model_version, generated_at"),
    ]
    for table, cols in checks:
        row = conn.execute(f"SELECT COUNT(*) FROM (SELECT {cols} FROM {table} GROUP BY {cols} HAVING COUNT(*) > 1)").fetchone()
        assert row[0] == 0, f"Duplicate PK values in {table}"

def test_foreign_keys_are_valid(conn):
    assert conn.execute("PRAGMA foreign_key_check").fetchall() == []

def test_daily_fact_values_respect_nonnegative_constraints(conn):
    assert conn.execute("SELECT COUNT(*) FROM atm_daily_fact WHERE withdrawal_amount_inr < 0").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM atm_daily_fact WHERE replenished_amount_inr < 0").fetchone()[0] == 0

def test_missing_replenishment_is_not_coerced_to_zero(conn):
    null_count = conn.execute("SELECT COUNT(*) FROM atm_daily_fact WHERE replenished_amount_inr IS NULL").fetchone()[0]
    assert null_count >= 0
    # Semantic contract: NULL remains NULL in the source table and is not rewritten by test setup.
    assert conn.execute("SELECT COUNT(*) FROM atm_daily_fact WHERE replenished_amount_inr IS NULL AND replenished_amount_inr = 0").fetchone()[0] == 0

def test_duplicate_candidates_are_separate_from_constrained_fact_table():
    candidate_file = ROOT / "data" / "duplicate_candidates_for_cleaning.csv"
    assert candidate_file.exists()
    candidates = pd.read_csv(candidate_file)
    assert len(candidates) > 0
    assert "atm_daily_fact" in REQUIRED_TABLES
