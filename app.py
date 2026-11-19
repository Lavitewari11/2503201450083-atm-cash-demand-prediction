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
    st.markdown("""
    #### 📊 Operational Analytics
    - **[1. Overview & KPIs](pages/1_Overview.py):** Network-wide total withdrawals, 7-day moving average trend, and top ATM rankings.
    - **[2. Trend Analysis](pages/2_Trend_Analysis.py):** Day-of-week patterns, monthly trend curve, and seasonal shifts (Summer, Monsoon, Winter).
    - **[3. ATM Comparison](pages/3_ATM_Comparison.py):** Benchmark and rank ATMs by historical volume, area, and site type.
    - **[4. EDA & Statistics](pages/4_EDA_Statistics.py):** Demand distributions, histograms, box plots, and correlation heatmaps.
    """)

with p_col2:
    st.markdown("""
    #### 🔮 Predictive & Governance Modules
    - **[5. Forecast & Insights](pages/5_Forecast_Insights.py):** Single ATM forecasts (OQ-06), network demand (OQ-10), holdout evaluation (OQ-07), and anomaly detection (OQ-08).
    - **[6. Data Explorer](pages/6_Data_Explorer.py):** Filter, search, inspect, and export clean database records to CSV.
    - **[7. Data Quality](pages/7_Data_Quality.py):** Automated audits for foreign keys, missing values, duplicates, and range rules (BR-11).
    - **[8. About & Methodology](pages/8_About_Methodology.py):** Academic context, holdout design, mathematical metrics, and limitations.
    """)

st.markdown("---")
st.caption("Developed by **Lavi Tewari** (Roll No: 2503201450083) | Guided by **Kalpana Dwivedi** | MCA Data Analytics, ABES")
