"""
Data Loader Layer (satisfies BUILD-02, US-01, US-02).
Safe SQLite connection context, parameterised queries, and schema-aware table loading.
"""
from pathlib import Path
import sqlite3
from typing import Optional, List, Any, Union
from datetime import date
import pandas as pd

from src.utils import date_to_key

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "app.db"

REQUIRED_TABLES = {"atm_master", "date_dim", "atm_daily_fact", "atm_forecast_fact"}


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create a SQLite connection with foreign keys enabled."""
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found at {db_path}. Run generate_data.py to create it.")
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")
    con.row_factory = sqlite3.Row
    return con


def verify_schema(con: sqlite3.Connection) -> None:
    """Verify that all required tables exist in the database."""
    names = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    missing = REQUIRED_TABLES - names
    if missing:
        raise ValueError(f"Database is missing required tables: {missing}")


def load_atm_master(con: Optional[sqlite3.Connection] = None) -> pd.DataFrame:
    """Load all records from atm_master."""
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True
    try:
        verify_schema(con)
        df = pd.read_sql_query("SELECT * FROM atm_master ORDER BY atm_id", con)
        return df
    finally:
        if close_con:
            con.close()


def load_date_dim(con: Optional[sqlite3.Connection] = None) -> pd.DataFrame:
    """Load all records from date_dim."""
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True
    try:
        verify_schema(con)
        df = pd.read_sql_query("SELECT * FROM date_dim ORDER BY date_key", con)
        if "date_value" in df.columns:
            df["date_value"] = pd.to_datetime(df["date_value"]).dt.date
        return df
    finally:
        if close_con:
            con.close()


def load_daily_fact(
    atm_id: Optional[str] = None,
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None,
    region: Optional[str] = None,
    site_type: Optional[str] = None,
    con: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """
    Load daily facts with relational joins to ATM master and date dimension.
    Supports filtering by ATM ID, date range, region, and site type.
    Keeps NULL replenishment values as NULL (per BUILD-02).
    """
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True
    try:
        verify_schema(con)
        query = """
        SELECT 
            f.atm_id,
            f.date_key,
            f.withdrawal_amount_inr,
            f.replenished_amount_inr,
            f.transaction_count,
            f.opening_balance_inr,
            f.closing_balance_inr,
            f.source_batch_id,
            f.record_created_at,
            d.date_value,
            d.day_of_month,
            d.day_of_week_num,
            d.day_of_week_name,
            d.week_of_year,
            d.month_num,
            d.month_name,
            d.quarter_num,
            d.year_num,
            d.season_name,
            d.is_weekend,
            d.is_holiday,
            a.atm_name,
            a.area_name,
            a.site_type,
            a.is_active
        FROM atm_daily_fact f
        JOIN date_dim d ON d.date_key = f.date_key
        JOIN atm_master a ON a.atm_id = f.atm_id
        WHERE 1=1
        """
        params: List[Any] = []
        if atm_id and atm_id != "All ATMs":
            query += " AND f.atm_id = ?"
            params.append(atm_id)
        if start_date:
            query += " AND f.date_key >= ?"
            params.append(date_to_key(start_date))
        if end_date:
            query += " AND f.date_key <= ?"
            params.append(date_to_key(end_date))
        if region and region != "All regions":
            query += " AND a.area_name = ?"
            params.append(region)
        if site_type and site_type != "All site types":
            query += " AND a.site_type = ?"
            params.append(site_type)

        query += " ORDER BY f.date_key ASC, f.atm_id ASC"
        df = pd.read_sql_query(query, con, params=params)
        if not df.empty and "date_value" in df.columns:
            df["date_value"] = pd.to_datetime(df["date_value"]).dt.date
        return df
    finally:
        if close_con:
            con.close()


def load_forecast_fact(
    atm_id: Optional[str] = None,
    target_date: Optional[Union[str, date]] = None,
    model_version: Optional[str] = None,
    generated_at: Optional[str] = None,
    con: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """
    Load forecast facts with explicit model_version / generated_at selection.
    Prevents duplicate Cartesian joins across multiple runs.
    """
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True
    try:
        verify_schema(con)
        query = """
        SELECT 
            p.*,
            d.date_value AS target_date,
            d.day_of_week_name,
            d.month_name,
            d.season_name,
            a.atm_name,
            a.area_name,
            a.site_type
        FROM atm_forecast_fact p
        JOIN date_dim d ON d.date_key = p.target_date_key
        JOIN atm_master a ON a.atm_id = p.atm_id
        WHERE 1=1
        """
        params: List[Any] = []
        if atm_id and atm_id != "All ATMs":
            query += " AND p.atm_id = ?"
            params.append(atm_id)
        if target_date:
            query += " AND p.target_date_key = ?"
            params.append(date_to_key(target_date))
        if model_version:
            query += " AND p.model_version = ?"
            params.append(model_version)
        if generated_at:
            query += " AND p.generated_at = ?"
            params.append(generated_at)

        query += " ORDER BY p.target_date_key ASC, p.atm_id ASC"
        df = pd.read_sql_query(query, con, params=params)
        if not df.empty and "target_date" in df.columns:
            df["target_date"] = pd.to_datetime(df["target_date"]).dt.date
        return df
    finally:
        if close_con:
            con.close()
