# 🏦 ATM Cash Demand Prediction & Replenishment Analytics

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Streamlit-1.30%2B-red.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/pytest-20%20passed-brightgreen.svg)](https://pytest.org/)
[![Database](https://img.shields.io/badge/SQLite-3NF%20Compliant-orange.svg)](https://sqlite.org/)

An end-to-end data analytics and machine learning decision-support platform built for ATM cash replenishment planning. Designed and implemented in strict compliance with the **Business Requirements Document (BRD v1.0)**, **Database Design (Step 8)**, **ER Diagram (Step 9)**, and **Traceability Matrix**.

---

## 👨‍🎓 Project Information
- **Student Name:** Lavi Tewari
- **Roll Number:** 2503201450083
- **Degree / Year:** MCA, 2nd Year — Data Analytics
- **Institution:** ABES Engineering College
- **Faculty Mentor:** Kalpana Dwivedi
- **Submission Date:** 19 November 2026
- **Assumed Business Domain:** Mid-sized retail bank in Noida & Ghaziabad operating 50 ATMs

---

## 🎯 Coverage of Operational Questions (OQs) & Business Requirements (BRs)

| OQ ID | Operational Question | Business Requirement | Status |
|---|---|---|---|
| **OQ-01** | Total cash withdrawn over selected period | **BR-01** (Historical Totals) | ✅ Implemented |
| **OQ-02** | Average daily cash withdrawal | **BR-02** (Daily Averages) | ✅ Implemented |
| **OQ-03** | Day of week variation | **BR-03** (Weekday Distribution) | ✅ Implemented |
| **OQ-04** | Monthly & seasonal variation | **BR-04** (Monthly/Seasonal) | ✅ Implemented |
| **OQ-05** | Highest & lowest usage ATM rankings | **BR-05** (Usage Rankings) | ✅ Implemented |
| **OQ-06** | Future daily cash demand estimate | **BR-06** (ATM Forecast) | ✅ Implemented |
| **OQ-07** | Holdout evaluation vs naive baselines | **BR-07** (Holdout Evaluation) | ✅ Implemented |
| **OQ-08** | Demand anomaly detection | **BR-08** (Anomaly Detection) | ✅ Implemented |
| **OQ-09** | Replenished cash vs withdrawn cash | **BR-09** (Replenishment Reconciliation) | ✅ Implemented |
| **OQ-10** | Combined network forecast for a target date | **BR-10** (Network Aggregate) | ✅ Implemented |
| **-** | Data completeness & quality assessment | **BR-11** (Quality Audit) | ✅ Implemented |
| **-** | Assumptions, limitations & disclaimer | **BR-12** (Transparency & Viva) | ✅ Implemented |

---

## 📂 Project Repository Structure

```text
atm cash demand prediction/
├── data/
│   ├── app.db                                # SQLite database (conforming to Step 8 DDL)
│   ├── atm_master.csv                        # 50 ATM master records
│   ├── date_dim.csv                          # 730 days calendar dimension (2024-2025)
│   ├── atm_daily_fact.csv                    # 250 daily withdrawal and replenishment records
│   ├── atm_forecast_fact.csv                 # 75 benchmark forecast records
│   ├── duplicate_candidates_for_cleaning.csv  # Intentionally tagged QA duplicates
│   ├── validation_report.txt                 # Data validation report
│   └── atm_cash_demand_prediction_data.xlsx  # Multi-sheet Excel dataset
├── src/
│   ├── __init__.py
│   ├── database.py                           # SQLite connection, DDL schema, query functions
│   ├── data_quality.py                       # Data validation, null counts, duplicate checks
│   ├── analytics.py                          # Aggregations, statistics, rankings, anomalies
│   ├── models.py                             # ML models (Random Forest, Ridge, Naive Baselines)
│   ├── utils.py                              # INR currency (₹) formatting & date helpers
│   └── generate_data.py                      # Reproducible synthetic data generation script (seed 42)
├── tests/
│   ├── __init__.py
│   ├── test_database.py                      # Tests for SQLite schema, keys, foreign keys
│   ├── test_data_quality.py                  # Tests for audit rules and data health
│   ├── test_analytics.py                     # Tests for historical calculations, OQ-01..05, 08, 09
│   └── test_models.py                        # Tests for forecasting models, chronological split, MAE/RMSE
├── docs/
│   ├── 01_lavi_tewari_project_understanding.docx
│   ├── 03_Needs_Analysis.docx
│   ├── 04_Traceability_Matrix.xlsx
│   ├── 05_BRD.docx
│   ├── 08_Database_Design.xlsx
│   ├── 09_ER_Diagram.docx
│   ├── PROJECT_REPORT.md                     # Comprehensive academic report
│   └── VIVA_QUESTIONS.md                     # Viva questions & answers guide
├── app.py                                    # Full-featured Streamlit Web Application
├── requirements.txt                          # Pinned dependencies
├── README.md                                 # Complete documentation
└── run_app.bat                               # Windows 1-click startup batch script
```

---

## 🚀 Quick Start Guide

### 1. Installation
Clone or navigate to the project directory:
```bash
cd "d:\hcl project\atm cash demand prediction"
```
Install the required packages:
```bash
pip install -r requirements.txt
```

### 2. Run Automated Tests
Verify that all 20 tests pass:
```bash
pytest -v
```

### 3. Launch Interactive Dashboard
Run the Streamlit application:
```bash
streamlit run app.py
```
*(On Windows, you can also double-click `run_app.bat`)*

Once started, open your web browser at:
```text
http://localhost:8501
```

---

## 📊 Application Features & Dashboard Tabs

1. **📊 Overview:** Executive operational summary, daily demand time series with 7-day moving average, and site type distribution.
2. **📈 Historical Demand (OQ-01, OQ-02):** Total withdrawn, daily average (observed vs calendar days), min, median, max, std dev.
3. **📅 Patterns & Seasonality (OQ-03, OQ-04):** Weekday distribution (Monday to Sunday) with reconciliation, monthly trend line, and seasonal breakdown (Summer, Monsoon, Winter, Other).
4. **🏆 ATM Rankings (OQ-05):** Top-N & Bottom-N ATM rankings with interactive horizontal bar charts and site type filters.
5. **🔮 ATM Forecast (OQ-06):** Single ATM demand prediction for any future date with minimum history check and contextual factors.
6. **🌐 Network Forecast (OQ-10):** Network-wide aggregate demand across active ATMs with explicit exclusion disclosure.
7. **🎯 Model Evaluation (OQ-07):** Chronological holdout evaluation demonstrating `MAE(ML) < MAE(Baseline)` (verifying **KPI-05**).
8. **⚠️ Anomalies (OQ-08):** Statistical outlier detection (Z-score & IQR) flagging candidate high/low demand days.
9. **💰 Replenishment (OQ-09):** Cash loaded vs withdrawn, net cash difference, and replenishment ratio.
10. **🔍 Data Quality (BR-11):** 100% Data health audit, foreign key verification, null audit, and quarantined duplicate inspector.
11. **ℹ️ Project Info & Viva:** Complete project profile, traceability mapping, and viva examination preparation answers.
