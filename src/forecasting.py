"""
Forecasting and Chronological Evaluation Module (satisfies BUILD-06, BR-06, BR-07, BR-10).
Guarantees zero future data leakage, compares against naive baselines, and returns non-negative predictions.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import date, datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

from src.utils import date_to_key, key_to_date
from src.analysis import forecast_metrics


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Extract calendar and historical features for demand forecasting without data leakage."""
    df_feat = df.copy()

    if "date_value" in df_feat.columns:
        dates = pd.to_datetime(df_feat["date_value"])
        df_feat["day_of_month"] = dates.dt.day
        df_feat["day_of_week_num"] = dates.dt.dayofweek + 1
        df_feat["month_num"] = dates.dt.month
        df_feat["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)
        df_feat["is_month_end"] = (dates.dt.day >= 25).astype(int)

    season_map = {"Summer": 1, "Monsoon": 2, "Winter": 3, "Other": 0}
    if "season_name" in df_feat.columns:
        df_feat["season_code"] = df_feat["season_name"].map(season_map).fillna(0).astype(int)
    else:
        df_feat["season_code"] = 0

    df_feat["holiday_code"] = df_feat["is_holiday"].fillna(0).astype(int) if "is_holiday" in df_feat.columns else 0

    if "atm_id" in df_feat.columns:
        df_feat["atm_code"] = df_feat["atm_id"].astype("category").cat.codes
    else:
        df_feat["atm_code"] = 0

    site_map = {"Branch": 1, "Market": 2, "Transit": 3, "Residential": 4, "Office": 5}
    if "site_type" in df_feat.columns:
        df_feat["site_code"] = df_feat["site_type"].map(site_map).fillna(0).astype(int)
    else:
        df_feat["site_code"] = 0

    feature_cols = [
        "atm_code", "site_code", "day_of_week_num", "month_num",
        "day_of_month", "season_code", "is_weekend", "is_month_end", "holiday_code"
    ]
    for col in feature_cols:
        if col not in df_feat.columns:
            df_feat[col] = 0

    X = df_feat[feature_cols].copy()
    y = df_feat["withdrawal_amount_inr"].copy() if "withdrawal_amount_inr" in df_feat.columns else pd.Series(dtype=float)
    return X, y


class SeasonalNaiveBaseline:
    """Predicts historical ATM-specific weekday average."""
    def __init__(self):
        self.lookup: Dict[Tuple[str, int], float] = {}
        self.global_mean: float = 0.0

    def fit(self, train_df: pd.DataFrame) -> "SeasonalNaiveBaseline":
        self.global_mean = float(train_df["withdrawal_amount_inr"].mean())
        grouped = train_df.groupby(["atm_id", "day_of_week_num"])["withdrawal_amount_inr"].mean()
        self.lookup = grouped.to_dict()
        return self

    def predict(self, test_df: pd.DataFrame) -> np.ndarray:
        preds = []
        for _, row in test_df.iterrows():
            key = (row["atm_id"], int(row["day_of_week_num"]))
            p = self.lookup.get(key, self.global_mean)
            preds.append(max(0.0, float(p)))
        return np.array(preds)


class MovingAverageBaseline:
    """Predicts recent overall historical mean for ATM."""
    def __init__(self, window: int = 7):
        self.window = window
        self.atm_means: Dict[str, float] = {}
        self.global_mean: float = 0.0

    def fit(self, train_df: pd.DataFrame) -> "MovingAverageBaseline":
        self.global_mean = float(train_df["withdrawal_amount_inr"].mean())
        grouped = train_df.groupby("atm_id")["withdrawal_amount_inr"].mean()
        self.atm_means = grouped.to_dict()
        return self

    def predict(self, test_df: pd.DataFrame) -> np.ndarray:
        preds = []
        for _, row in test_df.iterrows():
            p = self.atm_means.get(row["atm_id"], self.global_mean)
            preds.append(max(0.0, float(p)))
        return np.array(preds)


class CashDemandMLForecaster:
    """Random Forest Regressor capturing non-linear calendar and ATM interactions."""
    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=10,
            min_samples_split=3,
            random_state=random_state
        )

    def fit(self, train_df: pd.DataFrame) -> "CashDemandMLForecaster":
        X, y = prepare_features(train_df)
        self.model.fit(X, y)
        return self

    def predict(self, test_df: pd.DataFrame) -> np.ndarray:
        X, _ = prepare_features(test_df)
        preds = self.model.predict(X)
        return np.clip(preds, a_min=0.0, a_max=None)


def evaluate_chronological_holdout(
    facts_df: pd.DataFrame,
    test_ratio: float = 0.20
) -> Dict[str, Any]:
    """
    Evaluates forecast models on a strictly chronological holdout test set (BR-07, OQ-07, KPI-05).
    """
    if facts_df.empty or len(facts_df) < 15:
        return {"error": "Insufficient data to perform chronological evaluation."}

    df_sorted = facts_df.sort_values(["date_key", "atm_id"]).reset_index(drop=True)
    unique_dates = df_sorted["date_key"].unique()
    split_idx = int(len(unique_dates) * (1 - test_ratio))
    split_date_key = unique_dates[split_idx]

    train_df = df_sorted[df_sorted["date_key"] < split_date_key].copy()
    test_df = df_sorted[df_sorted["date_key"] >= split_date_key].copy()

    if train_df.empty or test_df.empty:
        return {"error": "Train/test split produced an empty partition."}

    y_true = test_df["withdrawal_amount_inr"].values

    # Baselines
    sn_model = SeasonalNaiveBaseline().fit(train_df)
    sn_preds = sn_model.predict(test_df)
    sn_metrics = forecast_metrics(y_true, sn_preds)

    ma_model = MovingAverageBaseline().fit(train_df)
    ma_preds = ma_model.predict(test_df)
    ma_metrics = forecast_metrics(y_true, ma_preds)

    # ML Model
    ml_model = CashDemandMLForecaster().fit(train_df)
    ml_preds = ml_model.predict(test_df)
    ml_metrics = forecast_metrics(y_true, ml_preds)

    # Ridge ML
    ridge = Ridge(alpha=1.0)
    X_train, y_train = prepare_features(train_df)
    X_test, _ = prepare_features(test_df)
    ridge.fit(X_train, y_train)
    ridge_preds = np.clip(ridge.predict(X_test), 0.0, None)
    ridge_metrics = forecast_metrics(y_true, ridge_preds)

    comparison_rows = [
        {
            "Model Name": "Random Forest Regressor (ML)",
            "Model Type": "Machine Learning",
            "MAE (INR)": round(ml_metrics["mae"], 2),
            "RMSE (INR)": round(ml_metrics["rmse"], 2),
            "Better Than Baseline?": "YES (Pass KPI-05)" if ml_metrics["mae"] < sn_metrics["mae"] else "NO"
        },
        {
            "Model Name": "Ridge Regression (Linear ML)",
            "Model Type": "Machine Learning",
            "MAE (INR)": round(ridge_metrics["mae"], 2),
            "RMSE (INR)": round(ridge_metrics["rmse"], 2),
            "Better Than Baseline?": "YES" if ridge_metrics["mae"] < sn_metrics["mae"] else "NO"
        },
        {
            "Model Name": "Seasonal Naive Baseline",
            "Model Type": "Rule Baseline",
            "MAE (INR)": round(sn_metrics["mae"], 2),
            "RMSE (INR)": round(sn_metrics["rmse"], 2),
            "Better Than Baseline?": "Reference Baseline"
        },
        {
            "Model Name": "Moving Average Baseline",
            "Model Type": "Statistical Baseline",
            "MAE (INR)": round(ma_metrics["mae"], 2),
            "RMSE (INR)": round(ma_metrics["rmse"], 2),
            "Better Than Baseline?": "Reference Baseline"
        }
    ]

    test_results_df = test_df[[
        "atm_id", "atm_name", "date_value", "day_of_week_name", "withdrawal_amount_inr"
    ]].copy()
    test_results_df["predicted_ml_rf"] = np.round(ml_preds, 2)
    test_results_df["predicted_seasonal_naive"] = np.round(sn_preds, 2)
    test_results_df["error_ml_rf"] = np.round(test_results_df["predicted_ml_rf"] - test_results_df["withdrawal_amount_inr"], 2)

    return {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_start_date": str(train_df["date_value"].min()),
        "train_end_date": str(train_df["date_value"].max()),
        "test_start_date": str(test_df["date_value"].min()),
        "test_end_date": str(test_df["date_value"].max()),
        "comparison_table": pd.DataFrame(comparison_rows),
        "test_predictions": test_results_df,
        "kpi_05_pass": ml_metrics["mae"] < sn_metrics["mae"],
        "trained_ml_model": ml_model
    }


def predict_single_atm_demand(
    atm_id: str,
    target_date: Union[date, str],
    facts_df: pd.DataFrame,
    atms_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
    trained_model: Optional[CashDemandMLForecaster] = None
) -> Dict[str, Any]:
    """Generate future cash demand prediction for a single ATM (BR-06, OQ-06)."""
    if isinstance(target_date, str):
        target_date = datetime.fromisoformat(target_date.strip()).date()

    t_key = date_to_key(target_date)
    atm_row = atms_df[atms_df["atm_id"] == atm_id]
    if atm_row.empty:
        return {"status": "ERROR", "message": f"ATM ID '{atm_id}' not found."}

    atm_name = atm_row.iloc[0]["atm_name"]
    area_name = atm_row.iloc[0]["area_name"]
    site_type = atm_row.iloc[0]["site_type"]
    is_active = atm_row.iloc[0].get("is_active", 1)

    atm_history = facts_df[facts_df["atm_id"] == atm_id]
    if len(atm_history) < 3:
        return {
            "status": "UNAVAILABLE",
            "atm_id": atm_id,
            "atm_name": atm_name,
            "target_date": str(target_date),
            "message": f"Insufficient historical observations for {atm_id} ({len(atm_history)} found, minimum 3 required). Demand estimate unavailable per BR-06."
        }

    cal_row = calendar_df[calendar_df["date_key"] == t_key]
    if cal_row.empty:
        cal_dict = {
            "date_key": t_key,
            "date_value": target_date,
            "day_of_week_num": target_date.isoweekday(),
            "day_of_week_name": target_date.strftime("%A"),
            "month_num": target_date.month,
            "month_name": target_date.strftime("%B"),
            "is_weekend": int(target_date.weekday() >= 5),
            "is_holiday": 0,
            "season_name": "Summer" if target_date.month in (3,4,5,6) else ("Monsoon" if target_date.month in (7,8,9) else "Winter")
        }
    else:
        cal_dict = cal_row.iloc[0].to_dict()

    input_row = pd.DataFrame([{
        "atm_id": atm_id,
        "atm_name": atm_name,
        "site_type": site_type,
        "date_value": target_date,
        "day_of_week_num": cal_dict["day_of_week_num"],
        "day_of_week_name": cal_dict["day_of_week_name"],
        "month_num": cal_dict["month_num"],
        "month_name": cal_dict["month_name"],
        "season_name": cal_dict["season_name"],
        "is_weekend": cal_dict["is_weekend"],
        "is_holiday": cal_dict.get("is_holiday", 0)
    }])

    if trained_model is None:
        trained_model = CashDemandMLForecaster().fit(facts_df)

    pred_val = float(trained_model.predict(input_row)[0])
    pred_val = round(max(0.0, pred_val), 2)
    hist_avg = float(atm_history["withdrawal_amount_inr"].mean())
    ratio = (pred_val / hist_avg) if hist_avg > 0 else 1.0

    return {
        "status": "SUCCESS",
        "atm_id": atm_id,
        "atm_name": atm_name,
        "area_name": area_name,
        "site_type": site_type,
        "is_active": is_active,
        "target_date": str(target_date),
        "target_date_key": t_key,
        "day_of_week_name": cal_dict["day_of_week_name"],
        "month_name": cal_dict["month_name"],
        "season_name": cal_dict["season_name"],
        "predicted_demand_inr": pred_val,
        "historical_avg_inr": round(hist_avg, 2),
        "ratio_to_history": round(ratio, 2),
        "model_name": "Random Forest Regressor (ML)",
        "model_version": "v1.0-rf-prod",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "disclaimer": "Decision-support estimate based on synthetic data. Operations supervisor retains final replenishment approval."
    }


def predict_network_demand(
    target_date: Union[date, str],
    facts_df: pd.DataFrame,
    atms_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
    trained_model: Optional[CashDemandMLForecaster] = None
) -> Dict[str, Any]:
    """Calculate aggregate predicted cash demand across all eligible ATMs (BR-10, OQ-10)."""
    if isinstance(target_date, str):
        target_date = datetime.fromisoformat(target_date.strip()).date()

    if trained_model is None:
        trained_model = CashDemandMLForecaster().fit(facts_df)

    included_atms = []
    excluded_atms = []
    atm_predictions = []

    for _, row in atms_df.iterrows():
        a_id = row["atm_id"]
        if row.get("is_active", 1) == 0:
            excluded_atms.append({"atm_id": a_id, "reason": "ATM is marked inactive in ATM Master"})
            continue

        res = predict_single_atm_demand(
            atm_id=a_id,
            target_date=target_date,
            facts_df=facts_df,
            atms_df=atms_df,
            calendar_df=calendar_df,
            trained_model=trained_model
        )

        if res["status"] == "SUCCESS":
            included_atms.append(a_id)
            atm_predictions.append({
                "atm_id": a_id,
                "atm_name": res["atm_name"],
                "area_name": res["area_name"],
                "site_type": res["site_type"],
                "predicted_withdrawal_inr": res["predicted_demand_inr"],
                "historical_avg_inr": res["historical_avg_inr"]
            })
        else:
            excluded_atms.append({"atm_id": a_id, "reason": res["message"]})

    preds_df = pd.DataFrame(atm_predictions)
    total_network = float(preds_df["predicted_withdrawal_inr"].sum()) if not preds_df.empty else 0.0

    return {
        "target_date": str(target_date),
        "total_network_demand_inr": round(total_network, 2),
        "total_atms_in_network": len(atms_df),
        "included_atms_count": len(included_atms),
        "excluded_atms_count": len(excluded_atms),
        "predictions_table": preds_df,
        "exclusions_table": pd.DataFrame(excluded_atms),
        "model_name": "Random Forest Regressor (ML)",
        "model_version": "v1.0-rf-prod",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
