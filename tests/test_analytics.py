"""
Analytics and Aggregation Tests (satisfies BR-01 to BR-05, BR-08, BR-09).
"""
import pytest
import pandas as pd
from src.database import load_daily_fact, load_atm_master
from src.analytics import (
    get_historical_summary, get_weekday_distribution,
    get_monthly_distribution, get_seasonal_distribution,
    get_atm_rankings, detect_demand_anomalies,
    compare_replenishment_vs_withdrawal, WEEKDAY_ORDER
)


@pytest.fixture
def sample_facts():
    return load_daily_fact()


@pytest.fixture
def sample_atms():
    return load_atm_master()


def test_historical_summary(sample_facts):
    summary = get_historical_summary(sample_facts)
    assert summary["observed_days"] == 250
    assert summary["total_withdrawn"] > 0
    assert summary["avg_daily_observed"] > 0
    assert summary["min_daily"] <= summary["avg_daily_observed"] <= summary["max_daily"]


def test_weekday_distribution_reconciliation(sample_facts):
    df_week = get_weekday_distribution(sample_facts)
    # Check all 7 days present
    assert len(df_week) == 7
    assert list(df_week["day_of_week_name"]) == WEEKDAY_ORDER
    # Check total reconciles within 1 INR tolerance (BR-03 acceptance criteria)
    total_reconciled = df_week["total_withdrawn"].sum()
    expected_total = sample_facts["withdrawal_amount_inr"].sum()
    assert abs(total_reconciled - expected_total) < 1.0


def test_monthly_and_seasonal_distribution(sample_facts):
    df_month = get_monthly_distribution(sample_facts)
    assert not df_month.empty
    assert "total_withdrawn" in df_month.columns

    df_season = get_seasonal_distribution(sample_facts)
    assert not df_season.empty
    assert "Summer" in df_season["season_name"].values


def test_atm_rankings(sample_facts, sample_atms):
    df_ranked = get_atm_rankings(sample_facts, sample_atms, sort_by="total_withdrawn", ascending=False)
    assert not df_ranked.empty
    assert "rank" in df_ranked.columns
    assert df_ranked.iloc[0]["rank"] == 1
    # Check sorting is descending
    assert df_ranked.iloc[0]["total_withdrawn"] >= df_ranked.iloc[-1]["total_withdrawn"]


def test_demand_anomalies(sample_facts):
    anomalies = detect_demand_anomalies(sample_facts, method="zscore", threshold=2.0)
    assert not anomalies.empty
    assert "observed_withdrawal_inr" in anomalies.columns
    assert "score" in anomalies.columns


def test_replenishment_comparison(sample_facts):
    comp = compare_replenishment_vs_withdrawal(sample_facts)
    assert comp["total_withdrawn"] > 0
    assert comp["total_replenished"] > 0
    assert "net_difference" in comp
    assert comp["replenishment_ratio_pct"] > 0
