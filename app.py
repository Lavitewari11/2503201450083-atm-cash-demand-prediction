"""
ATM Cash Demand Prediction — Main Application Entry Point.
Streamlit Multipage Hub (BUILD-07, BUILD-08, Step 12 UI Framework).
Student: Lavi Tewari | Roll No: 2503201450083 | MCA Data Analytics, ABES
Mentor: Kalpana Dwivedi
"""
from datetime import date
import streamlit as st

from src.data_loader import load_atm_master, load_date_dim, load_daily_fact
from src.analysis import calculate_total_withdrawal, calculate_average_daily_withdrawal, apply_filters
from src.ui import render_header, render_kpi_card, init_shared_filters
from src.utils import format_inr, format_number

st.set_page_config(
    page_title="ATM Cash Demand Prediction",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load base data
atms_df = load_atm_master()
calendar_df = load_date_dim()
facts_df = load_daily_fact()

# Initialize global filters in session state
filters = init_shared_filters(atms_df, calendar_df)

render_header("ATM Cash Demand Prediction & Replenishment Analytics", "Decision-support platform for banking cash logistics")

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
active_count = int(atms_df["is_active"].sum()) if "is_active" in atms_df.columns else len(atms_df)

c1, c2, c3, c4 = st.columns(4)
with c1:
    render_kpi_card("Total Cash Withdrawn", format_inr(tot_withdrawn, compact=True), f"Sum over {len(filtered_facts)} observed days (OQ-01)")
with c2:
    render_kpi_card("Avg Daily Withdrawal", format_inr(avg_daily, compact=True), "Arithmetic mean of observed days (OQ-02)")
with c3:
    render_kpi_card("Active Network ATMs", f"{active_count} / {len(atms_df)} Machines", "Noida & Ghaziabad retail network")
with c4:
    render_kpi_card("Calendar Coverage", f"{len(calendar_df)} Days", "2024-01-01 to 2025-12-30 (date_dim)")

st.markdown("---")
st.subheader("Explore Analytics Workspace Pages")
st.markdown("Select a module from the **left sidebar** navigation or click below:")

p_col1, p_col2 = st.columns(2)

with p_col1:
    st.markdown("#### 📊 Operational Analytics")
    with st.container(border=True):
        st.page_link("pages/1_Overview.py", label="1. Overview & KPIs", icon="📊")
        st.caption("Network-wide total withdrawals, 7-day moving average trend, and top ATM rankings.")
    with st.container(border=True):
        st.page_link("pages/2_Trend_Analysis.py", label="2. Trend Analysis", icon="📈")
        st.caption("Day-of-week patterns, monthly trend curve, and seasonal shifts (Summer, Monsoon, Winter).")
    with st.container(border=True):
        st.page_link("pages/3_ATM_Comparison.py", label="3. ATM Comparison", icon="🏆")
        st.caption("Benchmark and rank ATMs by historical volume, area, and site type.")
    with st.container(border=True):
        st.page_link("pages/4_EDA_Statistics.py", label="4. EDA & Statistics", icon="🔬")
        st.caption("Demand distributions, histograms, box plots, and correlation heatmaps.")

with p_col2:
    st.markdown("#### 🔮 Predictive & Governance Modules")
    with st.container(border=True):
        st.page_link("pages/5_Forecast_Insights.py", label="5. Forecast & Insights", icon="🔮")
        st.caption("Single ATM forecasts (OQ-06), network demand (OQ-10), holdout evaluation (OQ-07), and anomaly detection (OQ-08).")
    with st.container(border=True):
        st.page_link("pages/6_Data_Explorer.py", label="6. Data Explorer", icon="📁")
        st.caption("Filter, search, inspect, and export clean database records to CSV.")
    with st.container(border=True):
        st.page_link("pages/7_Data_Quality.py", label="7. Data Quality", icon="🔍")
        st.caption("Automated audits for foreign keys, missing values, duplicates, and range rules (BR-11).")
    with st.container(border=True):
        st.page_link("pages/8_About_Methodology.py", label="8. About & Methodology", icon="ℹ️")
        st.caption("Academic context, holdout design, mathematical metrics, and limitations.")


st.markdown("---")
st.caption("Developed by **Lavi Tewari** (Roll No: 2503201450083) | Guided by **Kalpana Dwivedi** | MCA Data Analytics, ABES")
