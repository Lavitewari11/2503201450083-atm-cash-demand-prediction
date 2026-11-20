"""
UI-02: Trend Analysis Page (BUILD-09, US-02, US-06, US-07).
Answers OQ-03 (Weekday patterns) and OQ-04 (Monthly and seasonal patterns).
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.data_loader import load_atm_master, load_date_dim, load_daily_fact
from src.analysis import (
    apply_filters, get_weekday_distribution,
    get_monthly_distribution, get_seasonal_distribution
)
from src.insights import generate_weekday_insight
from src.ui import (
    render_header, render_insight_box, init_shared_filters,
    render_empty_state, render_top_nav, render_bottom_nav,
    safe_page_link, apply_chart_theme
)
from src.utils import format_inr

try:
    st.set_page_config(page_title="Trend Analysis - ATM Analytics", page_icon="📈", layout="wide")
except Exception:
    pass

try:
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()
except Exception as exc:
    st.error(f"❌ Database error loading trend data: {exc}")
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

render_header("Trend & Pattern Analysis", "Multi-frequency analysis of daily, weekday, monthly, and seasonal cash demand variations")
render_top_nav("2. Trend Analysis")


if filtered_df.empty:
    render_empty_state("No data available for trend analysis with current filter selection.")
else:
    # 1. Daily Withdrawal Trend (Dual-Trace: Daily Volume + 7-Day Moving Average)
    col_t1, col_t2 = st.columns([3, 2])
    with col_t1:
        st.markdown("### 📈 Daily Cash Demand & 7-Day Moving Average Trajectory")
    with col_t2:
        metric_mode = st.radio(
            "Daily Demand Metric:",
            ["Average Demand per ATM (Normalized)", "Network Total Demand (Aggregate Sum)"],
            horizontal=True,
            key="trend_metric_toggle",
            help="Normalized view shows average daily cash demand per reporting ATM (ideal for analyzing true customer withdrawal patterns across variable reporting cohorts). Aggregate Sum shows total network cash volume."
        )

    daily_ts = filtered_df.groupby("date_value").agg(
        total_withdrawn=("withdrawal_amount_inr", "sum"),
        avg_withdrawn=("withdrawal_amount_inr", "mean"),
        reporting_atms=("atm_id", "count")
    ).reset_index()
    daily_ts["date_value"] = pd.to_datetime(daily_ts["date_value"])
    daily_ts = daily_ts.sort_values("date_value")
    daily_ts["7D_MA_total"] = daily_ts["total_withdrawn"].rolling(7, min_periods=1).mean()
    daily_ts["7D_MA_avg"] = daily_ts["avg_withdrawn"].rolling(7, min_periods=1).mean()

    is_avg_mode = (metric_mode == "Average Demand per ATM (Normalized)")
    y_data = daily_ts["avg_withdrawn"] if is_avg_mode else daily_ts["total_withdrawn"]
    ma_data = daily_ts["7D_MA_avg"] if is_avg_mode else daily_ts["7D_MA_total"]
    bar_name = "Avg Daily Demand / ATM" if is_avg_mode else "Daily Network Volume"
    line_name = "7-Day Moving Avg (Norm.)" if is_avg_mode else "7-Day Moving Avg (Total)"
    yaxis_title = "Average Demand (₹ INR / ATM)" if is_avg_mode else "Total Demand (₹ INR)"
    chart_title = "Daily Average Cash Demand per Reporting ATM (7-Day Smoothed Trend)" if is_avg_mode else "Network Total Daily Cash Withdrawal Trajectory (7-Day Smoothed Trend)"

    fig_daily = go.Figure()
    if is_avg_mode:
        fig_daily.add_trace(go.Bar(
            x=daily_ts["date_value"],
            y=y_data,
            name=bar_name,
            marker_color="#93C5FD",
            opacity=0.75,
            customdata=daily_ts[["total_withdrawn", "reporting_atms"]].values,
            hovertemplate="<b>Date:</b> %{x|%d %b %Y}<br><b>Avg Demand / ATM:</b> ₹%{y:,.0f}<br><b>Total Demand:</b> ₹%{customdata[0]:,.0f}<br><b>Active Reporting ATMs:</b> %{customdata[1]}<extra></extra>"
        ))
        fig_daily.add_trace(go.Scatter(
            x=daily_ts["date_value"],
            y=ma_data,
            name=line_name,
            line=dict(color="#0F766E", width=3.5),
            mode="lines",
            hovertemplate="<b>7-Day Moving Avg:</b> ₹%{y:,.0f}/ATM<extra></extra>"
        ))
    else:
        fig_daily.add_trace(go.Bar(
            x=daily_ts["date_value"],
            y=y_data,
            name=bar_name,
            marker_color="#93C5FD",
            opacity=0.75,
            customdata=daily_ts[["avg_withdrawn", "reporting_atms"]].values,
            hovertemplate="<b>Date:</b> %{x|%d %b %Y}<br><b>Total Demand:</b> ₹%{y:,.0f}<br><b>Avg Demand / ATM:</b> ₹%{customdata[0]:,.0f}<br><b>Active Reporting ATMs:</b> %{customdata[1]}<extra></extra>"
        ))
        fig_daily.add_trace(go.Scatter(
            x=daily_ts["date_value"],
            y=ma_data,
            name=line_name,
            line=dict(color="#0F766E", width=3.5),
            mode="lines",
            hovertemplate="<b>7-Day Moving Avg:</b> ₹%{y:,.0f}<extra></extra>"
        ))

    apply_chart_theme(
        fig_daily,
        height=460,
        title=chart_title,
        xaxis_title="Observation Calendar Date",
        yaxis_title=yaxis_title
    )
    st.plotly_chart(fig_daily, use_container_width=True)
    st.caption("💡 **Cohort Concurrency Note:** In this benchmark dataset, reporting ATM concurrency varies by date (e.g. 26 ATMs on 01 Jan 2024 and 32 ATMs on 30 Dec 2025 during baseline audits vs. 1–5 ATMs on intermediate dates). The **Average Demand per ATM** view normalizes for cohort size, revealing the stable underlying customer withdrawal velocity (network average: ₹47,403/ATM/day).")

    st.markdown("---")
    df_week = get_weekday_distribution(filtered_df)
    insight = generate_weekday_insight(df_week)
    render_insight_box(insight["finding"], insight["evidence"], insight["caveat"])

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📆 Weekday Demand Pattern (OQ-03)")
        fig_w = px.bar(
            df_week,
            x="day_of_week_name",
            y="avg_daily_withdrawal",
            text="avg_daily_withdrawal",
            category_orders={"day_of_week_name": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]},
            labels={"day_of_week_name": "Day of Week", "avg_daily_withdrawal": "Avg Daily Withdrawal (₹)"},
            color="avg_daily_withdrawal",
            color_continuous_scale="Teal"
        )
        fig_w.update_traces(
            texttemplate='₹%{text:,.0f}',
            textposition='outside',
            textfont=dict(size=13, family="'Segoe UI', sans-serif"),
            hovertemplate="<b>%{x}</b><br>Average Demand: ₹%{y:,.0f}<extra></extra>"
        )
        apply_chart_theme(
            fig_w,
            height=390,
            xaxis_title="Day of Week",
            yaxis_title="Average Daily Demand (₹ INR)",
            show_legend=False
        )
        st.plotly_chart(fig_w, use_container_width=True)
        st.caption(f"Reconciled Network Filtered Demand: **{format_inr(df_week['total_withdrawn'].sum())}** across {int(df_week['observation_count'].sum())} observations.")

    with col2:
        st.markdown("### 🌦️ Seasonal Demand Pattern (OQ-04)")
        df_season = get_seasonal_distribution(filtered_df)
        if not df_season.empty:
            fig_s = px.bar(
                df_season,
                x="season_name",
                y="avg_daily_withdrawal",
                text="avg_daily_withdrawal",
                labels={"season_name": "Season Name", "avg_daily_withdrawal": "Avg Daily Withdrawal (₹)"},
                color="season_name",
                color_discrete_sequence=["#14B8A6", "#38BDF8", "#F59E0B", "#64748B"]
            )
            fig_s.update_traces(
                texttemplate='₹%{text:,.0f}',
                textposition='outside',
                textfont=dict(size=13, family="'Segoe UI', sans-serif"),
                hovertemplate="<b>%{x}</b><br>Average Demand: ₹%{y:,.0f}<extra></extra>"
            )
            apply_chart_theme(
                fig_s,
                height=390,
                xaxis_title="Climatic Season",
                yaxis_title="Average Daily Demand (₹ INR)",
                show_legend=False
            )
            st.plotly_chart(fig_s, use_container_width=True)
            st.caption(f"Peak Season Demand: **{df_season.iloc[0]['season_name']}** ({format_inr(df_season.iloc[0]['avg_daily_withdrawal'])}/day average).")

    st.markdown("---")
    st.markdown("### 🗓️ Monthly Withdrawal Trajectory (OQ-04)")
    df_month = get_monthly_distribution(filtered_df)
    if not df_month.empty:
        fig_m = px.line(
            df_month,
            x="month_name",
            y="avg_daily_withdrawal",
            markers=True,
            labels={"month_name": "Calendar Month", "avg_daily_withdrawal": "Average Daily Demand (₹)"}
        )
        fig_m.update_traces(
            line=dict(color="#0F766E", width=3.5),
            marker=dict(size=10, color="#115E59", line=dict(width=2, color="#FFFFFF")),
            hovertemplate="<b>%{x}</b><br>Average Daily Demand: ₹%{y:,.0f}<br>Total Withdrawn: ₹%{customdata[0]:,.0f}<br>Sample Observations: %{customdata[1]} records<extra></extra>",
            customdata=df_month[["total_withdrawn", "observation_count"]].values
        )
        apply_chart_theme(
            fig_m,
            height=410,
            title="Monthly Cash Demand Trajectory Across Benchmark Periods",
            xaxis_title="Calendar Month",
            yaxis_title="Average Daily Demand (₹ INR)",
            show_legend=False
        )
        st.plotly_chart(fig_m, use_container_width=True)
        st.caption("ℹ️ *Data Governance Disclosure (BR-04): The 250 benchmark observations in the dataset were sampled across 5 seasonal audit windows (Winter Baseline in January, Summer Peak in June/July, and Year-End/Holiday in December). Intermediate months contain no observation records in the database, preserving data authenticity under Business Rule BR-04 without artificial zero-filling.*")

render_bottom_nav(
    prev_page=("pages/1_Overview.py", "1. Overview & KPIs", "📊"),
    next_page=("pages/3_ATM_Comparison.py", "3. ATM Comparison", "🏆")
)

