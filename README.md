# 🏦 ATM Cash Demand Prediction & Replenishment Analytics

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.12-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-Multipage-red.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/pytest-54%20passed-brightgreen.svg)](https://pytest.org/)
[![Database](https://img.shields.io/badge/SQLite-3NF%20Compliant-orange.svg)](https://sqlite.org/)

An end-to-end data analytics and machine learning decision-support platform built for ATM cash replenishment planning. Designed and implemented in strict compliance with the **Business Requirements Document (BRD v1.0)**, **Technical Requirements Document (TRD v1.0)**, **Database Design (Step 8)**, **ER Diagram (Step 9)**, **User Stories (Step 11)**, **UI Framework (Step 12)**, and the **Build Plan (Step 15)**.

---

## 👨‍🎓 Project Information
- **Student Name:** Lavi Tewari
- **Roll Number:** 2503201450083
- **Degree / Year:** MCA, 2nd Year — Data Analytics
- **Institution:** ABES Engineering College
- **Faculty Mentor:** Kalpana Dwivedi
- **Release Version:** 1.0 (Step 15 Production Build)
- **Assumed Business Domain:** Mid-sized retail bank in Noida & Ghaziabad operating ~50 ATMs

---

## 🎯 Coverage of Operational Questions (OQs) & Business Requirements (BRs)

| OQ ID | Operational Question | Business Requirement | Covering Page / Module | Status |
|---|---|---|---|---|
| **OQ-01** | Total cash withdrawn over selected period | **BR-01** (Historical Totals) | `pages/1_Overview.py`, `src/analysis.py` | ✅ Implemented |
| **OQ-02** | Average daily cash withdrawal | **BR-02** (Daily Averages) | `pages/1_Overview.py`, `src/analysis.py` | ✅ Implemented |
| **OQ-03** | Day of week variation | **BR-03** (Weekday Distribution) | `pages/2_Trend_Analysis.py`, `src/analysis.py` | ✅ Implemented |
| **OQ-04** | Monthly & seasonal variation | **BR-04** (Monthly/Seasonal) | `pages/2_Trend_Analysis.py`, `src/analysis.py` | ✅ Implemented |
| **OQ-05** | Highest & lowest usage ATM rankings | **BR-05** (Usage Rankings) | `pages/3_ATM_Comparison.py`, `src/analysis.py` | ✅ Implemented |
| **OQ-06** | Future daily cash demand estimate | **BR-06** (ATM Forecast) | `pages/5_Forecast_Insights.py`, `src/forecasting.py` | ✅ Implemented |
| **OQ-07** | Holdout evaluation vs naive baselines | **BR-07** (Holdout Evaluation) | `pages/5_Forecast_Insights.py`, `src/forecasting.py` | ✅ Implemented |
| **OQ-08** | Demand anomaly detection | **BR-08** (Anomaly Detection) | `pages/5_Forecast_Insights.py`, `src/analysis.py` | ✅ Implemented |
| **OQ-09** | Replenished cash vs withdrawn cash | **BR-09** (Replenishment Reconciliation) | `pages/5_Forecast_Insights.py`, `src/analysis.py` | ✅ Implemented |
| **OQ-10** | Combined network forecast for a target date | **BR-10** (Network Aggregate) | `pages/5_Forecast_Insights.py`, `src/forecasting.py` | ✅ Implemented |
| **-** | Data completeness & quality assessment | **BR-11** (Quality Audit) | `pages/7_Data_Quality.py`, `src/validation.py` | ✅ Implemented |
| **-** | Assumptions, limitations & disclaimer | **BR-12** (Transparency & Viva) | `pages/8_About_Methodology.py`, `src/ui.py` | ✅ Implemented |

---

## 📂 Final Folder Structure

```text
atm-cash-demand-prediction/
├── app.py                                    # Streamlit entry point and navigation hub
├── requirements.txt                          # Pinned production dependencies
├── README.md                                 # Project documentation
├── BUILD_PLAN.md                             # Step-by-step master build plan
├── .gitignore                                # Git ignore file
├── .streamlit/
│   └── config.toml                           # Streamlit theme configuration (Step 12)
├── data/
│   ├── app.db                                # SQLite database (conforming to Step 8 DDL)
│   ├── atm_cash_demand_prediction_data.xlsx  # Multi-sheet Excel dataset
│   ├── atm_master.csv                        # 50 ATM master records
│   ├── date_dim.csv                          # 730 days calendar dimension (2024-2025)
│   ├── atm_daily_fact.csv                    # 250 daily withdrawal and replenishment records
│   ├── atm_forecast_fact.csv                 # 75 benchmark forecast records
│   ├── duplicate_candidates_for_cleaning.csv  # Intentionally quarantined QA records
│   └── validation_report.txt                 # Formatted validation report
├── docs/
│   ├── 01_lavi_tewari_project_understanding.docx
│   ├── 02_HMW_Statements.docx
│   ├── 03_Needs_Analysis.docx
│   ├── 04_Traceability_Matrix.xlsx
│   ├── 04_Traceability_Matrix_Updated_STEP12.xlsx
│   ├── 05_BRD.docx
│   ├── 07_TRD.docx
│   ├── 08_Database_Design.xlsx
│   ├── 09_ER_Diagram.docx
│   ├── 11_User_Stories.docx
│   ├── 12_UI_Framework.docx
│   ├── 13_Test_Cases.docx
│   ├── 13_Final_RTM.xlsx
│   ├── 14_BUILD_PLAN.docx
│   ├── PROJECT_REPORT.md                     # Comprehensive academic report
│   └── VIVA_QUESTIONS.md                     # Viva questions & answers guide
├── src/
│   ├── __init__.py
│   ├── data_loader.py                        # Safe SQLite connection & parameterised queries
│   ├── validation.py                         # Quality rules, DDL checks & foreign key audits
│   ├── cleaning.py                           # Deterministic cleaning & deduplication
│   ├── analysis.py                           # Pure analytical functions & aggregations
│   ├── forecasting.py                        # ML models (Random Forest, Ridge, Naive Baselines)
│   ├── insights.py                           # Evidence-based business interpretation
│   ├── ui.py                                 # Tailwind-styled components & shared state
│   └── utils.py                              # Currency (₹) & date utilities
├── pages/
│   ├── 1_Overview.py                         # UI-01: Network KPIs, trend line & rankings
│   ├── 2_Trend_Analysis.py                   # UI-02: Weekday, monthly & seasonal breakdowns
│   ├── 3_ATM_Comparison.py                   # UI-03: Benchmarking ATMs & dispersion box plots
│   ├── 4_EDA_Statistics.py                   # UI-04: Histograms, distributions & correlations
│   ├── 5_Forecast_Insights.py                # UI-05: Forecasts, holdout evaluation & anomalies
│   ├── 6_Data_Explorer.py                    # UI-06: Filtered data search & CSV export
│   ├── 7_Data_Quality.py                     # UI-07: Relational audit & quarantined records
│   └── 8_About_Methodology.py                # UI-08: Academic context & mathematical definitions
├── tests/
│   ├── conftest.py                           # Shared pytest fixtures
│   ├── test_data.py                          # Database & data-quality test suite
│   ├── test_analysis.py                      # Pure function unit tests with tiny fixtures
│   ├── test_app.py                           # Streamlit AppTest smoke tests
│   └── test_forecasting.py                   # Chronological holdout & KPI-05 verification
└── run_app.bat                               # Windows 1-click startup batch script
```

---

## 🚀 Quick Start Guide

### 1. Installation
Navigate to the repository:
```bash
cd "d:\hcl project\atm cash demand prediction"
```
Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Run All Automated Tests
Execute the full pytest suite (54 passed):
```bash
pytest -v
```

### 3. Launch Interactive Dashboard
Run the multi-page Streamlit application:
```bash
streamlit run app.py
```
*(On Windows, you can also double-click `run_app.bat`)*

Open your browser at: `http://localhost:8501`
