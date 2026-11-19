"""
Shared Pytest Fixtures for ATM Cash Demand Prediction.
"""
from pathlib import Path
import sqlite3
import pytest
import pandas as pd

from src.data_loader import DB_PATH, get_connection, load_daily_fact, load_atm_master, load_date_dim


@pytest.fixture(scope="session")
def db_conn():
    """Provides a session-wide SQLite connection with foreign keys enabled."""
    con = get_connection(DB_PATH)
    try:
        yield con
    finally:
        con.close()


@pytest.fixture
def sample_facts_df():
    """Load all daily facts for testing."""
    return load_daily_fact()


@pytest.fixture
def sample_atms_df():
    """Load all ATM master records."""
    return load_atm_master()


@pytest.fixture
def sample_calendar_df():
    """Load full calendar dimension."""
    return load_date_dim()
