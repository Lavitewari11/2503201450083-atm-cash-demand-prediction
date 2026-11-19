"""
Machine Learning & Forecasting Engine.
Satisfies BR-06, BR-07, BR-10 (OQ-06, OQ-07, OQ-10).
Implements chronological holdout evaluation, baseline benchmarks, and feature-engineered ML models.
"""
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import date, datetime
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.utils import date_to_key, key_to_date


def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Extract calendar and historical features for demand forecasting.
    Guarantees no future leakage.
    """
    df_feat = df.copy()

    # Derived calendar features
    if "date_value" in df_feat.columns:
        dates = pd.to_datetime(df_feat["date_value"])
        df_feat["day_of_month"] = dates.dt.day
        df_feat["day_of_week_num"] = dates.dt.dayofweek + 1  # 1 = Mon, 7 = Sun
        df_feat["month_num"] = dates.dt.month
        df_feat["is_weekend"] = (dates.dt.dayofweek >= 5).astype(int)
        df_feat["is_month_end"] = (dates.dt.day >= 25).astype(int)

    # Encode season
    season_map = {"Summer": 1, "Monsoon": 2, "Winter": 3, "Other": 0}
    df_feat["season_code"] = df_feat["season_name"].map(season_map).fillna(0).astype(int)
    df_feat["holiday_code"] = df_feat["is_holiday"].fillna(0).astype(int)

    # ATM encoding (frequency / mean target encoding or one-hot / categorical codes)
    if "atm_id" in df_feat.columns:
        df_feat["atm_code"] = df_feat["atm_id"].astype("category").cat.codes

    # Site type encoding
    site_map = {"Branch": 1, "Market": 2, "Transit": 3, "Residential": 4, "Office": 5}
    if "site_type" in df_feat.columns:
        df_feat["site_code"] = df_feat["site_type"].map(site_map).fillna(0).astype(int)
    else:
        df_feat["site_code"] = 0

    feature_cols = [
        "atm_code", "site_code", "day_of_week_num", "month_num",
        "day_of_month", "season_code", "is_weekend", "is_month_end", "holiday_code"
    ]

    X = df_feat[feature_cols].copy()
    y = df_feat["withdrawal_amount_inr"].copy() if "withdrawal_amount_inr" in df_feat.columns else pd.Series(dtype=float)
    return X, y


class SeasonalNaiveBaseline:
    """Baseline Model: Predicts historical ATM-specific weekday average."""

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
    """Baseline Model: Predicts recent overall historical mean for ATM."""

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
    """Advanced Machine Learning Model: Feature-Engineered Random Forest Regressor."""

    def __init__(self, n_estimators: int = 100, random_state: int = 42):
        self.model = RandomForestRegressor(
            n_estimators=n_estimators,
            max_depth=10,
            min_samples_split=3,
            random_state=random_state
        )
        self.feature_names: List[str] = []

    def fit(self, train_df: pd.DataFrame) -> "CashDemandMLForecaster":
        X, y = prepare_features(train_df)
        self.feature_names = list(X.columns)
        self.model.fit(X, y)
        return self

    def predict(self, test_df: pd.DataFrame) -> np.ndarray:
        X, _ = prepare_features(test_df)
        preds = self.model.predict(X)
        return np.clip(preds, a_min=0.0, a_max=None)


def evaluate_forecast_models(
    facts_df: pd.DataFrame,
    test_ratio: float = 0.20
) -> Dict[str, Any]:
    """
    Evaluates forecast models on a strictly chronological holdout test set (BR-07, OQ-07, KPI-05, KPI-06).
    """
    if facts_df.empty or len(facts_df) < 15:
        return {"error": "Insufficient data to perform chronological evaluation."}

    # Sort strictly by date to ensure chronological integrity
    df_sorted = facts_df.sort_values(["date_key", "atm_id"]).reset_index(drop=True)

    unique_dates = df_sorted["date_key"].unique()
    split_idx = int(len(unique_dates) * (1 - test_ratio))
    split_date_key = unique_dates[split_idx]

    train_df = df_sorted[df_sorted["date_key"] < split_date_key].copy()
    test_df = df_sorted[df_sorted["date_key"] >= split_date_key].copy()

    if train_df.empty or test_df.empty:
        return {"error": "Train/test split produced an empty partition."}

    y_true = test_df["withdrawal_amount_inr"].values

    # 1. Seasonal Naive Baseline
    sn_model = SeasonalNaiveBaseline().fit(train_df)
    sn_preds = sn_model.predict(test_df)
    sn_mae = float(mean_absolute_error(y_true, sn_preds))
    sn_rmse = float(np.sqrt(mean_squared_error(y_true, sn_preds)))

    # 2. Moving Average Baseline
    ma_model = MovingAverageBaseline().fit(train_df)
    ma_preds = ma_model.predict(test_df)
    ma_mae = float(mean_absolute_error(y_true, ma_preds))
    ma_rmse = float(np.sqrt(mean_squared_error(y_true, ma_preds)))

    # 3. ML Model (Random Forest Regressor)
    ml_model = CashDemandMLForecaster().fit(train_df)
    ml_preds = ml_model.predict(test_df)
    ml_mae = float(mean_absolute_error(y_true, ml_preds))
    ml_rmse = float(np.sqrt(mean_squared_error(y_true, ml_preds)))

    # 4. Linear Ridge Model
    ridge = Ridge(alpha=1.0)
    X_train, y_train = prepare_features(train_df)
    X_test, _ = prepare_features(test_df)
    ridge.fit(X_train, y_train)
    ridge_preds = np.clip(ridge.predict(X_test), 0.0, None)
    ridge_mae = float(mean_absolute_error(y_true, ridge_preds))
    ridge_rmse = float(np.sqrt(mean_squared_error(y_true, ridge_preds)))

    # Metrics comparison table
    comparison_rows = [
        {
            "Model Name": "Random Forest Regressor (ML)",
            "Model Type": "Machine Learning",
            "MAE (INR)": round(ml_mae, 2),
            "RMSE (INR)": round(ml_rmse, 2),
            "Is Baseline": 0,
            "Better Than Naive Baseline?": "YES (Pass KPI-05)" if ml_mae < sn_mae else "NO"
        },
        {
            "Model Name": "Ridge Regression (Linear ML)",
            "Model Type": "Machine Learning",
            "MAE (INR)": round(ridge_mae, 2),
            "RMSE (INR)": round(ridge_rmse, 2),
            "Is Baseline": 0,
            "Better Than Naive Baseline?": "YES" if ridge_mae < sn_mae else "NO"
        },
        {
            "Model Name": "Seasonal Naive Baseline",
            "Model Type": "Rule-based Baseline",
            "MAE (INR)": round(sn_mae, 2),
            "RMSE (INR)": round(sn_rmse, 2),
            "Is Baseline": 1,
            "Better Than Naive Baseline?": "Reference Baseline"
        },
        {
            "Model Name": "Moving Average Baseline",
            "Model Type": "Statistical Baseline",
            "MAE (INR)": round(ma_mae, 2),
            "RMSE (INR)": round(ma_rmse, 2),
            "Is Baseline": 1,
            "Better Than Naive Baseline?": "Reference Baseline"
        }
    ]

    # Prepare detailed paired comparison dataframe for test period
    test_results_df = test_df[[
        "atm_id", "atm_name", "date_value", "day_of_week_name", "withdrawal_amount_inr"
    ]].copy()
    test_results_df["predicted_ml_rf"] = np.round(ml_preds, 2)
    test_results_df["predicted_seasonal_naive"] = np.round(sn_preds, 2)
    test_results_df["error_ml_rf"] = np.round(test_results_df["predicted_ml_rf"] - test_results_df["withdrawal_amount_inr"], 2)
    test_results_df["abs_error_ml_rf"] = np.abs(test_results_df["error_ml_rf"])

    return {
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_start_date": str(train_df["date_value"].min()),
        "train_end_date": str(train_df["date_value"].max()),
        "test_start_date": str(test_df["date_value"].min()),
        "test_end_date": str(test_df["date_value"].max()),
        "comparison_table": pd.DataFrame(comparison_rows),
        "test_predictions": test_results_df,
        "kpi_05_pass": ml_mae < sn_mae,
        "trained_ml_model": ml_model,
        "trained_sn_model": sn_model
    }


def predict_single_atm(
    atm_id: str,
    target_date: Union[date, str],
    facts_df: pd.DataFrame,
    atms_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
    trained_model: Optional[CashDemandMLForecaster] = None
) -> Dict[str, Any]:
    """
    Generate future cash demand prediction for a specific ATM and date (BR-06, OQ-06).
    Checks history requirement (minimum 3 observations).
    """
    if isinstance(target_date, str):
        target_date = datetime.fromisoformat(target_date.strip()).date()

    t_key = date_to_key(target_date)

    # Check ATM existence and history
    atm_row = atms_df[atms_df["atm_id"] == atm_id]
    if atm_row.empty:
        return {"status": "ERROR", "message": f"ATM ID '{atm_id}' not found in ATM master."}

    atm_name = atm_row.iloc[0]["atm_name"]
    area_name = atm_row.iloc[0]["area_name"]
    site_type = atm_row.iloc[0]["site_type"]
    is_active = atm_row.iloc[0]["is_active"]

    atm_history = facts_df[facts_df["atm_id"] == atm_id]
    if len(atm_history) < 3:
        return {
            "status": "UNAVAILABLE",
            "atm_id": atm_id,
            "atm_name": atm_name,
            "target_date": str(target_date),
            "message": f"Insufficient historical observations for {atm_id} ({len(atm_history)} found, minimum 3 required). Demand estimate unavailable per BR-06."
        }

    # Retrieve calendar attributes for target date
    cal_row = calendar_df[calendar_df["date_key"] == t_key]
    if cal_row.empty:
        # Fallback derive
        d_val = target_date
        cal_dict = {
            "date_key": t_key,
            "date_value": d_val,
            "day_of_week_num": d_val.isoweekday(),
            "day_of_week_name": d_val.strftime("%A"),
            "month_num": d_val.month,
            "month_name": d_val.strftime("%B"),
            "is_weekend": int(d_val.weekday() >= 5),
            "is_holiday": 0,
            "season_name": "Summer" if d_val.month in (3,4,5,6) else ("Monsoon" if d_val.month in (7,8,9) else "Winter")
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

    # Predict using trained ML model or fit on full history
    if trained_model is None:
        model = CashDemandMLForecaster().fit(facts_df)
    else:
        model = trained_model

    pred_val = float(model.predict(input_row)[0])
    pred_val = round(max(0.0, pred_val), 2)

    # Contextual explanation factors
    historical_avg = float(atm_history["withdrawal_amount_inr"].mean())
    ratio_to_avg = (pred_val / historical_avg) if historical_avg > 0 else 1.0

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
        "historical_avg_inr": round(historical_avg, 2),
        "ratio_to_history": round(ratio_to_avg, 2),
        "model_name": "Random Forest Regressor (ML)",
        "model_version": "v1.0-rf-prod",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "disclaimer": "Analytical decision-support estimate based on synthetic data. Replenishment team retains final approval authority (BR-12)."
    }


def predict_network_aggregate(
    target_date: Union[date, str],
    facts_df: pd.DataFrame,
    atms_df: pd.DataFrame,
    calendar_df: pd.DataFrame,
    trained_model: Optional[CashDemandMLForecaster] = None
) -> Dict[str, Any]:
    """
    Computes aggregate predicted cash demand across all eligible ATMs for a target date (BR-10, OQ-10).
    Discloses included and excluded ATM counts per BRULE-09.
    """
    if isinstance(target_date, str):
        target_date = datetime.fromisoformat(target_date.strip()).date()

    if trained_model is None:
        trained_model = CashDemandMLForecaster().fit(facts_df)

    included_atms = []
    excluded_atms = []
    atm_predictions = []

    for _, row in atms_df.iterrows():
        a_id = row["atm_id"]
        # Check active status
        if row.get("is_active", 1) == 0:
            excluded_atms.append({"atm_id": a_id, "reason": "ATM is marked inactive in ATM Master"})
            continue

        res = predict_single_atm(
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
    total_network_demand = float(preds_df["predicted_withdrawal_inr"].sum()) if not preds_df.empty else 0.0

    return {
        "target_date": str(target_date),
        "total_network_demand_inr": round(total_network_demand, 2),
        "total_atms_in_network": len(atms_df),
        "included_atms_count": len(included_atms),
        "excluded_atms_count": len(excluded_atms),
        "predictions_table": preds_df,
        "exclusions_table": pd.DataFrame(excluded_atms),
        "model_name": "Random Forest Regressor (ML)",
        "model_version": "v1.0-rf-prod",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
