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


def test_atm_encoding_consistency():
    """Verify ATM categorical encoding is deterministic across single-row and multi-row contexts."""
    from src.forecasting import prepare_features, get_atm_encoding_map
    import pandas as pd

    atm_map = get_atm_encoding_map()
    assert atm_map["ATM-001"] == 0
    assert atm_map["ATM-045"] == 44

    # Single-row DataFrame for ATM-045 must NOT collapse to 0
    single_row = pd.DataFrame([{
        "atm_id": "ATM-045",
        "date_value": "2026-01-05",
        "site_type": "Branch",
        "season_name": "Winter",
        "is_holiday": 0
    }])
    X_single, _ = prepare_features(single_row)
    assert X_single.iloc[0]["atm_code"] == 44, f"Expected atm_code 44 for ATM-045, got {X_single.iloc[0]['atm_code']}"

    # Unknown ATM must map to -1
    unknown_row = pd.DataFrame([{
        "atm_id": "ATM-999",
        "date_value": "2026-01-05",
        "site_type": "Branch",
        "season_name": "Winter",
        "is_holiday": 0
    }])
    X_unknown, _ = prepare_features(unknown_row)
    assert X_unknown.iloc[0]["atm_code"] == -1


def test_october_season_fallback_classification():
    """Verify October (month 10) is consistently classified as 'Other' (season_code = 0)."""
    from src.forecasting import get_season_for_month, prepare_features
    import pandas as pd

    assert get_season_for_month(10) == "Other"

    oct_row = pd.DataFrame([{
        "atm_id": "ATM-001",
        "date_value": "2026-10-15",
        "site_type": "Branch",
        "season_name": get_season_for_month(10),
        "is_holiday": 0
    }])
    X_oct, _ = prepare_features(oct_row)
    assert X_oct.iloc[0]["season_code"] == 0


def test_seasonal_naive_fallback_hierarchy():
    """Verify SeasonalNaiveBaseline falls back to ATM mean before network mean."""
    import pandas as pd
    from src.forecasting import SeasonalNaiveBaseline

    # ATM-A only has Monday (day 1) data with mean 30,000
    # ATM-B only has Tuesday (day 2) data with mean 80,000
    train_df = pd.DataFrame([
        {"atm_id": "ATM-A", "day_of_week_num": 1, "withdrawal_amount_inr": 30000.0},
        {"atm_id": "ATM-B", "day_of_week_num": 2, "withdrawal_amount_inr": 80000.0},
    ])
    sn = SeasonalNaiveBaseline().fit(train_df)
    assert sn.global_mean == 55000.0

    # Test 1: Exact weekday match for ATM-A (Monday) -> 30,000
    test_match = pd.DataFrame([{"atm_id": "ATM-A", "day_of_week_num": 1}])
    assert sn.predict(test_match)[0] == 30000.0

    # Test 2: Unseen weekday for ATM-A (Wednesday, day 3) -> should fallback to ATM-A mean (30,000), NOT global (55,000)
    test_unseen_day = pd.DataFrame([{"atm_id": "ATM-A", "day_of_week_num": 3}])
    assert sn.predict(test_unseen_day)[0] == 30000.0

    # Test 3: Completely unseen ATM-C -> falls back to global mean (55,000)
    test_unseen_atm = pd.DataFrame([{"atm_id": "ATM-C", "day_of_week_num": 1}])
    assert sn.predict(test_unseen_atm)[0] == 55000.0


def test_predictions_atm001_vs_atm045_are_differentiated():
    """Verify ATM-001 (high demand) and ATM-045 (low demand) receive distinct predictions."""
    facts_df = load_daily_fact()
    atms_df = load_atm_master()
    cal_df = load_date_dim()

    res_001 = predict_single_atm_demand("ATM-001", date(2026, 1, 5), facts_df, atms_df, cal_df)
    res_045 = predict_single_atm_demand("ATM-045", date(2026, 1, 5), facts_df, atms_df, cal_df)

    assert res_001["status"] == "SUCCESS"
    assert res_045["status"] == "SUCCESS"
    # Predictions must not be identical
    diff = abs(res_001["predicted_demand_inr"] - res_045["predicted_demand_inr"])
    assert diff > 5000, f"Expected distinct predictions for ATM-001 and ATM-045, difference was only {diff}"

