"""
Forecasting Engine Tests (satisfies BUILD-06, BR-06, BR-07, BR-10, KPI-05).
"""
import pytest
from datetime import date
from src.data_loader import load_daily_fact, load_atm_master, load_date_dim
from src.forecasting import (
    evaluate_chronological_holdout,
    predict_single_atm_demand,
    predict_network_demand,
    SeasonalNaiveBaseline,
    MovingAverageBaseline,
    CashDemandMLForecaster
)


def test_chronological_holdout_split_and_kpi05():
    facts_df = load_daily_fact()
    res = evaluate_chronological_holdout(facts_df, test_ratio=0.20)

    assert "error" not in res
    assert res["train_rows"] > 0
    assert res["test_rows"] > 0
    # Strict chronological check (zero future leakage)
    assert res["train_end_date"] <= res["test_start_date"]

    table = res["comparison_table"]
    assert len(table) >= 3
    assert "MAE (INR)" in table.columns
    assert "RMSE (INR)" in table.columns

    # Verify KPI-05: ML model beats seasonal naive baseline
    ml_mae = table[table["Model Name"].str.contains("Random Forest")].iloc[0]["MAE (INR)"]
    sn_mae = table[table["Model Name"].str.contains("Seasonal Naive")].iloc[0]["MAE (INR)"]
    assert ml_mae < sn_mae, f"Expected ML MAE ({ml_mae}) < Baseline MAE ({sn_mae})"


def test_predict_single_atm_success():
    facts_df = load_daily_fact()
    atms_df = load_atm_master()
    cal_df = load_date_dim()

    res = predict_single_atm_demand(
        atm_id="ATM-001",
        target_date=date(2026, 1, 5),
        facts_df=facts_df,
        atms_df=atms_df,
        calendar_df=cal_df
    )
    assert res["status"] == "SUCCESS"
    assert res["predicted_demand_inr"] >= 0
    assert "target_date" in res
    assert "disclaimer" in res


def test_predict_single_atm_insufficient_history():
    facts_df = load_daily_fact()
    atms_df = load_atm_master()
    cal_df = load_date_dim()

    # Sparse history (only 1 observation)
    sparse_facts = facts_df[facts_df["atm_id"] == "ATM-001"].head(1)
    res = predict_single_atm_demand(
        atm_id="ATM-001",
        target_date=date(2026, 1, 5),
        facts_df=sparse_facts,
        atms_df=atms_df,
        calendar_df=cal_df
    )
    # Must report UNAVAILABLE rather than fabricated estimate
    assert res["status"] == "UNAVAILABLE"
    assert "Insufficient" in res["message"]


def test_predict_network_demand():
    facts_df = load_daily_fact()
    atms_df = load_atm_master()
    cal_df = load_date_dim()

    res = predict_network_demand(
        target_date=date(2026, 1, 5),
        facts_df=facts_df,
        atms_df=atms_df,
        calendar_df=cal_df
    )
    assert res["total_network_demand_inr"] > 0
    assert res["included_atms_count"] > 0
    assert res["excluded_atms_count"] >= 2  # Inactive ATMs disclosed
    # Sum of predictions must match total network demand
    sum_preds = res["predictions_table"]["predicted_withdrawal_inr"].sum()
    assert abs(sum_preds - res["total_network_demand_inr"]) < 0.1
