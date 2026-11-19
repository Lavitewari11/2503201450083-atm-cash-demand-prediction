"""
Forecasting Engine and Evaluation Tests (satisfies BR-06, BR-07, BR-10, KPI-05, KPI-06).
"""
import pytest
from datetime import date
from src.database import load_daily_fact, load_atm_master, load_date_dim
from src.models import (
    evaluate_forecast_models, predict_single_atm,
    predict_network_aggregate, CashDemandMLForecaster
)


@pytest.fixture
def facts_df():
    return load_daily_fact()


@pytest.fixture
def atms_df():
    return load_atm_master()


@pytest.fixture
def calendar_df():
    return load_date_dim()


def test_chronological_holdout_evaluation(facts_df):
    eval_res = evaluate_forecast_models(facts_df, test_ratio=0.20)
    assert "error" not in eval_res
    assert eval_res["train_rows"] > 0
    assert eval_res["test_rows"] > 0
    # Strict chronological assertion: train end must be <= test start
    assert eval_res["train_end_date"] <= eval_res["test_start_date"]

    table = eval_res["comparison_table"]
    assert len(table) >= 3
    assert "MAE (INR)" in table.columns
    assert "RMSE (INR)" in table.columns

    # Verify KPI-05: ML model MAE is lower than naive baseline MAE
    ml_row = table[table["Model Name"].str.contains("Random Forest")].iloc[0]
    sn_row = table[table["Model Name"].str.contains("Seasonal Naive")].iloc[0]
    assert ml_row["MAE (INR)"] < sn_row["MAE (INR)"], (
        f"Expected ML MAE ({ml_row['MAE (INR)']}) < Seasonal Naive MAE ({sn_row['MAE (INR)']})"
    )


def test_predict_single_atm_success(facts_df, atms_df, calendar_df):
    target = date(2025, 12, 31)
    res = predict_single_atm(
        atm_id="ATM-001",
        target_date=target,
        facts_df=facts_df,
        atms_df=atms_df,
        calendar_df=calendar_df
    )
    assert res["status"] == "SUCCESS"
    assert res["predicted_demand_inr"] >= 0
    assert "target_date" in res
    assert "disclaimer" in res


def test_predict_single_atm_insufficient_history(facts_df, atms_df, calendar_df):
    # Filter facts to only 1 observation for ATM-001
    sparse_facts = facts_df[facts_df["atm_id"] == "ATM-001"].head(1)
    res = predict_single_atm(
        atm_id="ATM-001",
        target_date=date(2025, 12, 31),
        facts_df=sparse_facts,
        atms_df=atms_df,
        calendar_df=calendar_df
    )
    # Must report UNAVAILABLE per BR-06 rather than a fabricated estimate
    assert res["status"] == "UNAVAILABLE"
    assert "Insufficient" in res["message"]


def test_predict_network_aggregate(facts_df, atms_df, calendar_df):
    target = date(2025, 12, 31)
    res = predict_network_aggregate(
        target_date=target,
        facts_df=facts_df,
        atms_df=atms_df,
        calendar_df=calendar_df
    )
    assert res["total_network_demand_inr"] > 0
    assert res["included_atms_count"] > 0
    # Inactive ATMs must be in exclusions table
    assert res["excluded_atms_count"] >= 2
    # Sum of predictions must match total_network_demand_inr
    preds_sum = res["predictions_table"]["predicted_withdrawal_inr"].sum()
    assert abs(preds_sum - res["total_network_demand_inr"]) < 0.1
