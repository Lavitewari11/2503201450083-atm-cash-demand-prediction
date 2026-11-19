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
    init_shared_filters, render_empty_state, render_top_nav, render_bottom_nav
)
from src.utils import format_inr

st.set_page_config(page_title="ATM Comparison - ATM Analytics", page_icon="🏆", layout="wide")

try:
    atms_df = load_atm_master()
    calendar_df = load_date_dim()
    facts_df = load_daily_fact()
except Exception as exc:
    st.error(f"❌ Database error loading comparison data: {exc}")
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
        st.subheader("ATM Cash Demand Rankings")
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
        fig_h.update_layout(yaxis=dict(autorange="reversed"), height=max(360, top_n * 25), margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_h, use_container_width=True)

    with col_box:
        st.subheader("Daily Demand Dispersion")
        top_ids = ranked_df.head(top_n)["atm_id"].tolist()
        box_data = filtered_df[filtered_df["atm_id"].isin(top_ids)]
        fig_box = px.box(
            box_data,
            x="atm_id",
            y="withdrawal_amount_inr",
            labels={"atm_id": "ATM", "withdrawal_amount_inr": "Daily Withdrawal (₹)"},
            color="site_type"
        )
        fig_box.update_layout(height=max(360, top_n * 25), margin=dict(l=20, r=20, t=20, b=20), showlegend=False)
        st.plotly_chart(fig_box, use_container_width=True)

    st.markdown("---")
    st.subheader("Detailed Ranking Table")
    dt = ranked_df[[
        "rank", "atm_id", "atm_name", "area_name", "site_type",
        "total_withdrawn", "avg_daily_withdrawal", "observation_count"
    ]].copy()
    dt["total_withdrawn"] = dt["total_withdrawn"].apply(lambda v: format_inr(v))
    dt["avg_daily_withdrawal"] = dt["avg_daily_withdrawal"].apply(lambda v: format_inr(v))
    st.dataframe(dt, use_container_width=True, height=300)

render_bottom_nav(
    prev_page=("pages/2_Trend_Analysis.py", "2. Trend Analysis", "📈"),
    next_page=("pages/4_EDA_Statistics.py", "4. EDA & Statistics", "🔬")
)

