"""
UI-07: Data Quality & Integrity Page (BUILD-14, US-01, US-13).
Displays structured validation report, foreign key checks, null audits, and quarantined candidates.
"""
import streamlit as st
from src.validation import run_validation_pipeline
from src.ui import render_header, render_kpi_card, render_top_nav, render_bottom_nav, safe_page_link

try:
    st.set_page_config(page_title="Data Quality - ATM Analytics", page_icon="🔍", layout="wide")
except Exception:
    pass

render_header("Data Quality & Governance Audit", "Systematic inspection of relational constraints, completeness, and schema rules")
render_top_nav("7. Data Quality")

try:
    report = run_validation_pipeline()
except Exception as exc:
    st.error(f"❌ Error executing data quality validation pipeline: {exc}")
    safe_page_link("app.py", label="Return to Home Hub", icon="🏠")
    st.stop()


k1, k2, k3, k4 = st.columns(4)
with k1:
    render_kpi_card("Overall Data Health", "PASS" if report["overall_status"] == "PASS" else "FAIL", "All DDL rules & FKs satisfied")
with k2:
    render_kpi_card("Foreign Key Integrity", report["foreign_key_audit"]["status"], f"{report['foreign_key_audit']['violations_count']} violations")
with k3:
    render_kpi_card("Total Base Entities", f"{len(report['row_counts'])} Tables", "50 ATMs, 730 Dates, 250 Facts")
with k4:
    render_kpi_card("Quarantined Duplicates", f"{len(report['quarantined_duplicates_df'])} Rows", "Isolated in QA file (Step 10)")

st.markdown("---")
tab_schema, tab_nulls, tab_quar = st.tabs(["📋 Schema & Range Rules", "🔍 Missing Values Audit", "⚠️ Quarantined Duplicates"])

with tab_schema:
    st.subheader("Automated DDL Range & Integrity Checks")
    st.dataframe(report["schema_rules_df"], use_container_width=True)

with tab_nulls:
    st.subheader("Null Value Distribution across Base Tables")
    st.caption("Verifies that missing values exist ONLY in authorized nullable columns (e.g. replenishment, balances).")
    st.dataframe(report["missing_values_df"], use_container_width=True)

with tab_quar:
    st.subheader("Quarantined Duplicate Candidates")
    st.caption("These duplicate records were deliberately isolated into `duplicate_candidates_for_cleaning.csv` during synthetic generation to demonstrate deduplication without corrupting production primary keys.")
    st.dataframe(report["quarantined_duplicates_df"], use_container_width=True)

render_bottom_nav(
    prev_page=("pages/6_Data_Explorer.py", "6. Data Explorer", "📁"),
    next_page=("pages/8_About_Methodology.py", "8. About & Methodology", "ℹ️")
)

