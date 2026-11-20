"""
UI-08: About & Methodology Page (BUILD-15, US-14).
Explains academic provenance, synthetic dataset design, KPI definitions, and limitations.
"""
import streamlit as st
from src.ui import render_header, render_top_nav, render_bottom_nav

try:
    st.set_page_config(page_title="About & Methodology - ATM Analytics", page_icon="ℹ️", layout="wide")
except Exception:
    pass

render_header("About & Analytical Methodology", "Project specifications, academic governance, and mathematical definitions")
render_top_nav("8. About & Methodology")


st.markdown("""
### 🎓 Academic Project Profile
- **Project Title:** ATM Cash Demand Prediction (Data Analytics Project)
- **Student Name:** Lavi Tewari
- **Roll Number:** 2503201450083
- **Degree:** Master of Computer Applications (MCA), 2nd Year — Data Analytics
- **Institution:** ABES Engineering College
- **Faculty Mentor:** Kalpana Dwivedi
- **Release Version:** 1.0 (Step 15 Build)

---
### 🛠️ Technology Stack & Architecture
- **Language & Runtime:** Python 3.10+
- **Interactive UI Framework:** Streamlit 1.57 (Multi-Page Navigation Architecture)
- **Relational Data Warehouse:** SQLite 3 (ACID-compliant local relational store with enforced foreign keys)
- **Data Engineering & Manipulation:** Pandas 2.2+, NumPy
- **Interactive Visualizations:** Plotly Express & Plotly Graph Objects (Interactive HTML5 charts)
- **Statistical & ML Modeling:** Scikit-Learn (Random Forest Regressor, Seasonal Naive Baseline)
- **Testing & QA Suite:** Pytest (58 automated unit and end-to-end integration tests)

---
### 🏛️ Relational Data Grain
- **`atm_master`:** One row per ATM, keyed by `atm_id` (50 synthetic ATMs across Noida & Ghaziabad).
- **`date_dim`:** One row per calendar date, keyed by `date_key` (730 dates: 2024-01-01 to 2025-12-30).
- **`atm_daily_fact`:** One row per ATM per date, composite primary key `(atm_id, date_key)` (250 observations).
- **`atm_forecast_fact`:** Composite primary key `(atm_id, target_date_key, model_version, generated_at)`.
- **Referential Integrity:** Enforced via `PRAGMA foreign_keys = ON;`.

---
### 📐 Evaluation Metrics & Holdout Design
- **Chronological Split:** Strictly chronological train/test split. Earlier 80% of dates for training; later 20% of dates for testing. **Zero future data leakage**.
- **Mean Absolute Error (MAE):**  
  $$\\text{MAE} = \\frac{1}{n} \\sum_{i=1}^n |y_i - \\hat{y}_i|$$
- **Root Mean Squared Error (RMSE):**  
  $$\\text{RMSE} = \\sqrt{\\frac{1}{n} \\sum_{i=1}^n (y_i - \\hat{y}_i)^2}$$
- **KPI-05 Target:** Machine Learning model achieves $\\text{MAE}(\\text{model}) < \\text{MAE}(\\text{baseline})$, proving statistical uplift over simple averages.

---
### ⚠️ Scope & Operational Disclaimers
1. **Academic Demonstration Only:** All data is synthetic and generated with seed 42. No real customer, card, or banking data is used.
2. **Decision Support:** Forecasts are analytical recommendations to assist human planners, not automated cash replenishment triggers.
3. **Out of Scope:** Live ATM switch connections, core banking integration, physical cash-in-transit routing, and multi-bank production clustering.
""")

render_bottom_nav(
    prev_page=("pages/7_Data_Quality.py", "7. Data Quality", "🔍"),
    next_page=("app.py", "Return to Home Hub", "🏠")
)

