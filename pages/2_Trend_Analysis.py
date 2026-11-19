"""
UI-02: Trend Analysis Page (BUILD-09, US-02, US-06, US-07).
Answers OQ-03 (Weekday patterns) and OQ-04 (Monthly and seasonal patterns).
"""
import streamlit as st
import plotly.express as px

from src.data_loader import load_atm_master, load_date_dim, load_daily_fact
from src.analysis import (
    apply_filters, get_weekday_distribution,
    get_monthly_distribution, get_seasonal_distribution
)
from src.insights import generate_weekday_insight
from src.ui import (
    render_header, render_insight_box, init_shared_filters,
    render_empty_state, render_top_nav, render_bottom_nav
)
from src.utils import format_inr

st.set_page_config(page_title="Trend Analysis - ATM Analytics", page_icon="📈", layout="wide")

try:
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()
except Exception as exc:
    st.error(f"❌ Database error loading trend data: {exc}")
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

render_header("Trend & Pattern Analysis", "Analyzing weekday, monthly, and seasonal demand variations")
render_top_nav("2. Trend Analysis")


if filtered_df.empty:
    render_empty_state("No data available for trend analysis with current filter selection.")
else:
    df_week = get_weekday_distribution(filtered_df)
    insight = generate_weekday_insight(df_week)
    render_insight_box(insight["finding"], insight["evidence"], insight["caveat"])

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📆 Weekday Demand Pattern (OQ-03)")
        fig_w = px.bar(
            df_week,
            x="day_of_week_name",
            y="avg_daily_withdrawal",
            text="avg_daily_withdrawal",
            labels={"day_of_week_name": "Day of Week", "avg_daily_withdrawal": "Avg Daily Withdrawal (₹)"},
            color="avg_daily_withdrawal",
            color_continuous_scale="Teal"
        )
        fig_w.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
        fig_w.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
        st.plotly_chart(fig_w, use_container_width=True)

        st.caption(f"Reconciled Filtered Total: **{format_inr(df_week['total_withdrawn'].sum())}**")

    with col2:
        st.subheader("🌦️ Seasonal Demand Pattern (OQ-04)")
        df_season = get_seasonal_distribution(filtered_df)
        if not df_season.empty:
            fig_s = px.bar(
                df_season,
                x="season_name",
                y="avg_daily_withdrawal",
                text="avg_daily_withdrawal",
                labels={"season_name": "Season", "avg_daily_withdrawal": "Avg Daily Withdrawal (₹)"},
                color="season_name",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_s.update_traces(texttemplate='₹%{text:,.0f}', textposition='outside')
            fig_s.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
            st.plotly_chart(fig_s, use_container_width=True)

    st.markdown("---")
    st.subheader("🗓️ Monthly Withdrawal Trend (OQ-04)")
    df_month = get_monthly_distribution(filtered_df)
    if not df_month.empty:
        fig_m = px.line(
            df_month,
            x="month_name",
            y="avg_daily_withdrawal",
            markers=True,
            labels={"month_name": "Month", "avg_daily_withdrawal": "Average Daily Demand (₹)"}
        )
        fig_m.update_traces(line=dict(color="#0F766E", width=3), marker=dict(size=8, color="#115E59"))
        fig_m.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_m, use_container_width=True)

render_bottom_nav(
    prev_page=("pages/1_Overview.py", "1. Overview & KPIs", "📊"),
    next_page=("pages/3_ATM_Comparison.py", "3. ATM Comparison", "🏆")
)

