"""
UI-05: Forecast & Insights Page (BUILD-12, US-08 to US-12, US-14).
Answers OQ-06 (ATM Forecast), OQ-07 (Evaluation), OQ-08 (Anomalies), OQ-09 (Replenishment), and OQ-10 (Network Demand).
"""
from datetime import date
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_atm_master, load_date_dim, load_daily_fact, load_forecast_fact
from src.analysis import apply_filters, detect_demand_anomalies, compare_replenishment_vs_withdrawal
from src.forecasting import (
    evaluate_chronological_holdout,
    predict_single_atm_demand,
    predict_network_demand,
    CashDemandMLForecaster
)
from src.insights import generate_replenishment_insight
from src.ui import (
    render_header, render_kpi_card, render_insight_box,
    init_shared_filters, render_empty_state, render_top_nav, render_bottom_nav,
    safe_page_link, apply_chart_theme
)
from src.utils import format_inr

try:
    st.set_page_config(page_title="Forecast & Insights - ATM Analytics", page_icon="🔮", layout="wide")
except Exception:
    pass

try:
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()
except Exception as exc:
    st.error(f"❌ Database error loading forecast data: {exc}")
    safe_page_link("app.py", label="Return to Home Hub", icon="🏠")
    st.stop()


@st.cache_resource(show_spinner="Fitting forecasting model...")
def get_cached_ml_model(data_fingerprint: str) -> CashDemandMLForecaster:
    """
    Fits and caches the Random Forest forecaster.
    Invalidated automatically if the underlying fact data fingerprint changes.
    """
    return CashDemandMLForecaster().fit(facts_df)


@st.cache_data(show_spinner="Evaluating holdout models...")
def get_cached_holdout_eval(data_fingerprint: str):
    """
    Caches chronological holdout evaluation results.
    Invalidated automatically if the underlying fact data fingerprint changes.
    """
    return evaluate_chronological_holdout(facts_df)


data_fingerprint = f"{len(facts_df)}_{facts_df['withdrawal_amount_inr'].sum():.2f}_{facts_df['date_key'].max()}"
cached_ml_model = get_cached_ml_model(data_fingerprint)

filters = init_shared_filters(atms_df, calendar_df)
filtered_df = apply_filters(
    facts_df,
    atm_id=filters["atm_id"],
    start_date=filters["start_date"],
    end_date=filters["end_date"],
    region=filters["region"],
    site_type=filters["site_type"]
)

render_header("Forecasting & Operational Insights", "Predictive cash demand estimates and model holdout evaluations")
render_top_nav("5. Forecast & Insights")


tab_single, tab_net, tab_eval, tab_anom, tab_replen = st.tabs([
    "🔮 Single ATM Forecast (OQ-06)",
    "🌐 Network Forecast (OQ-10)",
    "🎯 Model Evaluation (OQ-07)",
    "⚠️ Demand Anomalies (OQ-08)",
    "💰 Replenishment Balance (OQ-09)"
])

# 1. Single ATM Forecast
with tab_single:
    st.subheader("ATM Future Cash Demand Prediction")
    c1, c2 = st.columns([1, 2])
    with c1:
        atm_pick = st.selectbox("Select Target ATM:", sorted(atms_df["atm_id"].unique().tolist()), index=0, key="single_atm_select")
        fc_target_date = st.date_input("Target Date:", value=date(2026, 1, 5), key="single_fc_date")
        run_btn = st.button("Generate Forecast", type="primary", key="btn_run_single")

    with c2:
        res = predict_single_atm_demand(atm_pick, fc_target_date, facts_df, atms_df, calendar_df, trained_model=cached_ml_model)
        if res["status"] == "SUCCESS":
            render_kpi_card(
                f"Estimated Demand ({res['day_of_week_name']}, {res['target_date']})",
                format_inr(res["predicted_demand_inr"]),
                f"ATM: {res['atm_name']} ({res['site_type']}) | Model: {res['model_name']}"
            )
            st.info(f"💡 **Context:** Historical Avg: **{format_inr(res['historical_avg_inr'])}** (Ratio: {res['ratio_to_history']:.2f}x) | Season: `{res['season_name']}` | Month: `{res['month_name']}`.")
        else:
            st.error(res["message"])

# 2. Network Forecast
with tab_net:
    st.subheader("Network-Wide Aggregate Cash Demand (OQ-10)")
    net_date = st.date_input("Forecast Date for Network:", value=date(2026, 1, 5), key="net_date_pick")
    net_res = predict_network_demand(net_date, facts_df, atms_df, calendar_df, trained_model=cached_ml_model)

    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card(f"Total Network Demand ({net_res['target_date']})", format_inr(net_res["total_network_demand_inr"], compact=True), "Sum across eligible active ATMs")
    with k2:
        render_kpi_card("Active ATMs Included", f"{net_res['included_atms_count']} / {net_res['total_atms_in_network']}", "Active machines with valid history")
    with k3:
        render_kpi_card("Excluded ATMs", f"{net_res['excluded_atms_count']} Machines", "Disclosed per BRULE-09")

    if not net_res["exclusions_table"].empty:
        st.warning("⚠️ **Excluded ATMs:** The following ATMs were excluded from network summation:")
        st.dataframe(net_res["exclusions_table"], use_container_width=True)

    st.subheader("ATM-Wise Forecast Breakdown")
    st.dataframe(net_res["predictions_table"], use_container_width=True, height=260)

# 3. Model Evaluation
with tab_eval:
    st.subheader("Chronological Holdout Model Evaluation (OQ-07, BR-07, KPI-05)")
    eval_res = get_cached_holdout_eval(data_fingerprint)
    if "error" not in eval_res:
        st.caption(f"Training Window: `{eval_res['train_start_date']}` to `{eval_res['train_end_date']}` | Test Window: `{eval_res['test_start_date']}` to `{eval_res['test_end_date']}`. Zero data leakage.")
        st.dataframe(eval_res["comparison_table"], use_container_width=True)
        if eval_res["kpi_05_pass"]:
            st.success("✅ **KPI-05 Verified:** Machine Learning Model MAE is lower than Seasonal Naive Baseline MAE (`MAE(model) < MAE(baseline)`).")

        st.markdown("### 🎯 Actual vs Predicted Withdrawals on Unseen Holdout Set")
        preds = eval_res["test_predictions"].sort_values("date_value")
        fig_eval = go.Figure()
        fig_eval.add_trace(go.Scatter(
            x=list(range(len(preds))),
            y=preds["withdrawal_amount_inr"],
            name="Actual Customer Demand",
            line=dict(color="#0F172A", width=2.5),
            hovertemplate="<b>Actual:</b> ₹%{y:,.0f}<extra></extra>"
        ))
        fig_eval.add_trace(go.Scatter(
            x=list(range(len(preds))),
            y=preds["predicted_ml_rf"],
            name="Random Forest ML Model",
            line=dict(color="#0F766E", width=3, dash="dash"),
            hovertemplate="<b>ML Predicted:</b> ₹%{y:,.0f}<extra></extra>"
        ))
        fig_eval.add_trace(go.Scatter(
            x=list(range(len(preds))),
            y=preds["predicted_seasonal_naive"],
            name="Seasonal Naive Baseline",
            line=dict(color="#DC2626", width=2, dash="dot"),
            hovertemplate="<b>Naive Baseline:</b> ₹%{y:,.0f}<extra></extra>"
        ))
        apply_chart_theme(
            fig_eval,
            height=430,
            xaxis_title="Chronological Holdout Observation Sequence (Zero Data Leakage)",
            yaxis_title="Cash Withdrawal (₹ INR)"
        )
        st.plotly_chart(fig_eval, use_container_width=True)

# 4. Demand Anomalies
with tab_anom:
    st.subheader("Statistical Demand Anomaly Detection (OQ-08, BR-08)")
    anom_thresh = st.slider("Anomaly Sensitivity Threshold (|Z|):", 1.0, 3.5, 2.0, 0.1, key="anom_thresh")
    anomalies_df = detect_demand_anomalies(filtered_df, method="zscore", threshold=anom_thresh)
    st.caption(f"Identified `{len(anomalies_df)}` candidate exception days. Flagged for review, not confirmed fraud (BRULE-10).")
    if not anomalies_df.empty:
        st.dataframe(anomalies_df, use_container_width=True, height=280)

# 5. Replenishment
with tab_replen:
    st.subheader("Cash Replenishment Reconciliation (OQ-09, BR-09)")
    rep_comp = compare_replenishment_vs_withdrawal(filtered_df)
    rep_insight = generate_replenishment_insight(rep_comp)
    render_insight_box(rep_insight["finding"], rep_insight["evidence"], rep_insight["caveat"])

    net_diff = rep_comp["net_difference"]
    net_sign = "+" if net_diff > 0 else ""
    r1, r2, r3 = st.columns(3)
    with r1:
        render_kpi_card(
            "Total Cash Replenished",
            format_inr(rep_comp["total_replenished"], compact=True),
            f"Exact: {format_inr(rep_comp['total_replenished'])}"
        )
    with r2:
        render_kpi_card(
            "Total Cash Withdrawn",
            format_inr(rep_comp["total_withdrawn"], compact=True),
            f"Exact: {format_inr(rep_comp['total_withdrawn'])}"
        )
    with r3:
        render_kpi_card(
            "Net Cash Flow",
            f"{net_sign}{format_inr(net_diff, compact=True)}",
            f"Exact: {net_sign}{format_inr(net_diff)} | Ratio: {rep_comp['replenishment_ratio_pct']:.1f}%"
        )

render_bottom_nav(
    prev_page=("pages/4_EDA_Statistics.py", "4. EDA & Statistics", "🔬"),
    next_page=("pages/6_Data_Explorer.py", "6. Data Explorer", "📁")
)

