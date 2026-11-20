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
    render_empty_state, render_top_nav, render_bottom_nav,
    safe_page_link, apply_chart_theme
)
from src.utils import format_inr, format_number

try:
    st.set_page_config(page_title="Overview - ATM Analytics", page_icon="📊", layout="wide")
except Exception:
    pass

try:
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()
except Exception as exc:
    st.error(f"❌ Database error loading overview data: {exc}")
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

render_header("Overview & Operational KPIs", "High-level summary of ATM cash usage and network demand")
render_top_nav("1. Overview & KPIs")


if filtered_df.empty:
    render_empty_state("No withdrawal records found for the selected filter combination.")
else:
    # Core KPI Cards
    tot_withdrawn = calculate_total_withdrawal(filtered_df)
    avg_daily = calculate_average_daily_withdrawal(filtered_df)
    tot_txns = int(filtered_df["transaction_count"].sum()) if "transaction_count" in filtered_df.columns and not filtered_df.empty else 0
    atms_covered = filtered_df["atm_id"].nunique()
    tot_replenished = float(filtered_df["replenished_amount_inr"].dropna().sum()) if "replenished_amount_inr" in filtered_df.columns else 0.0

    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        render_kpi_card("Total Withdrawn", format_inr(tot_withdrawn, compact=True), f"Sum over {len(filtered_df)} observed days")
    with k2:
        render_kpi_card("Avg Daily Withdrawal", format_inr(avg_daily, compact=True), "Mean of observed ATM-days")
    with k3:
        render_kpi_card("Total Transactions", f"{tot_txns:,} Txns", "Customer ATM cash withdrawals")
    with k4:
        render_kpi_card("ATMs Covered", f"{atms_covered} ATMs", f"Out of {len(atms_df)} total network ATMs")
    with k5:
        render_kpi_card("Total Replenished", format_inr(tot_replenished, compact=True), "Cash loaded in selected window")

    st.markdown("---")
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("### 📈 Daily Withdrawal Volume & 7-Day Moving Average")
        daily_trend = filtered_df.groupby("date_value").agg(
            total_withdrawn=("withdrawal_amount_inr", "sum"),
            avg_withdrawn=("withdrawal_amount_inr", "mean"),
            reporting_atms=("atm_id", "count")
        ).reset_index()
        daily_trend["date_value"] = pd.to_datetime(daily_trend["date_value"])
        daily_trend = daily_trend.sort_values("date_value")
        daily_trend["7D_MA"] = daily_trend["total_withdrawn"].rolling(7, min_periods=1).mean()

        fig_line = go.Figure()
        fig_line.add_trace(go.Bar(
            x=daily_trend["date_value"],
            y=daily_trend["total_withdrawn"],
            name="Daily Cash Demand",
            marker_color="#93C5FD",
            opacity=0.70,
            customdata=daily_trend[["avg_withdrawn", "reporting_atms"]].values,
            hovertemplate="<b>Date:</b> %{x|%d %b %Y}<br><b>Total Demand:</b> ₹%{y:,.0f}<br><b>Avg / ATM:</b> ₹%{customdata[0]:,.0f}<br><b>Active Reporting ATMs:</b> %{customdata[1]}<extra></extra>"
        ))
        fig_line.add_trace(go.Scatter(
            x=daily_trend["date_value"],
            y=daily_trend["7D_MA"],
            name="7-Day Moving Avg",
            line=dict(color="#0F766E", width=3.5),
            mode="lines",
            hovertemplate="<b>7-Day Moving Avg:</b> ₹%{y:,.0f}<extra></extra>"
        ))
        apply_chart_theme(
            fig_line,
            height=430,
            xaxis_title="Calendar Date",
            yaxis_title="Total Demand (₹ INR)"
        )
        st.plotly_chart(fig_line, use_container_width=True)
        st.caption("💡 *Network aggregate demand reflects reporting cohort size (26 ATMs on 01 Jan 2024, 32 on 30 Dec 2025 vs. 1–5 ATMs on intermediate dates). Average per-ATM demand remains stable (~₹47k/ATM/day).*")

    with col_right:
        st.markdown("### 🏆 Top ATMs by Usage (OQ-05)")
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
        fig_bar.update_traces(
            texttemplate='₹%{x:,.0f}',
            textposition='inside',
            textfont=dict(size=12, color="white", family="'Segoe UI', sans-serif"),
            hovertemplate="<b>%{y}</b><br>Total Demand: ₹%{x:,.0f}<extra></extra>"
        )
        apply_chart_theme(
            fig_bar,
            height=430,
            xaxis_title="Total Cash Withdrawn (₹ INR)",
            yaxis_title="",
            show_legend=False
        )
        fig_bar.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Comprehensive ATM Usage & Ranking Summary")
    summary_table = get_atm_rankings(filtered_df, atms_df)[[
        "rank", "atm_id", "atm_name", "area_name", "site_type",
        "total_withdrawn", "avg_daily_withdrawal", "observation_count"
    ]].copy()
    summary_table["total_withdrawn"] = summary_table["total_withdrawn"].apply(lambda v: format_inr(v))
    summary_table["avg_daily_withdrawal"] = summary_table["avg_daily_withdrawal"].apply(lambda v: format_inr(v))
    st.dataframe(summary_table, use_container_width=True, height=320)

render_bottom_nav(
    prev_page=("app.py", "Home Hub", "🏠"),
    next_page=("pages/2_Trend_Analysis.py", "2. Trend Analysis", "📈")
)

