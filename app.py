"""
ATM Cash Demand Prediction — Main Application Entry Point.
Streamlit Multipage Hub (BUILD-07, BUILD-08, Step 12 UI Framework).
Student: Lavi Tewari | Roll No: 2503201450083 | MCA Data Analytics, ABES
Mentor: Kalpana Dwivedi
"""
import sys
from pathlib import Path
from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Ensure project root is prioritized in sys.path for Cloud environments
_ROOT_DIR = Path(__file__).resolve().parent
if str(_ROOT_DIR) not in sys.path or sys.path[0] != str(_ROOT_DIR):
    sys.path.insert(0, str(_ROOT_DIR))

from src.data_loader import load_atm_master, load_date_dim, load_daily_fact
from src.analysis import (
    calculate_total_withdrawal, calculate_average_daily_withdrawal,
    get_atm_rankings, apply_filters
)
from src.ui import (
    render_header, render_kpi_card, init_shared_filters,
    safe_page_link, ensure_pages_registered, apply_chart_theme
)

from src.utils import format_inr, format_number

st.set_page_config(
    page_title="ATM Cash Demand Prediction",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Guarantee multi-page navigation registry is initialized with url_pathname
ensure_pages_registered()


def render_home_hub():
    """Render the central executive Home Hub dashboard with KPIs, trend charts, and module launchers."""
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()

    # Initialize shared filters in sidebar
    filters = init_shared_filters(atms_df, calendar_df)

    render_header(
        "ATM Cash Demand Prediction & Replenishment Analytics",
        "Executive Operational Analytics & Decision-Support Hub | ABES Engineering College"
    )

    # Top Level Operational KPIs
    filtered_facts = apply_filters(
        facts_df,
        atm_id=filters["atm_id"],
        start_date=filters["start_date"],
        end_date=filters["end_date"],
        region=filters["region"],
        site_type=filters["site_type"]
    )

    tot_withdrawn = calculate_total_withdrawal(filtered_facts)
    avg_daily = calculate_average_daily_withdrawal(filtered_facts)
    tot_txns = int(filtered_facts["transaction_count"].sum()) if "transaction_count" in filtered_facts.columns and not filtered_facts.empty else 0
    active_count = int(atms_df["is_active"].sum()) if "is_active" in atms_df.columns else len(atms_df)

    # 4 Executive KPI Cards
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Total Cash Withdrawn", format_inr(tot_withdrawn, compact=True), f"Sum over {len(filtered_facts)} observed days (OQ-01)")
    with k2:
        render_kpi_card("Avg Daily Withdrawal", format_inr(avg_daily, compact=True), "Arithmetic mean of observed days (OQ-02)")
    with k3:
        render_kpi_card("Total Transactions", f"{tot_txns:,} Txns", "Customer ATM cash withdrawals")
    with k4:
        render_kpi_card("Active Network ATMs", f"{active_count} / {len(atms_df)} Machines", f"{round(active_count/len(atms_df)*100, 1)}% network active")

    st.markdown("---")

    # Executive Analytical Visualizations
    st.subheader("📈 Executive Network Overview & Analytics")
    if filtered_facts.empty:
        st.warning("No records match the current filter selection. Adjust sidebar filters to view analytical charts.")
    else:
        col_chart1, col_chart2 = st.columns([3, 2])
        with col_chart1:
            st.markdown("### 📈 7-Day Moving Average & Network Demand Trajectory")
            daily_trend = filtered_facts.groupby("date_value")["withdrawal_amount_inr"].sum().reset_index()
            daily_trend["date_value"] = pd.to_datetime(daily_trend["date_value"])
            daily_trend = daily_trend.sort_values("date_value")
            daily_trend["7D_MA"] = daily_trend["withdrawal_amount_inr"].rolling(7, min_periods=1).mean()

            fig_exec = go.Figure()
            fig_exec.add_trace(go.Bar(
                x=daily_trend["date_value"],
                y=daily_trend["withdrawal_amount_inr"],
                name="Daily Cash Demand",
                marker_color="#93C5FD",
                opacity=0.65,
                hovertemplate="<b>Date:</b> %{x|%d %b %Y}<br><b>Daily Demand:</b> ₹%{y:,.0f}<extra></extra>"
            ))
            fig_exec.add_trace(go.Scatter(
                x=daily_trend["date_value"],
                y=daily_trend["7D_MA"],
                name="7-Day Moving Average",
                line=dict(color="#0F766E", width=3.5),
                mode="lines",
                hovertemplate="<b>7-Day Moving Avg:</b> ₹%{y:,.0f}<extra></extra>"
            ))
            apply_chart_theme(
                fig_exec,
                height=400,
                xaxis_title="Observation Date",
                yaxis_title="Total Demand (₹ INR)"
            )
            st.plotly_chart(fig_exec, use_container_width=True)

        with col_chart2:
            st.markdown("### 🏢 Cash Demand Distribution by Site Type")
            site_summary = filtered_facts.groupby("site_type")["withdrawal_amount_inr"].sum().reset_index()
            fig_pie = px.pie(
                site_summary,
                values="withdrawal_amount_inr",
                names="site_type",
                color_discrete_sequence=px.colors.qualitative.Dark24,
                hole=0.4
            )
            fig_pie.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate="<b>%{label}</b><br>Demand: ₹%{value:,.0f} (%{percent})<extra></extra>"
            )
            apply_chart_theme(
                fig_pie,
                height=400,
                show_legend=False
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.subheader("Explore Analytics Workspace Modules")
    st.markdown("Navigate to detailed analytical modules via the **left sidebar** or click below:")

    p_col1, p_col2 = st.columns(2)

    with p_col1:
        st.markdown("#### 📊 Operational Analytics")
        with st.container(border=True):
            safe_page_link(overview_page, label="1. Overview & KPIs", icon="📊", use_container_width=True)
            st.caption("Network-wide total withdrawals, 7-day moving average trend, and top ATM rankings.")
        with st.container(border=True):
            safe_page_link(trend_page, label="2. Trend Analysis", icon="📈", use_container_width=True)
            st.caption("Day-of-week patterns, monthly trend curve, and seasonal shifts (Summer, Monsoon, Winter).")
        with st.container(border=True):
            safe_page_link(comparison_page, label="3. ATM Comparison", icon="🏆", use_container_width=True)
            st.caption("Benchmark and rank ATMs by historical volume, area, and site type.")
        with st.container(border=True):
            safe_page_link(eda_page, label="4. EDA & Statistics", icon="🔬", use_container_width=True)
            st.caption("Demand distributions, histograms, box plots, and correlation heatmaps.")

    with p_col2:
        st.markdown("#### 🔮 Predictive & Governance Modules")
        with st.container(border=True):
            safe_page_link(forecast_page, label="5. Forecast & Insights", icon="🔮", use_container_width=True)
            st.caption("Single ATM forecasts (OQ-06), network demand (OQ-10), holdout evaluation (OQ-07), and anomaly detection (OQ-08).")
        with st.container(border=True):
            safe_page_link(explorer_page, label="6. Data Explorer", icon="📁", use_container_width=True)
            st.caption("Filter, search, inspect, and export clean database records to CSV.")
        with st.container(border=True):
            safe_page_link(quality_page, label="7. Data Quality", icon="🔍", use_container_width=True)
            st.caption("Automated audits for foreign keys, missing values, duplicates, and range rules (BR-11).")
        with st.container(border=True):
            safe_page_link(about_page, label="8. About & Methodology", icon="ℹ️", use_container_width=True)
            st.caption("Academic context, holdout design, mathematical metrics, and limitations.")

    st.markdown("---")
    st.caption("Developed by **Lavi Tewari** (Roll No: 2503201450083) | Guided by **Kalpana Dwivedi** | MCA Data Analytics, ABES Engineering College")


# Configure unified Streamlit 1.57 multi-page navigation
home_page = st.Page(render_home_hub, title="Home Hub", icon="🏠", default=True, url_path="")
overview_page = st.Page("pages/1_Overview.py", title="1. Overview & KPIs", icon="📊", url_path="Overview")
trend_page = st.Page("pages/2_Trend_Analysis.py", title="2. Trend Analysis", icon="📈", url_path="Trend_Analysis")
comparison_page = st.Page("pages/3_ATM_Comparison.py", title="3. ATM Comparison", icon="🏆", url_path="ATM_Comparison")
eda_page = st.Page("pages/4_EDA_Statistics.py", title="4. EDA & Statistics", icon="🔬", url_path="EDA_Statistics")
forecast_page = st.Page("pages/5_Forecast_Insights.py", title="5. Forecast & Insights", icon="🔮", url_path="Forecast_Insights")
explorer_page = st.Page("pages/6_Data_Explorer.py", title="6. Data Explorer", icon="📁", url_path="Data_Explorer")
quality_page = st.Page("pages/7_Data_Quality.py", title="7. Data Quality", icon="🔍", url_path="Data_Quality")
about_page = st.Page("pages/8_About_Methodology.py", title="8. About & Methodology", icon="ℹ️", url_path="About_Methodology")

pg = st.navigation({
    "Analytics Hub": [home_page],
    "Operational Analytics": [overview_page, trend_page, comparison_page, eda_page],
    "Predictive & Governance": [forecast_page, explorer_page, quality_page, about_page]
})

pg.run()
