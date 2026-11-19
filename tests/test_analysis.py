"""Deterministic unit tests for analysis functions planned for Step 15.

The import contract is src.analysis. Missing implementation is reported as xfail
until Step 15; once the module exists, the assertions become active.
"""
import math
import pandas as pd
import pytest

try:
    from src.analysis import (
        calculate_total_withdrawal,
        calculate_average_daily_withdrawal,
        forecast_metrics,
        descriptive_statistics,
        apply_filters,
    )
except ImportError:
    pytestmark = pytest.mark.xfail(reason="src.analysis is scheduled for implementation in Step 15", strict=False)

def test_total_withdrawal_tiny_fixture():
    frame = pd.DataFrame({"withdrawal_amount_inr": [100, 200, 300]})
    assert calculate_total_withdrawal(frame) == pytest.approx(600)

def test_average_daily_withdrawal_tiny_fixture():
    frame = pd.DataFrame({"withdrawal_amount_inr": [100, 200, 300]})
    assert calculate_average_daily_withdrawal(frame) == pytest.approx(200)

def test_forecast_mae_rmse_tiny_fixture():
    actual = [100, 200]
    predicted = [110, 180]
    result = forecast_metrics(actual, predicted)
    assert result["mae"] == pytest.approx(15)
    assert result["rmse"] == pytest.approx(math.sqrt(250))

def test_descriptive_statistics_tiny_fixture():
    result = descriptive_statistics(pd.Series([10, 20, 30, 40]))
    assert result["count"] == 4
    assert result["mean"] == pytest.approx(25)
    assert result["median"] == pytest.approx(25)

def test_apply_filters_limits_atm_and_date_range():
    frame = pd.DataFrame({
        "atm_id": ["A", "A", "B"],
        "date_value": ["2026-01-01", "2026-01-02", "2026-01-01"],
        "withdrawal_amount_inr": [10, 20, 30],
    })
    out = apply_filters(frame, atm_id="A", start_date="2026-01-02", end_date="2026-01-02")
    assert out["withdrawal_amount_inr"].tolist() == [20]
