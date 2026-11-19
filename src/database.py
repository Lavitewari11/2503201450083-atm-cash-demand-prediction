"""
SQLite Database Layer for ATM Cash Demand Prediction.
Conforms strictly to Step 8 Database Design & Step 9 ER Diagram.
"""
from pathlib import Path
import sqlite3
from typing import Optional, List, Dict, Any, Union
from datetime import date, datetime
import pandas as pd

from src.utils import date_to_key

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
DB_PATH = DATA_DIR / "app.db"

DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS atm_master (
    atm_id TEXT PRIMARY KEY NOT NULL,
    atm_name TEXT NOT NULL UNIQUE,
    area_name TEXT NOT NULL,
    site_type TEXT NOT NULL CHECK(site_type IN ('Branch','Market','Transit','Residential','Office')),
    is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
    install_date TEXT CHECK(install_date IS NULL OR date(install_date) IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS date_dim (
    date_key INTEGER PRIMARY KEY NOT NULL CHECK(date_key BETWEEN 19000101 AND 29991231),
    date_value TEXT NOT NULL UNIQUE CHECK(date(date_value) IS NOT NULL),
    day_of_month INTEGER NOT NULL CHECK(day_of_month BETWEEN 1 AND 31),
    day_of_week_num INTEGER NOT NULL CHECK(day_of_week_num BETWEEN 1 AND 7),
    day_of_week_name TEXT NOT NULL CHECK(day_of_week_name IN ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')),
    week_of_year INTEGER NOT NULL CHECK(week_of_year BETWEEN 1 AND 53),
    month_num INTEGER NOT NULL CHECK(month_num BETWEEN 1 AND 12),
    month_name TEXT NOT NULL CHECK(month_name IN ('January','February','March','April','May','June','July','August','September','October','November','December')),
    quarter_num INTEGER NOT NULL CHECK(quarter_num BETWEEN 1 AND 4),
    year_num INTEGER NOT NULL CHECK(year_num BETWEEN 1900 AND 2999),
    season_name TEXT CHECK(season_name IS NULL OR season_name IN ('Summer','Monsoon','Winter','Other')),
    is_weekend INTEGER NOT NULL CHECK(is_weekend IN (0,1)),
    is_holiday INTEGER CHECK(is_holiday IS NULL OR is_holiday IN (0,1))
);

CREATE TABLE IF NOT EXISTS atm_daily_fact (
    atm_id TEXT NOT NULL,
    date_key INTEGER NOT NULL,
    withdrawal_amount_inr REAL NOT NULL CHECK(withdrawal_amount_inr >= 0),
    replenished_amount_inr REAL CHECK(replenished_amount_inr IS NULL OR replenished_amount_inr >= 0),
    transaction_count INTEGER CHECK(transaction_count IS NULL OR transaction_count >= 0),
    opening_balance_inr REAL CHECK(opening_balance_inr IS NULL OR opening_balance_inr >= 0),
    closing_balance_inr REAL CHECK(closing_balance_inr IS NULL OR closing_balance_inr >= 0),
    source_batch_id TEXT,
    record_created_at TEXT NOT NULL,
    PRIMARY KEY(atm_id, date_key),
    FOREIGN KEY(atm_id) REFERENCES atm_master(atm_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY(date_key) REFERENCES date_dim(date_key) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS atm_forecast_fact (
    atm_id TEXT NOT NULL,
    target_date_key INTEGER NOT NULL,
    predicted_withdrawal_inr REAL NOT NULL CHECK(predicted_withdrawal_inr >= 0),
    model_name TEXT NOT NULL CHECK(length(trim(model_name)) > 0),
    model_version TEXT NOT NULL CHECK(length(trim(model_version)) > 0),
    generated_at TEXT NOT NULL,
    training_start_key INTEGER,
    training_end_key INTEGER,
    evaluation_split TEXT CHECK(evaluation_split IS NULL OR evaluation_split IN ('train','validation','test','production_demo')),
    is_baseline INTEGER NOT NULL DEFAULT 0 CHECK(is_baseline IN (0,1)),
    PRIMARY KEY(atm_id, target_date_key, model_version, generated_at),
    FOREIGN KEY(atm_id) REFERENCES atm_master(atm_id) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY(target_date_key) REFERENCES date_dim(date_key) ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY(training_start_key) REFERENCES date_dim(date_key) ON UPDATE CASCADE ON DELETE SET NULL,
    FOREIGN KEY(training_end_key) REFERENCES date_dim(date_key) ON UPDATE CASCADE ON DELETE SET NULL,
    CHECK(training_start_key IS NULL OR training_end_key IS NULL OR training_start_key <= training_end_key)
);

CREATE INDEX IF NOT EXISTS idx_daily_date ON atm_daily_fact(date_key);
CREATE INDEX IF NOT EXISTS idx_forecast_target ON atm_forecast_fact(target_date_key);
CREATE INDEX IF NOT EXISTS idx_atm_area ON atm_master(area_name);

CREATE VIEW IF NOT EXISTS vw_atm_daily_analysis AS
SELECT 
    f.atm_id,
    a.atm_name,
    a.area_name,
    a.site_type,
    a.is_active,
    a.install_date,
    d.date_key,
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
    f.withdrawal_amount_inr,
    f.replenished_amount_inr,
    f.transaction_count,
    f.opening_balance_inr,
    f.closing_balance_inr,
    f.source_batch_id,
    f.record_created_at,
    p.predicted_withdrawal_inr,
    p.model_name,
    p.model_version,
    p.generated_at,
    p.training_start_key,
    p.training_end_key,
    p.evaluation_split,
    p.is_baseline
FROM atm_daily_fact f
JOIN atm_master a ON a.atm_id = f.atm_id
JOIN date_dim d ON d.date_key = f.date_key
LEFT JOIN atm_forecast_fact p ON p.atm_id = f.atm_id AND p.target_date_key = f.date_key;
"""


def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """Create a SQLite connection with foreign keys enabled."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON;")
    con.row_factory = sqlite3.Row
    return con


def init_database(db_path: Path = DB_PATH, force: bool = False) -> None:
    """Initialize database tables and populate from CSV if empty or force=True."""
    if force and db_path.exists():
        db_path.unlink()

    con = get_connection(db_path)
    con.executescript(DDL)
    con.commit()

    # Check if atm_master is empty
    count = con.execute("SELECT COUNT(*) FROM atm_master").fetchone()[0]
    if count == 0:
        csv_tables = ["atm_master", "date_dim", "atm_daily_fact", "atm_forecast_fact"]
        for tbl in csv_tables:
            csv_file = DATA_DIR / f"{tbl}.csv"
            if csv_file.exists():
                df = pd.read_csv(csv_file)
                df.to_sql(tbl, con, if_exists="append", index=False)
        con.commit()
    con.close()


def get_table_counts(con: Optional[sqlite3.Connection] = None) -> Dict[str, int]:
    """Return dictionary of row counts for all base tables."""
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True

    tables = ["atm_master", "date_dim", "atm_daily_fact", "atm_forecast_fact"]
    counts = {}
    for tbl in tables:
        row = con.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()
        counts[tbl] = row[0] if row else 0

    if close_con:
        con.close()
    return counts


def load_atm_master(con: Optional[sqlite3.Connection] = None) -> pd.DataFrame:
    """Load all ATM master records."""
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True
    df = pd.read_sql_query("SELECT * FROM atm_master ORDER BY atm_id", con)
    if close_con:
        con.close()
    return df


def load_date_dim(con: Optional[sqlite3.Connection] = None) -> pd.DataFrame:
    """Load full calendar dimension."""
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True
    df = pd.read_sql_query("SELECT * FROM date_dim ORDER BY date_key", con)
    df["date_value"] = pd.to_datetime(df["date_value"]).dt.date
    if close_con:
        con.close()
    return df


def load_daily_fact(
    atm_id: Optional[str] = None,
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None,
    con: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """Load daily fact records with optional ATM and date filtering."""
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True

    query = """
    SELECT 
        f.*,
        d.date_value,
        d.day_of_week_name,
        d.day_of_week_num,
        d.month_name,
        d.month_num,
        d.year_num,
        d.season_name,
        d.is_weekend,
        d.is_holiday,
        a.atm_name,
        a.area_name,
        a.site_type
    FROM atm_daily_fact f
    JOIN date_dim d ON d.date_key = f.date_key
    JOIN atm_master a ON a.atm_id = f.atm_id
    WHERE 1=1
    """
    params: List[Any] = []
    if atm_id:
        query += " AND f.atm_id = ?"
        params.append(atm_id)
    if start_date:
        k_start = date_to_key(start_date)
        query += " AND f.date_key >= ?"
        params.append(k_start)
    if end_date:
        k_end = date_to_key(end_date)
        query += " AND f.date_key <= ?"
        params.append(k_end)

    query += " ORDER BY f.date_key ASC, f.atm_id ASC"
    df = pd.read_sql_query(query, con, params=params)
    if not df.empty:
        df["date_value"] = pd.to_datetime(df["date_value"]).dt.date
    if close_con:
        con.close()
    return df


def load_joined_analysis(
    atm_id: Optional[str] = None,
    start_date: Optional[Union[str, date]] = None,
    end_date: Optional[Union[str, date]] = None,
    model_version: Optional[str] = None,
    con: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """
    Load data from vw_atm_daily_analysis.
    Filters by model_version if provided to avoid duplicate rows caused by multiple forecast runs.
    """
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True

    query = "SELECT * FROM vw_atm_daily_analysis WHERE 1=1"
    params: List[Any] = []
    if atm_id:
        query += " AND atm_id = ?"
        params.append(atm_id)
    if start_date:
        query += " AND date_key >= ?"
        params.append(date_to_key(start_date))
    if end_date:
        query += " AND date_key <= ?"
        params.append(date_to_key(end_date))
    if model_version:
        query += " AND (model_version = ? OR model_version IS NULL)"
        params.append(model_version)

    query += " ORDER BY date_key ASC, atm_id ASC"
    df = pd.read_sql_query(query, con, params=params)
    if not df.empty:
        df["date_value"] = pd.to_datetime(df["date_value"]).dt.date
    if close_con:
        con.close()
    return df


def load_forecast_fact(
    atm_id: Optional[str] = None,
    target_date: Optional[Union[str, date]] = None,
    model_version: Optional[str] = None,
    con: Optional[sqlite3.Connection] = None
) -> pd.DataFrame:
    """Load benchmark and generated forecast records."""
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True

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
    if atm_id:
        query += " AND p.atm_id = ?"
        params.append(atm_id)
    if target_date:
        query += " AND p.target_date_key = ?"
        params.append(date_to_key(target_date))
    if model_version:
        query += " AND p.model_version = ?"
        params.append(model_version)

    query += " ORDER BY p.target_date_key ASC, p.atm_id ASC"
    df = pd.read_sql_query(query, con, params=params)
    if not df.empty:
        df["target_date"] = pd.to_datetime(df["target_date"]).dt.date
    if close_con:
        con.close()
    return df


def save_forecasts(forecasts_df: pd.DataFrame, con: Optional[sqlite3.Connection] = None) -> int:
    """Save newly generated forecasts into atm_forecast_fact."""
    close_con = False
    if con is None:
        con = get_connection()
        close_con = True

    required_cols = [
        "atm_id", "target_date_key", "predicted_withdrawal_inr",
        "model_name", "model_version", "generated_at",
        "training_start_key", "training_end_key", "evaluation_split", "is_baseline"
    ]
    df_to_save = forecasts_df[required_cols].copy()
    
    rows_inserted = 0
    with con:
        for _, row in df_to_save.iterrows():
            con.execute("""
            INSERT OR REPLACE INTO atm_forecast_fact 
            (atm_id, target_date_key, predicted_withdrawal_inr, model_name, model_version, 
             generated_at, training_start_key, training_end_key, evaluation_split, is_baseline)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row["atm_id"],
                int(row["target_date_key"]),
                float(row["predicted_withdrawal_inr"]),
                str(row["model_name"]),
                str(row["model_version"]),
                str(row["generated_at"]),
                int(row["training_start_key"]) if pd.notna(row["training_start_key"]) else None,
                int(row["training_end_key"]) if pd.notna(row["training_end_key"]) else None,
                str(row["evaluation_split"]) if pd.notna(row["evaluation_split"]) else None,
                int(row["is_baseline"])
            ))
            rows_inserted += 1

    if close_con:
        con.close()
    return rows_inserted
