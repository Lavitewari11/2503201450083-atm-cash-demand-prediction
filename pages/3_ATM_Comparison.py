"""
UI-03: ATM Comparison Page (BUILD-10, US-02, US-05).
Answers OQ-05 (Ranking and comparing historical ATM cash usage).
"""
import streamlit as st
import plotly.express as px

from src.data_loader import load_atm_master, load_date_dim, load_daily_fact
from src.analysis import apply_filters, get_atm_rankings
from src.insights import generate_ranking_insight
from src.ui import (
    render_header, render_kpi_card, render_insight_box,
    init_shared_filters, render_empty_state, render_top_nav, render_bottom_nav,
    safe_page_link, apply_chart_theme
)
from src.utils import format_inr

try:
    st.set_page_config(page_title="ATM Comparison - ATM Analytics", page_icon="🏆", layout="wide")
except Exception:
    pass

try:
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()
except Exception as exc:
    st.error(f"❌ Database error loading comparison data: {exc}")
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

render_header("ATM Historical Comparison", "Benchmarking performance and usage across the ATM network")
render_top_nav("3. ATM Comparison")


if filtered_df.empty:
    render_empty_state("No ATM observations match the selected criteria.")
else:
    ranked_df = get_atm_rankings(filtered_df, atms_df, sort_by="total_withdrawn", ascending=False)
    insight = generate_ranking_insight(ranked_df)
    render_insight_box(insight["finding"], insight["evidence"], insight["caveat"])

    st.markdown("---")
    # Top KPIs
    top_atm = ranked_df.iloc[0]
    low_atm = ranked_df.iloc[-1]

    k1, k2, k3 = st.columns(3)
    with k1:
        render_kpi_card("ATMs Covered", f"{len(ranked_df)} Machines", f"{round(len(ranked_df)/len(atms_df)*100, 1)}% of network")
    with k2:
        render_kpi_card("Highest Usage ATM", f"{top_atm['atm_id']}", f"{format_inr(top_atm['total_withdrawn'])} total")
    with k3:
        render_kpi_card("Lowest Usage ATM", f"{low_atm['atm_id']}", f"{format_inr(low_atm['total_withdrawn'])} total")

    st.markdown("---")
    col_chart, col_box = st.columns([3, 2])

    with col_chart:
        st.markdown("### 🏆 ATM Demand Rankings (OQ-05)")
        top_n = st.slider("Number of ATMs to display:", 5, min(50, len(ranked_df)), 15)
        fig_h = px.bar(
            ranked_df.head(top_n),
            x="total_withdrawn",
            y="atm_name",
            orientation="h",
            color="site_type",
            labels={"total_withdrawn": "Total Withdrawn (₹)", "atm_name": "ATM Name"},
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_h.update_traces(
            texttemplate='₹%{x:,.0f}',
            textposition='inside',
            textfont=dict(size=12, color="white", family="'Segoe UI', sans-serif"),
            hovertemplate="<b>%{y}</b><br>Total Withdrawn: ₹%{x:,.0f}<extra></extra>"
        )
        apply_chart_theme(
            fig_h,
            height=max(420, top_n * 27),
            xaxis_title="Total Cash Withdrawn (₹ INR)",
            yaxis_title="",
            show_legend=False
        )
        fig_h.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_h, use_container_width=True)

    with col_box:
        st.markdown("### 📦 Daily Demand Dispersion")
        top_ids = ranked_df.head(top_n)["atm_id"].tolist()
        box_data = filtered_df[filtered_df["atm_id"].isin(top_ids)]
        fig_box = px.box(
            box_data,
            x="atm_id",
            y="withdrawal_amount_inr",
            labels={"atm_id": "ATM", "withdrawal_amount_inr": "Daily Withdrawal (₹)"},
            color="site_type"
        )
        apply_chart_theme(
            fig_box,
            height=max(420, top_n * 27),
            xaxis_title="ATM Machine ID",
            yaxis_title="Daily Withdrawal (₹ INR)",
            show_legend=False
        )
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📍 Area & Site Type Dimension Comparison")
    col_area, col_site = st.columns(2)

    with col_area:
        st.markdown("##### Total Demand by Area / Region")
        area_agg = filtered_df.groupby("area_name")["withdrawal_amount_inr"].agg(["sum", "mean"]).reset_index()
        area_agg.columns = ["area_name", "total_withdrawn", "avg_daily"]
        area_agg = area_agg.sort_values("total_withdrawn", ascending=False)
        fig_area = px.bar(
            area_agg,
            x="area_name",
            y="total_withdrawn",
            text="total_withdrawn",
            labels={"area_name": "Area", "total_withdrawn": "Total Withdrawn (₹)"},
            color="total_withdrawn",
            color_continuous_scale="Viridis"
        )
        fig_area.update_traces(
            texttemplate='₹%{text:,.0f}',
            textposition='outside',
            textfont=dict(size=12.5, family="'Segoe UI', sans-serif"),
            hovertemplate="<b>%{x}</b><br>Total Demand: ₹%{y:,.0f}<extra></extra>"
        )
        apply_chart_theme(
            fig_area,
            height=390,
            xaxis_title="Geographical Area",
            yaxis_title="Total Withdrawn (₹ INR)",
            show_legend=False
        )
        st.plotly_chart(fig_area, use_container_width=True)

    with col_site:
        st.markdown("##### Total Demand by Site Type")
        site_agg = filtered_df.groupby("site_type")["withdrawal_amount_inr"].agg(["sum", "mean"]).reset_index()
        site_agg.columns = ["site_type", "total_withdrawn", "avg_daily"]
        site_agg = site_agg.sort_values("total_withdrawn", ascending=False)
        fig_site = px.bar(
            site_agg,
            x="site_type",
            y="total_withdrawn",
            text="total_withdrawn",
            labels={"site_type": "Site Type", "total_withdrawn": "Total Withdrawn (₹)"},
            color="site_type",
            color_discrete_sequence=px.colors.qualitative.Dark24
        )
        fig_site.update_traces(
            texttemplate='₹%{text:,.0f}',
            textposition='outside',
            textfont=dict(size=12.5, family="'Segoe UI', sans-serif"),
            hovertemplate="<b>%{x}</b><br>Total Demand: ₹%{y:,.0f}<extra></extra>"
        )
        apply_chart_theme(
            fig_site,
            height=390,
            xaxis_title="ATM Placement Site Type",
            yaxis_title="Total Withdrawn (₹ INR)",
            show_legend=False
        )
        st.plotly_chart(fig_site, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📋 Complete Machine Ranking Table")
    dt = ranked_df[[
        "rank", "atm_id", "atm_name", "area_name", "site_type",
        "total_withdrawn", "avg_daily_withdrawal", "observation_count"
    ]].copy()
    dt["total_withdrawn"] = dt["total_withdrawn"].apply(lambda v: format_inr(v))
    dt["avg_daily_withdrawal"] = dt["avg_daily_withdrawal"].apply(lambda v: format_inr(v))
    st.dataframe(dt, use_container_width=True, height=340)

render_bottom_nav(
    prev_page=("pages/2_Trend_Analysis.py", "2. Trend Analysis", "📈"),
    next_page=("pages/4_EDA_Statistics.py", "4. EDA & Statistics", "🔬")
)

