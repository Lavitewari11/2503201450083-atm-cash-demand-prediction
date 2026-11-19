"""
UI-01: Overview / KPIs Page (BUILD-08, US-01 to US-05, US-14).
Answers OQ-01, OQ-02, and supports OQ-05 at a glance.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_atm_master, load_date_dim, load_daily_fact
from src.analysis import calculate_total_withdrawal, calculate_average_daily_withdrawal, get_atm_rankings, apply_filters
from src.ui import (
    render_header, render_kpi_card, init_shared_filters,
    render_empty_state, render_top_nav, render_bottom_nav
)
from src.utils import format_inr, format_number

st.set_page_config(page_title="Overview - ATM Analytics", page_icon="📊", layout="wide")

try:
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()
except Exception as exc:
    st.error(f"❌ Database error loading overview data: {exc}")
    st.page_link("app.py", label="Return to Home Hub", icon="🏠")
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

render_header("Overview & Operational KPIs", "High-level summary of ATM cash usage and network demand")
render_top_nav("1. Overview & KPIs")


if filtered_df.empty:
    render_empty_state("No withdrawal records found for the selected filter combination.")
else:
    # 4 Core KPI Cards (UI-01 wireframe)
    tot_withdrawn = calculate_total_withdrawal(filtered_df)
    avg_daily = calculate_average_daily_withdrawal(filtered_df)
    atms_covered = filtered_df["atm_id"].nunique()
    tot_replenished = float(filtered_df["replenished_amount_inr"].dropna().sum()) if "replenished_amount_inr" in filtered_df.columns else 0.0

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Total Withdrawn", format_inr(tot_withdrawn, compact=True), f"Sum over {len(filtered_df)} observed days")
    with k2:
        render_kpi_card("Avg Daily Withdrawal", format_inr(avg_daily, compact=True), "Mean of observed ATM-days")
    with k3:
        render_kpi_card("ATMs Covered", f"{atms_covered} ATMs", f"Out of {len(atms_df)} total network ATMs")
    with k4:
        render_kpi_card("Total Replenished", format_inr(tot_replenished, compact=True), "Cash loaded in selected window")

    st.markdown("---")
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.subheader("Daily Withdrawal Trend")
        daily_trend = filtered_df.groupby("date_value")["withdrawal_amount_inr"].sum().reset_index()
        daily_trend["date_value"] = pd.to_datetime(daily_trend["date_value"])
        daily_trend["7D_MA"] = daily_trend["withdrawal_amount_inr"].rolling(7, min_periods=1).mean()

        fig_line = go.Figure()
        fig_line.add_trace(go.Bar(
            x=daily_trend["date_value"],
            y=daily_trend["withdrawal_amount_inr"],
            name="Daily Demand",
            marker_color="#93C5FD",
            opacity=0.65
        ))
        fig_line.add_trace(go.Scatter(
            x=daily_trend["date_value"],
            y=daily_trend["7D_MA"],
            name="7-Day Moving Avg",
            line=dict(color="#0F766E", width=2.5)
        ))
        fig_line.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=340,
            xaxis_title="Date",
            yaxis_title="Demand (INR ₹)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with col_right:
        st.subheader("Top ATMs by Usage (OQ-05)")
        rank_df = get_atm_rankings(filtered_df, atms_df).head(8)
        fig_bar = px.bar(
            rank_df,
            x="total_withdrawn",
            y="atm_name",
            orientation="h",
            color="site_type",
            labels={"total_withdrawn": "Total Withdrawn (₹)", "atm_name": "ATM Name"},
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_bar.update_layout(
            yaxis=dict(autorange="reversed"),
            margin=dict(l=20, r=20, t=20, b=20),
            height=340,
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader("ATM Summary Table")
    summary_table = get_atm_rankings(filtered_df, atms_df)[[
        "rank", "atm_id", "atm_name", "area_name", "site_type",
        "total_withdrawn", "avg_daily_withdrawal", "observation_count"
    ]].copy()
    summary_table["total_withdrawn"] = summary_table["total_withdrawn"].apply(lambda v: format_inr(v))
    summary_table["avg_daily_withdrawal"] = summary_table["avg_daily_withdrawal"].apply(lambda v: format_inr(v))
    st.dataframe(summary_table, use_container_width=True, height=260)

render_bottom_nav(
    prev_page=("app.py", "Home Hub", "🏠"),
    next_page=("pages/2_Trend_Analysis.py", "2. Trend Analysis", "📈")
)

