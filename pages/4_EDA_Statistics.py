"""
UI-04: EDA & Statistics Page (BUILD-11, US-02, US-06, US-07).
Provides histograms, box plots by weekday, descriptive statistics, and correlation heatmaps.
"""
import streamlit as st
import plotly.express as px

from src.data_loader import load_atm_master, load_date_dim, load_daily_fact
from src.analysis import apply_filters, descriptive_statistics
from src.ui import (
    render_header, init_shared_filters, render_empty_state,
    render_top_nav, render_bottom_nav, safe_page_link, apply_chart_theme
)
from src.utils import format_inr

try:
    st.set_page_config(page_title="EDA & Statistics - ATM Analytics", page_icon="🔬", layout="wide")
except Exception:
    pass

try:
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()
except Exception as exc:
    st.error(f"❌ Database error loading statistics data: {exc}")
    safe_page_link("app.py", label="Return to Home Hub", icon="🏠")
    st.stop()


filters = init_shared_filters(atms_df, calendar_df)
filtered_df = apply_filters(
    facts_df,
    atm_id=filters["atm_id"],
    start_date=filters["start_date"],
    end_date=filters["end_date"],
    region=filters["region"],
    site_type=filters["site_type"]
)

render_header("Exploratory Data Analysis & Statistics", "Statistical distributions, demand dispersion, and multi-metric correlations")
render_top_nav("4. EDA & Statistics")


if filtered_df.empty:
    render_empty_state("No data available for statistical exploration with current filters.")
else:
    stats = descriptive_statistics(filtered_df["withdrawal_amount_inr"])

    st.markdown("### 📊 Parametric & Non-Parametric Demand Statistics")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Observation Count", f"{stats['count']:,}")
        st.metric("Mean Demand", format_inr(stats["mean"]))
    with c2:
        st.metric("Standard Deviation", format_inr(stats["std"]))
        st.metric("Median Demand", format_inr(stats["median"]))
    with c3:
        st.metric("25th Percentile (Q1)", format_inr(stats["q25"]))
        st.metric("75th Percentile (Q3)", format_inr(stats["q75"]))
    with c4:
        st.metric("Minimum Demand", format_inr(stats["min"]))
        st.metric("Maximum Demand", format_inr(stats["max"]))

    st.markdown("---")
    col_hist, col_box = st.columns(2)

    with col_hist:
        st.markdown("### 📉 Cash Demand Frequency Distribution")
        fig_hist = px.histogram(
            filtered_df,
            x="withdrawal_amount_inr",
            nbins=25,
            labels={"withdrawal_amount_inr": "Withdrawal Amount (₹)"},
            color_discrete_sequence=["#0F766E"]
        )
        apply_chart_theme(
            fig_hist,
            height=400,
            xaxis_title="Withdrawal Amount (₹ INR)",
            yaxis_title="Frequency (Observations)",
            show_legend=False
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_box:
        st.markdown("### 📦 Weekday Demand Distribution & Dispersion")
        fig_wbox = px.box(
            filtered_df,
            x="day_of_week_name",
            y="withdrawal_amount_inr",
            category_orders={"day_of_week_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            labels={"day_of_week_name": "Day of Week", "withdrawal_amount_inr": "Withdrawal (₹)"},
            color_discrete_sequence=["#0F766E"]
        )
        apply_chart_theme(
            fig_wbox,
            height=400,
            xaxis_title="Day of Week",
            yaxis_title="Daily Withdrawal (₹ INR)",
            show_legend=False
        )
        st.plotly_chart(fig_wbox, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🔗 Correlation Matrix across Banking Metrics")
    num_cols = ["withdrawal_amount_inr", "replenished_amount_inr", "transaction_count", "opening_balance_inr", "closing_balance_inr"]
    available_num = [c for c in num_cols if c in filtered_df.columns]
    if len(available_num) >= 2:
        corr = filtered_df[available_num].dropna().corr()
        fig_corr = px.imshow(
            corr,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            aspect="auto"
        )
        apply_chart_theme(
            fig_corr,
            height=430,
            show_legend=False
        )
        st.plotly_chart(fig_corr, use_container_width=True)

render_bottom_nav(
    prev_page=("pages/3_ATM_Comparison.py", "3. ATM Comparison", "🏆"),
    next_page=("pages/5_Forecast_Insights.py", "5. Forecast & Insights", "🔮")
)

