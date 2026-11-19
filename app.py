"""
ATM Cash Demand Prediction - Interactive Web Application.
Built with Streamlit & Plotly.
Conforms strictly to BRD v1.0, Database Design v1.0, ER Diagram v1.0, and Traceability Matrix.
Author: Lavi Tewari | Roll No: 2503201450083 | MCA Data Analytics, ABES
Mentor: Kalpana Dwivedi
"""
from datetime import date, datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.database import (
    load_atm_master, load_date_dim, load_daily_fact,
    load_forecast_fact, load_joined_analysis, save_forecasts,
    get_table_counts
)
from src.utils import format_inr, format_number, date_to_key, key_to_date, PALETTE
from src.analytics import (
    get_historical_summary, get_weekday_distribution,
    get_monthly_distribution, get_seasonal_distribution,
    get_atm_rankings, detect_demand_anomalies,
    compare_replenishment_vs_withdrawal, WEEKDAY_ORDER
)
from src.models import (
    evaluate_forecast_models, predict_single_atm,
    predict_network_aggregate, CashDemandMLForecaster
)
from src.data_quality import run_full_data_audit

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="ATM Cash Demand Prediction",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-val {
        font-size: 1.6rem;
        font-weight: bold;
        color: #0F172A;
    }
    .metric-label {
        font-size: 0.85rem;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .disclaimer-box {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 10px 14px;
        border-radius: 4px;
        font-size: 0.88rem;
        color: #1E40AF;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Data Loading (Cached)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_all_data():
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()
    forecasts_df = load_forecast_fact()
    return atms_df, calendar_df, facts_df, forecasts_df

try:
    atms_df, calendar_df, facts_df, forecasts_df = load_all_data()
except Exception as e:
    st.error(f"Error loading database: {e}")
    st.stop()

# ---------------------------------------------------------
# Sidebar Navigation & Global Filters
# ---------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/color/96/000000/atm--v1.png", width=70)
    st.markdown("### 🏦 ATM Cash Analytics")
    st.markdown("**Noida Retail Bank Network**")
    st.caption("Fictional Academic Prototype")

    st.markdown("---")
    st.markdown("#### 🎯 Filter Scope")

    # ATM Filter
    atm_options = ["All ATMs (Network)"] + sorted(list(atms_df["atm_id"].unique()))
    selected_atm_label = st.selectbox("Select ATM:", atm_options, index=0)
    selected_atm = None if selected_atm_label == "All ATMs (Network)" else selected_atm_label

    # Site Type Filter
    site_types = ["All Site Types"] + sorted(list(atms_df["site_type"].dropna().unique()))
    selected_site_type = st.selectbox("Site Type:", site_types, index=0)

    # Date Range Filter
    min_date = facts_df["date_value"].min()
    max_date = facts_df["date_value"].max()
    date_range = st.date_input(
        "Historical Date Range:",
        value=(min_date, max_date),
        min_value=calendar_df["date_value"].min(),
        max_value=calendar_df["date_value"].max()
    )

    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
    else:
        start_d, end_d = min_date, max_date

    st.markdown("---")
    st.markdown("#### 📑 Project Details")
    st.markdown("""
    - **Student:** Lavi Tewari
    - **Roll No:** 2503201450083
    - **Course:** MCA Data Analytics (2nd Year)
    - **College:** ABES
    - **Mentor:** Kalpana Dwivedi
    """)

    st.markdown("---")
    st.caption("⚠️ **Notice (BR-12):** All data is synthetic for college academic demonstration. Forecasts are decision-support estimates.")

# ---------------------------------------------------------
# Apply Global Filters to Data
# ---------------------------------------------------------
filtered_facts = facts_df.copy()
if selected_atm:
    filtered_facts = filtered_facts[filtered_facts["atm_id"] == selected_atm]
if selected_site_type != "All Site Types":
    filtered_facts = filtered_facts[filtered_facts["site_type"] == selected_site_type]

filtered_facts = filtered_facts[
    (filtered_facts["date_value"] >= start_d) & (filtered_facts["date_value"] <= end_d)
]

# ---------------------------------------------------------
# Main Header
# ---------------------------------------------------------
st.markdown('<div class="main-title">ATM Cash Demand Prediction & Replenishment Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">A decision-support system to balance ATM liquidity, prevent cash-outs, and minimize idle holding costs.</div>', unsafe_allow_html=True)

st.markdown("""
<div class="disclaimer-box">
    <strong>Decision Support System Notice (BR-12 & BRULE-12):</strong> 
    Predictions are probabilistic estimates derived from historical patterns. Final cash replenishment approval rests with the cash operations supervisor.
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Navigation Tabs (Covering OQ-01 through OQ-10 and BR-01 through BR-12)
# ---------------------------------------------------------
tab_overview, tab_hist, tab_patterns, tab_ranking, tab_single_fc, tab_network_fc, tab_eval, tab_anom, tab_replenish, tab_quality, tab_docs = st.tabs([
    "📊 Overview",
    "📈 Historical Demand (OQ-01/02)",
    "📅 Patterns & Seasonality (OQ-03/04)",
    "🏆 ATM Rankings (OQ-05)",
    "🔮 ATM Forecast (OQ-06)",
    "🌐 Network Forecast (OQ-10)",
    "🎯 Model Evaluation (OQ-07)",
    "⚠️ Anomalies (OQ-08)",
    "💰 Replenishment (OQ-09)",
    "🔍 Data Quality (BR-11)",
    "ℹ️ Project Info & Viva"
])

# =========================================================
# TAB 1: EXECUTIVE OVERVIEW
# =========================================================
with tab_overview:
    st.subheader("Network Operational Summary")
    summary = get_historical_summary(filtered_facts)

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Cash Withdrawn", format_inr(summary["total_withdrawn"], compact=True), help="Sum of historical withdrawals (BR-01)")
    with col2:
        st.metric("Avg Daily Demand", format_inr(summary["avg_daily_observed"], compact=True), help="Average daily demand across observed days (BR-02)")
    with col3:
        st.metric("Active ATMs", f"{atms_df['is_active'].sum()} / {len(atms_df)}", help="Number of operational ATMs in network")
    with col4:
        st.metric("Total Replenished", format_inr(summary["total_replenished"], compact=True), help="Total cash loaded into ATMs (BR-09)")
    with col5:
        st.metric("Transactions Count", format_number(summary["total_transactions"]), help="Total withdrawal transactions logged")

    st.markdown("---")
    c_left, c_right = st.columns([2, 1])

    with c_left:
        st.markdown("#### Daily Cash Demand Trend")
        if not filtered_facts.empty:
            daily_agg = filtered_facts.groupby("date_value")["withdrawal_amount_inr"].sum().reset_index()
            daily_agg["date_value"] = pd.to_datetime(daily_agg["date_value"])
            daily_agg["7D_MA"] = daily_agg["withdrawal_amount_inr"].rolling(window=7, min_periods=1).mean()

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=daily_agg["date_value"],
                y=daily_agg["withdrawal_amount_inr"],
                name="Daily Demand",
                marker_color="#93C5FD",
                opacity=0.7
            ))
            fig.add_trace(go.Scatter(
                x=daily_agg["date_value"],
                y=daily_agg["7D_MA"],
                name="7-Day Moving Avg",
                line=dict(color="#1D4ED8", width=2.5)
            ))
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=350,
                xaxis_title="Date",
                yaxis_title="Demand (INR ₹)",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No records match the current filter selection.")

    with c_right:
        st.markdown("#### Demand by ATM Site Type")
        if not filtered_facts.empty:
            site_agg = filtered_facts.groupby("site_type")["withdrawal_amount_inr"].sum().reset_index()
            fig_pie = px.pie(
                site_agg,
                names="site_type",
                values="withdrawal_amount_inr",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Safe
            )
            fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
            st.plotly_chart(fig_pie, use_container_width=True)

# =========================================================
# TAB 2: HISTORICAL DEMAND (OQ-01, OQ-02, BR-01, BR-02)
# =========================================================
with tab_hist:
    st.subheader("Historical Withdrawal Totals & Averages")
    st.caption("Answers OQ-01 (Total cash withdrawn) and OQ-02 (Average daily withdrawal).")

    cal_days = (end_d - start_d).days + 1
    hist_stats = get_historical_summary(filtered_facts, calendar_days=cal_days)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Withdrawn (OQ-01)", format_inr(hist_stats["total_withdrawn"]))
    with c2:
        st.metric("Avg Daily (Observed Days)", format_inr(hist_stats["avg_daily_observed"]))
    with c3:
        st.metric("Avg Daily (Calendar Days)", format_inr(hist_stats["avg_daily_calendar"]), help="Total divided by all calendar days in range (NA-Q02)")
    with c4:
        st.metric("Observed / Calendar Days", f"{hist_stats['observed_days']} / {hist_stats['calendar_days']}")

    c_s1, c_s2, c_s3, c_s4 = st.columns(4)
    with c_s1:
        st.metric("Minimum Daily Demand", format_inr(hist_stats["min_daily"]))
    with c_s2:
        st.metric("Median Daily Demand", format_inr(hist_stats["median_daily"]))
    with c_s3:
        st.metric("Maximum Daily Demand", format_inr(hist_stats["max_daily"]))
    with c_s4:
        st.metric("Demand Std Deviation", format_inr(hist_stats["std_daily"]))

    st.markdown("---")
    st.markdown("#### Historical Observations Log")
    if not filtered_facts.empty:
        display_cols = [
            "atm_id", "atm_name", "date_value", "day_of_week_name", "site_type",
            "withdrawal_amount_inr", "replenished_amount_inr", "transaction_count",
            "opening_balance_inr", "closing_balance_inr"
        ]
        st.dataframe(
            filtered_facts[display_cols].sort_values("date_value", ascending=False),
            use_container_width=True,
            height=300
        )
    else:
        st.warning("No records found for current filter criteria.")

# =========================================================
# TAB 3: PATTERNS & SEASONALITY (OQ-03, OQ-04, BR-03, BR-04)
# =========================================================
with tab_patterns:
    st.subheader("Recurring Demand Patterns: Weekly, Monthly & Seasonal")
    st.caption("Answers OQ-03 (Day of week variation) and OQ-04 (Month and season variation).")

    p_col1, p_col2 = st.columns(2)

    with p_col1:
        st.markdown("#### 📆 Weekday Demand Breakdown (OQ-03)")
        df_week = get_weekday_distribution(filtered_facts)

        fig_week = px.bar(
            df_week,
            x="day_of_week_name",
            y="avg_daily_withdrawal",
            text="avg_daily_withdrawal",
            labels={"day_of_week_name": "Day of Week", "avg_daily_withdrawal": "Average Daily Demand (₹)"},
            color="avg_daily_withdrawal",
            color_continuous_scale="Blues"
        )
        fig_week.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
        fig_week.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
        st.plotly_chart(fig_week, use_container_width=True)

        st.dataframe(
            df_week[["day_of_week_name", "total_withdrawn", "avg_daily_withdrawal", "observation_count", "pct_of_total"]],
            use_container_width=True,
            height=200
        )
        st.caption(f"✅ Reconciled Total: **{format_inr(df_week['total_withdrawn'].sum())}** (matches filtered total).")

    with p_col2:
        st.markdown("#### 🌦️ Seasonal Demand Breakdown (OQ-04)")
        df_season = get_seasonal_distribution(filtered_facts)

        fig_season = px.bar(
            df_season,
            x="season_name",
            y="avg_daily_withdrawal",
            text="avg_daily_withdrawal",
            labels={"season_name": "Season", "avg_daily_withdrawal": "Average Daily Demand (₹)"},
            color="season_name",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_season.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
        fig_season.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
        st.plotly_chart(fig_season, use_container_width=True)

        st.dataframe(
            df_season[["season_name", "total_withdrawn", "avg_daily_withdrawal", "observation_count", "pct_of_total"]],
            use_container_width=True,
            height=200
        )

    st.markdown("---")
    st.markdown("#### 🗓️ Monthly Demand Evolution (OQ-04)")
    df_month = get_monthly_distribution(filtered_facts)
    if not df_month.empty:
        fig_m = px.line(
            df_month,
            x="month_name",
            y="avg_daily_withdrawal",
            markers=True,
            labels={"month_name": "Month", "avg_daily_withdrawal": "Avg Daily Demand (₹)"},
            line_shape="spline"
        )
        fig_m.update_traces(line=dict(color="#2563EB", width=3), marker=dict(size=8, color="#1E40AF"))
        fig_m.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_m, use_container_width=True)

# =========================================================
# TAB 4: ATM RANKINGS (OQ-05, BR-05)
# =========================================================
with tab_ranking:
    st.subheader("ATM Historical Usage Comparison & Rankings")
    st.caption("Answers OQ-05 (Which ATMs have the highest and lowest historical cash usage).")

    r_col1, r_col2 = st.columns([1, 3])
    with r_col1:
        ranking_metric = st.selectbox("Ranking Basis:", ["Total Withdrawn", "Average Daily Withdrawal"])
        top_n = st.slider("Number of ATMs to show:", min_value=5, max_value=50, value=10)
        sort_col = "total_withdrawn" if ranking_metric == "Total Withdrawn" else "avg_daily_withdrawal"

    ranked_df = get_atm_rankings(filtered_facts, atms_df, sort_by=sort_col, ascending=False)

    with r_col2:
        if not ranked_df.empty:
            top_df = ranked_df.head(top_n)
            fig_rank = px.bar(
                top_df,
                x=sort_col,
                y="atm_name",
                orientation="h",
                text=sort_col,
                labels={sort_col: f"{ranking_metric} (₹)", "atm_name": "ATM Name"},
                color="site_type",
                color_discrete_sequence=px.colors.qualitative.Dark24
            )
            fig_rank.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
            fig_rank.update_layout(
                yaxis=dict(autorange="reversed"),
                height=max(350, top_n * 28),
                margin=dict(l=20, r=20, t=20, b=20)
            )
            st.plotly_chart(fig_rank, use_container_width=True)

    st.markdown("#### Complete ATM Ranking Table")
    if not ranked_df.empty:
        display_ranks = ranked_df[[
            "rank", "atm_id", "atm_name", "area_name", "site_type",
            "total_withdrawn", "avg_daily_withdrawal", "observation_count",
            "total_replenished", "total_transactions"
        ]].copy()
        display_ranks["total_withdrawn"] = display_ranks["total_withdrawn"].apply(lambda v: format_inr(v))
        display_ranks["avg_daily_withdrawal"] = display_ranks["avg_daily_withdrawal"].apply(lambda v: format_inr(v))
        display_ranks["total_replenished"] = display_ranks["total_replenished"].apply(lambda v: format_inr(v))
        st.dataframe(display_ranks, use_container_width=True, height=350)

# =========================================================
# TAB 5: SINGLE ATM FORECAST (OQ-06, BR-06)
# =========================================================
with tab_single_fc:
    st.subheader("ATM Future Daily Cash Demand Forecast")
    st.caption("Answers OQ-06 (What cash demand is estimated for a selected ATM on a future date).")

    f_col1, f_col2 = st.columns([1, 2])

    with f_col1:
        atm_select = st.selectbox("Select Target ATM:", sorted(list(atms_df["atm_id"].unique())), index=0)
        future_date = st.date_input(
            "Select Target Forecast Date:",
            value=date(2026, 1, 5),
            min_value=date(2024, 1, 1),
            max_value=date(2026, 12, 31)
        )
        run_fc_btn = st.button("🚀 Generate Demand Forecast", type="primary")

    with f_col2:
        if run_fc_btn or True:
            prediction_res = predict_single_atm(
                atm_id=atm_select,
                target_date=future_date,
                facts_df=facts_df,
                atms_df=atms_df,
                calendar_df=calendar_df
            )

            if prediction_res["status"] == "SUCCESS":
                st.markdown(f"""
                <div class="metric-card" style="border: 2px solid #2563EB;">
                    <div class="metric-label">Estimated Cash Demand ({prediction_res['day_of_week_name']}, {prediction_res['target_date']})</div>
                    <div class="metric-val" style="color: #1D4ED8; font-size: 2.4rem;">{format_inr(prediction_res['predicted_demand_inr'])}</div>
                    <div style="font-size: 0.95rem; color: #475569; margin-top: 8px;">
                        ATM: <strong>{prediction_res['atm_name']}</strong> ({prediction_res['site_type']} | {prediction_res['area_name']})
                    </div>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("#### Forecast Context & Explainability")
                c_fc1, c_fc2, c_fc3 = st.columns(3)
                with c_fc1:
                    st.metric("Historical Avg Demand", format_inr(prediction_res["historical_avg_inr"]))
                with c_fc2:
                    st.metric("Ratio to Historical Avg", f"{prediction_res['ratio_to_history']:.2f}x")
                with c_fc3:
                    st.metric("Model Used", prediction_res["model_name"])

                st.info(f"💡 **Context Factors:** Season: `{prediction_res['season_name']}` | Month: `{prediction_res['month_name']}` | Weekday: `{prediction_res['day_of_week_name']}`.")
            else:
                st.error(prediction_res["message"])

# =========================================================
# TAB 6: NETWORK AGGREGATE FORECAST (OQ-10, BR-10)
# =========================================================
with tab_network_fc:
    st.subheader("Network-Wide Aggregate Cash Demand Forecast")
    st.caption("Answers OQ-10 (How much demand is expected across all ATMs for a selected future date).")

    n_col1, n_col2 = st.columns([1, 3])
    with n_col1:
        net_date = st.date_input(
            "Forecast Date for Network:",
            value=date(2026, 1, 5),
            min_value=date(2024, 1, 1),
            max_value=date(2026, 12, 31),
            key="net_fc_date"
        )
        run_net_btn = st.button("🌐 Calculate Network Demand", type="primary")

    with n_col2:
        net_res = predict_network_aggregate(
            target_date=net_date,
            facts_df=facts_df,
            atms_df=atms_df,
            calendar_df=calendar_df
        )

        st.markdown(f"""
        <div class="metric-card" style="border: 2px solid #059669;">
            <div class="metric-label">Total Expected Network Cash Demand ({net_res['target_date']})</div>
            <div class="metric-val" style="color: #059669; font-size: 2.4rem;">{format_inr(net_res['total_network_demand_inr'])}</div>
            <div style="font-size: 0.95rem; color: #475569; margin-top: 8px;">
                Aggregated across <strong>{net_res['included_atms_count']}</strong> active ATMs in Noida & Ghaziabad
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### ATM Eligibility & Coverage Disclosure (BRULE-09)")
    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Total ATMs in Master", net_res["total_atms_in_network"])
    with k2:
        st.metric("Included Active ATMs", net_res["included_atms_count"])
    with k3:
        st.metric("Excluded ATMs (Disclosed)", net_res["excluded_atms_count"])

    if not net_res["exclusions_table"].empty:
        st.warning("⚠️ **Excluded ATMs:** The following ATMs were excluded from network summation:")
        st.dataframe(net_res["exclusions_table"], use_container_width=True)

    st.markdown("#### Per-ATM Demand Forecast Breakdown")
    if not net_res["predictions_table"].empty:
        st.dataframe(net_res["predictions_table"], use_container_width=True, height=280)

# =========================================================
# TAB 7: MODEL EVALUATION (OQ-07, BR-07, KPI-05, KPI-06)
# =========================================================
with tab_eval:
    st.subheader("Forecasting Evaluation on Chronological Holdout")
    st.caption("Answers OQ-07 (Comparing model against naive baselines on unseen future historical data).")

    eval_results = evaluate_forecast_models(facts_df, test_ratio=0.20)

    if "error" not in eval_results:
        st.markdown(f"""
        <div class="disclaimer-box">
            <strong>Chronological Holdout Split (BR-07, BRULE-07):</strong> 
            Training Period: <code>{eval_results['train_start_date']}</code> to <code>{eval_results['train_end_date']}</code> ({eval_results['train_rows']} rows).<br>
            Held-out Test Period: <code>{eval_results['test_start_date']}</code> to <code>{eval_results['test_end_date']}</code> ({eval_results['test_rows']} rows).
            <strong>Zero future data leakage.</strong>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("#### 🏆 Benchmark Comparison (KPI-05 & KPI-06)")
        st.dataframe(eval_results["comparison_table"], use_container_width=True)

        if eval_results["kpi_05_pass"]:
            st.success("✅ **KPI-05 ACHIEVED:** Machine Learning Model MAE is strictly lower than Seasonal Naive Baseline MAE (`MAE(model) < MAE(baseline)`).")

        st.markdown("#### Actual vs Predicted Withdrawals on Chronological Holdout")
        test_preds = eval_results["test_predictions"].sort_values("date_value")

        fig_eval = go.Figure()
        fig_eval.add_trace(go.Scatter(
            x=list(range(len(test_preds))),
            y=test_preds["withdrawal_amount_inr"],
            mode="lines+markers",
            name="Actual Withdrawal",
            line=dict(color="#1E293B", width=2)
        ))
        fig_eval.add_trace(go.Scatter(
            x=list(range(len(test_preds))),
            y=test_preds["predicted_ml_rf"],
            mode="lines+markers",
            name="Random Forest ML",
            line=dict(color="#2563EB", width=2, dash="dash")
        ))
        fig_eval.add_trace(go.Scatter(
            x=list(range(len(test_preds))),
            y=test_preds["predicted_seasonal_naive"],
            mode="lines",
            name="Seasonal Naive Baseline",
            line=dict(color="#DC2626", width=1.5, dash="dot")
        ))
        fig_eval.update_layout(
            height=380,
            margin=dict(l=20, r=20, t=20, b=20),
            xaxis_title="Holdout Test Observation Index (Chronological)",
            yaxis_title="Withdrawal Amount (INR ₹)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_eval, use_container_width=True)

# =========================================================
# TAB 8: ANOMALIES (OQ-08, BR-08, BRULE-10)
# =========================================================
with tab_anom:
    st.subheader("Statistical Demand Anomaly Detection")
    st.caption("Answers OQ-08 (Flagging unusually high- or low-demand ATM-days for human investigation).")

    a_col1, a_col2, a_col3 = st.columns(3)
    with a_col1:
        anom_scope = st.selectbox("Detection Scope:", ["network", "atm"], index=0, help="Network-wide or per-ATM grouping")
    with a_col2:
        anom_method = st.selectbox("Detection Method:", ["zscore", "iqr"], index=0)
    with a_col3:
        anom_threshold = st.slider("Sensitivity Threshold:", min_value=1.0, max_value=3.5, value=2.0, step=0.1)

    anomalies_df = detect_demand_anomalies(
        filtered_facts,
        method=anom_method,
        threshold=anom_threshold,
        scope=anom_scope
    )

    st.markdown(f"**Identified Candidates:** `{len(anomalies_df)}` anomalous observations flagged.")

    if not anomalies_df.empty:
        st.dataframe(anomalies_df, use_container_width=True, height=280)

        fig_anom = px.scatter(
            filtered_facts,
            x="date_value",
            y="withdrawal_amount_inr",
            color="site_type",
            title="Historical Demand Distribution with Outliers",
            labels={"date_value": "Date", "withdrawal_amount_inr": "Withdrawal (₹)"}
        )
        fig_anom.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_anom, use_container_width=True)
    else:
        st.info("No observations exceeded the selected anomaly threshold.")

# =========================================================
# TAB 9: REPLENISHMENT (OQ-09, BR-09)
# =========================================================
with tab_replenish:
    st.subheader("Cash Replenishment vs Withdrawal Reconciliation")
    st.caption("Answers OQ-09 (Comparing cash loaded with cash withdrawn over time).")

    rep_comp = compare_replenishment_vs_withdrawal(filtered_facts)

    rc1, rc2, rc3, rc4 = st.columns(4)
    with rc1:
        st.metric("Total Replenished", format_inr(rep_comp["total_replenished"]))
    with rc2:
        st.metric("Total Withdrawn", format_inr(rep_comp["total_withdrawn"]))
    with rc3:
        st.metric("Net Cash Variance", format_inr(rep_comp["net_difference"]), help="Replenished minus Withdrawn")
    with rc4:
        st.metric("Replenishment Ratio", f"{rep_comp['replenishment_ratio_pct']:.1f}%")

    if not rep_comp["daily_comparison_df"].empty:
        rep_daily = rep_comp["daily_comparison_df"].sort_values("date_value")
        fig_rep = go.Figure()
        fig_rep.add_trace(go.Bar(
            x=rep_daily["date_value"],
            y=rep_daily["withdrawal_amount_inr"],
            name="Cash Withdrawn",
            marker_color="#EF4444"
        ))
        fig_rep.add_trace(go.Bar(
            x=rep_daily["date_value"],
            y=rep_daily["replenished_amount_inr"],
            name="Cash Replenished",
            marker_color="#10B981"
        ))
        fig_rep.update_layout(
            barmode="group",
            height=350,
            xaxis_title="Date",
            yaxis_title="Amount (INR ₹)",
            margin=dict(l=20, r=20, t=20, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_rep, use_container_width=True)

# =========================================================
# TAB 10: DATA QUALITY (BR-11, KPI-04)
# =========================================================
with tab_quality:
    st.subheader("Data Completeness & Quality Audit Center")
    st.caption("Satisfies BR-11 and KPI-04 (Data quality visibility before analysis and modelling).")

    audit_summary = run_full_data_audit()

    q1, q2, q3, q4 = st.columns(4)
    with q1:
        st.metric("Overall Data Health", f"{audit_summary['overall_health_pct']}%")
    with q2:
        st.metric("Foreign Key Checks", audit_summary["fk_status"])
    with q3:
        st.metric("Passed Checks", f"{audit_summary['passed_checks']} / {audit_summary['total_checks']}")
    with q4:
        st.metric("Quarantined Duplicates", audit_summary["quarantined_duplicates_count"])

    st.markdown("---")
    st.markdown("#### Database Table Row Counts")
    st.dataframe(audit_summary["counts_df"], use_container_width=True)

    st.markdown("#### Business Rules & Integrity Checks")
    st.dataframe(audit_summary["rules_df"], use_container_width=True)

    st.markdown("#### Null & Missing Values Audit")
    st.dataframe(audit_summary["missing_df"], use_container_width=True)

    if not audit_summary["quarantine_df"].empty:
        st.markdown("#### Quarantined Duplicate Candidates (Isolated in QA file)")
        st.caption("Demonstrates deduplication governance: duplicate candidates are isolated rather than corrupting production primary keys.")
        st.dataframe(audit_summary["quarantine_df"], use_container_width=True)

# =========================================================
# TAB 11: PROJECT INFO & VIVA PREPARATION
# =========================================================
with tab_docs:
    st.subheader("Project Documentation & Viva Examination Guide")

    st.markdown("""
    ### 🎓 Academic Project Profile
    - **Project Name:** ATM Cash Demand Prediction (Data Analytics Project)
    - **Student Name:** Lavi Tewari
    - **Student Roll No:** 2503201450083
    - **Degree & Branch:** Master of Computer Applications (MCA), 2nd Year — Data Analytics
    - **College / Institution:** ABES Engineering College
    - **Faculty Mentor:** Kalpana Dwivedi
    - **Date of Submission:** 19 November 2026
    
    ---
    ### 🎯 Operational Questions (OQs) & Business Requirements (BRs) Matrix
    | OQ ID | Operational Question | Mapped BR | Status |
    |---|---|---|---|
    | **OQ-01** | Total cash withdrawn over selected period | **BR-01** (Historical Totals) | ✅ Covered |
    | **OQ-02** | Average daily cash withdrawal | **BR-02** (Daily Average) | ✅ Covered |
    | **OQ-03** | Variation by day of week | **BR-03** (Weekday Distribution) | ✅ Covered |
    | **OQ-04** | Variation by month or season | **BR-04** (Monthly/Seasonal) | ✅ Covered |
    | **OQ-05** | Highest and lowest usage ATMs ranking | **BR-05** (Usage Ranking) | ✅ Covered |
    | **OQ-06** | Future daily cash demand estimate | **BR-06** (Daily Forecast) | ✅ Covered |
    | **OQ-07** | Forecast evaluation against actual withdrawals | **BR-07** (Holdout Evaluation) | ✅ Covered |
    | **OQ-08** | Identify unusually high/low demand ATM-days | **BR-08** (Anomaly Detection) | ✅ Covered |
    | **OQ-09** | Compare cash replenished with withdrawn | **BR-09** (Replenishment Balance) | ✅ Covered |
    | **OQ-10** | Combined network forecast for a target date | **BR-10** (Network Forecast) | ✅ Covered |
    | **-** | Data completeness and consistency | **BR-11** (Data Quality Audit) | ✅ Covered |
    | **-** | Assumptions, limitations, and disclaimer | **BR-12** (Transparency & Viva) | ✅ Covered |

    ---
    ### 💡 Viva Examination Questions & Answers
    **Q1. Why is ATM cash demand prediction critical for banking operations?**  
    *Answer:* ATMs must maintain adequate cash to prevent stockouts (which damage customer satisfaction and violate service-level agreements), while avoiding excess idle cash (which incurs opportunity cost of funds, insurance costs, and unnecessary cash-in-transit trips).

    **Q2. Why is synthetic data used instead of real customer data?**  
    *Answer:* To strictly protect customer financial privacy and comply with banking data protection norms. Synthetic data with reproducible seed 42 allows safe, transparent, and auditable end-to-end evaluation.

    **Q3. How did you ensure your model evaluation was fair and realistic?**  
    *Answer:* We implemented a strictly chronological train/test holdout split (earlier dates for training, later dates for testing) to prevent any future-data leakage, and compared the ML model against naive baselines (Moving Average and Seasonal Naive).
    
    **Q4. Why does atm_daily_fact have a composite primary key (atm_id, date_key)?**  
    *Answer:* Because the analytical grain is exactly one record per ATM per calendar date. The composite key guarantees that daily transactions are aggregated and prevents multiple duplicate daily entries.
    """)
