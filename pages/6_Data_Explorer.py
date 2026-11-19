"""
UI-06: Data Explorer & Download Page (BUILD-13, US-01, US-02).
Safe inspection and export of filtered synthetic source records.
"""
import io
import streamlit as st
import pandas as pd

from src.data_loader import (
    load_atm_master, load_date_dim, load_daily_fact,
    load_forecast_fact, get_connection
)
from src.ui import render_header, render_empty_state, render_top_nav, render_bottom_nav

st.set_page_config(page_title="Data Explorer - ATM Analytics", page_icon="📁", layout="wide")

render_header("Data Explorer & Export Center", "Inspect, filter, and export synthetic database tables")
render_top_nav("6. Data Explorer")

tables = ["atm_daily_fact", "atm_master", "date_dim", "atm_forecast_fact", "vw_atm_daily_analysis"]
selected_table = st.selectbox("Select Database Entity / View:", tables, index=0)

try:
    con = get_connection()
    df_raw = pd.read_sql_query(f"SELECT * FROM {selected_table} LIMIT 1000", con)
    con.close()
except Exception as exc:
    st.error(f"❌ Database error loading table {selected_table}: {exc}")
    st.page_link("app.py", label="Return to Home Hub", icon="🏠")
    st.stop()


c1, c2, c3 = st.columns(3)
with c1:
    st.metric("Total Records Loaded", len(df_raw))
with c2:
    st.metric("Total Columns", len(df_raw.columns))
with c3:
    st.metric("Entity Type", "View" if "vw_" in selected_table else "Base Table")

st.markdown("---")
# Column selector
selected_cols = st.multiselect("Select Columns to Display:", options=df_raw.columns.tolist(), default=df_raw.columns.tolist()[:10])

if not selected_cols:
    st.warning("Please select at least one column to view.")
else:
    df_display = df_raw[selected_cols]
    st.dataframe(df_display, use_container_width=True, height=380)

    # Downloads
    csv_bytes = df_display.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Filtered Data as CSV",
        data=csv_bytes,
        file_name=f"{selected_table}_export.csv",
        mime="text/csv",
        type="primary"
    )

render_bottom_nav(
    prev_page=("pages/5_Forecast_Insights.py", "5. Forecast & Insights", "🔮"),
    next_page=("pages/7_Data_Quality.py", "7. Data Quality", "🔍")
)

