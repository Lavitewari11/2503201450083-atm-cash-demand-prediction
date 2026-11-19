# ATM Cash Demand Prediction — Build Plan
**AI build input for STEP 15 | Version 1.0 | 19 November 2026**

**Student:** Lavi Tewari · Roll No. 2503201450083 · MCA 2nd Year, Data Analytics, ABES  
**Mentor:** Kalpana Dwivedi  
**Project type:** Academic data analytics prototype using synthetic data only

> **Execution rule:** Build one task at a time, in the order below. Do not start the next BUILD task until the current task's checks pass, the requested files exist, and the tests listed for that task have been run. Preserve all existing identifiers. Do not invent real-bank data or claim real stakeholder approval. When a test cannot run because a later module is not yet built, mark it “blocked/pending”, not “passed”.

---

## 1. Project summary (10 lines)

1. ATM Cash Demand Prediction is an academic decision-support prototype for estimating daily cash demand at an ATM.
2. The illustrative business context is a fictional mid-sized retail bank with approximately 50 ATMs in Noida and nearby areas; this is an assumption, not a real client.
3. The application uses synthetic ATM withdrawal, replenishment, calendar, and forecast data; no real customer, card, account, PIN, or bank-sensitive data is allowed.
4. The core workflow is data loading → validation/cleaning → SQLite → descriptive analysis and forecasting → Streamlit/Plotly UI → tests → deployment.
5. The primary data grain is one ATM × calendar date for daily facts; forecasts are one ATM × target date × model version × generated timestamp.
6. The required stack is Python 3.12, pandas, NumPy, SciPy/statsmodels, Plotly, Streamlit multipage, SQLite, pytest and Streamlit AppTest.
7. Tailwind CDN is presentation-only inside the Streamlit HTML component/iframe for the header and KPI cards; interactive controls remain native Streamlit widgets.
8. The app must address OQ-01 to OQ-10 and BR-01 to BR-12, with the seven Must requirements treated as release-critical.
9. Forecasting must use chronological evaluation, MAE and RMSE, comparison with a naive baseline, and explicit model/run selection to prevent leakage and duplicate joins.
10. The result is not a production banking system: forecasts are estimates for human review, and deployment is a restart-safe academic demo on Streamlit Community Cloud.

### Source documents and project artefacts

Links below are repository-relative paths intended for the final project repository. Downloaded source artefacts should be copied into these paths without changing their IDs or meaning.

| Step | Document / artefact | Planned repository path | Use in build |
|---|---|---|---|
| 1 | Project Understanding | `docs/01_lavi_tewari_project_understanding.docx` | Problem, users, OQ-01…OQ-10, scope, objectives and constraints |
| 2 | HMW Statements | `docs/02_HMW_Statements.docx` | HMW-01…HMW-10 and OQ linkage |
| 3 | Needs Analysis | `docs/03_Needs_Analysis.docx` | BR-01…BR-12, priorities, data and acceptance measures |
| 4 | Original RTM | `docs/04_Traceability_Matrix.xlsx` | Original traceability artefact; verify and reconcile with final RTM |
| 4/12/13 | Updated / final RTM | `docs/04_Traceability_Matrix_Updated_STEP12.xlsx`, `docs/13_Final_RTM.xlsx` | Current OQ/HMW/BR/US/UI/test mapping; reconstructed baseline |
| 5 | BRD | `docs/05_BRD.docx` | Business scope, success measures, business rules and acceptance criteria |
| 6 | PRD | **Not supplied / Step 6 skipped** | No approved PRD feature catalogue; PF-01…PF-05 remain provisional epic references |
| 7 | TRD | `docs/07_TRD.docx` | Architecture, stack, performance, security, deployment and technical requirements |
| 8 | Database Design | `docs/08_Database_Design.xlsx` | Four-table SQLite schema, DDL, joins, KPIs and data dictionary |
| 9 | ER Diagram | `docs/09_ER_Diagram.docx`, `docs/09_ER_Diagram.png` | Entity grain, keys, relationships and database rules |
| 10 | Dataset workbook and source files | `data/atm_cash_demand_prediction_data.xlsx`, `data/*.csv`, `data/app.db`, `src/generate_data.py`, `data/validation_report.txt` | Synthetic input, generated database and data-quality evidence |
| 11 | User Stories | `docs/11_User_Stories.docx` | US-01…US-14 and Given/When/Then acceptance criteria |
| 12 | UI Framework | `docs/12_UI_Framework.docx` | UI-01…UI-08, page wireframes, chart choices, state and theme |
| 12 | UI starter artefacts | `src/ui.py`, `.streamlit/config.toml`, `STEP12_UI_Starter_Files.zip` | Header/KPI starter and Streamlit theme baseline |
| 13 | Test Cases | `docs/13_Test_Cases.docx` | TC-F-01…TC-F-27 and TC-T-01…TC-T-24 catalogue |
| 13 | Test starter suite | `tests/test_data.py`, `tests/test_analysis.py`, `tests/test_app.py` | Existing tests; some are intentionally pending Step 15 implementation |

**Traceability caveats to preserve:** Step 6 PRD was skipped; PF-01…PF-05 are provisional only. The Step 4 RTM was reconstructed in later work because the original Step 4 workbook was not created in the earlier workflow; compare both available RTM files before treating the later one as authoritative. Step 10's generated validation report was reported with literal `\n` formatting and final inspection was left pending; fix and re-run validation before calling data QA complete. The Step 13 test catalogue is prepared but its functional cases are initially “Not run”; do not claim they passed until executed.

---

## 2. Final folder structure

```text
atm-cash-demand-prediction/
├── app.py
├── requirements.txt
├── README.md
├── BUILD_PLAN.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   ├── app.db
│   ├── atm_cash_demand_prediction_data.xlsx
│   ├── atm_master.csv
│   ├── date_dim.csv
│   ├── atm_daily_fact.csv
│   ├── atm_forecast_fact.csv
│   ├── duplicate_candidates_for_cleaning.csv
│   └── validation_report.txt
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
│   ├── 09_ER_Diagram.png
│   ├── 11_User_Stories.docx
│   ├── 12_UI_Framework.docx
│   ├── 13_Test_Cases.docx
│   └── 13_Final_RTM.xlsx
├── src/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── validation.py
│   ├── cleaning.py
│   ├── analysis.py
│   ├── forecasting.py
│   ├── insights.py
│   └── ui.py
├── pages/
│   ├── 1_Overview.py
│   ├── 2_Trend_Analysis.py
│   ├── 3_ATM_Comparison.py
│   ├── 4_EDA_Statistics.py
│   ├── 5_Forecast_Insights.py
│   ├── 6_Data_Explorer.py
│   ├── 7_Data_Quality.py
│   └── 8_About_Methodology.py
└── tests/
    ├── conftest.py
    ├── test_data.py
    ├── test_analysis.py
    ├── test_app.py
    └── test_forecasting.py
```

`data/app.db` is the generated demo database. The application must be able to initialise/rebuild it from the synthetic source files/schema if it is missing (important for Community Cloud restarts). Commit only the intended synthetic demo artefacts; never commit secrets, virtual environments, caches, or personal/real banking data. Keep the Step 10 generator in `src/generate_data.py` if it is already present; do not delete it when creating the modules above.

---

## 3. Build tasks — execute one at a time

### BUILD-01 — Repository setup and dependency baseline
- **Goal:** Create the project skeleton, Python 3.12 environment, dependency pins and safe repository defaults.
- **Files:** `requirements.txt`, `.gitignore`, `src/__init__.py`, `.streamlit/config.toml`, folders from Section 2.
- **Stories / features:** Foundation for all US-01…US-14; provisional PF-01…PF-05 only (not approved PRD IDs).
- **Exact AI prompt:**
  > Work only on BUILD-01 of BUILD_PLAN.md. Create the repository folder structure and requirements.txt for Python 3.12 using the TRD baseline: streamlit==1.41.1, pandas==2.2.3, numpy==2.1.3, scipy==1.14.1, statsmodels==0.14.4, plotly==5.24.1, pytest==8.3.4. Add .gitignore for venvs, caches, secrets, local environment files and temporary outputs. Create src/__init__.py and .streamlit/config.toml with the theme values in Step 12. Do not implement application logic or move to BUILD-02. If the pinned Streamlit release lacks the required iframe API, report the evidence and propose a reviewed pin update; do not silently change it.
- **How to check:** `python --version` reports 3.12.x; `pip install -r requirements.txt`; `pip check`; inspect `.gitignore` and theme config.
- **Tests that must pass:** Dependency installation and `pip check`. No application tests required yet.

### BUILD-02 — Data loader and schema-aware database access
- **Goal:** Load the four approved SQLite entities with stable project-root paths and explicit date/ATM filters.
- **Files:** `src/data_loader.py`, `tests/test_data.py`, optionally `tests/conftest.py`.
- **Stories / features:** US-01, US-02; PF-01 (provisional).
- **Exact AI prompt:**
  > Work only on BUILD-02. Read the Step 8 Database Design and Step 9 ERD before coding. Implement src/data_loader.py with project-root-relative paths, a safe SQLite connection context, PRAGMA foreign_keys=ON, required-table/schema checks, and functions to load ATM master, date dimension, daily facts and forecast facts. Use parameterised SQL, not string interpolation for user values. Add filtered daily-data loading by ATM/date range and a forecast loader that supports explicit model_version/generated_at selection. Do not invent columns: use the physical schema from Step 8/9. Keep NULL replenishment values as NULL. Do not start cleaning or analysis.
- **How to check:** Import loader functions; load each required table; verify expected columns and types; missing DB/schema produces a clear actionable error; filtered rows obey filters.
- **Tests that must pass:** TC-T-01, TC-T-02, TC-T-21, TC-T-23 (where applicable); database tests in `tests/test_data.py`.

### BUILD-03 — Validation and cleaning pipeline
- **Goal:** Centralise quality checks and deterministic cleaning; preserve source data and report every action.
- **Files:** `src/validation.py`, `src/cleaning.py`, `data/validation_report.txt`, `tests/test_data.py`.
- **Stories / features:** US-01, US-13; PF-01 and PF-05 (provisional).
- **Exact AI prompt:**
  > Work only on BUILD-03. Implement validation and cleaning using the Step 3 BR-11 rules, Step 8 DDL, Step 9 business rules and Step 10 generated data. Check required fields, nulls, invalid dates, non-numeric/negative amounts, duplicate ATM-date keys, unmatched ATM/date foreign keys, calendar-key consistency and allowed enumerations. Do not treat a missing replenishment amount as zero. Keep duplicate candidates in the review file; do not silently append them to the constrained daily fact table. Make cleaning deterministic and auditable: return cleaned data plus a structured issue/action report with counts. Fix the Step 10 validation_report.txt newline formatting and rerun validation against data/app.db. Preserve valid rows and source provenance. Do not proceed to analysis.
- **How to check:** Run validation twice and compare identical reports; inspect issue counts; `PRAGMA foreign_key_check` returns no violations; no negative amounts; report uses real line breaks and documents NULLs/duplicate candidates.
- **Tests that must pass:** TC-T-04, TC-T-05, TC-T-22 and applicable checks in `tests/test_data.py`.

### BUILD-04 — Core descriptive analysis and KPI functions
- **Goal:** Implement pure, independently testable functions for BR-01…BR-05.
- **Files:** `src/analysis.py`, `tests/test_analysis.py`.
- **Stories / features:** US-02…US-07; PF-02 and PF-03 (provisional).
- **Exact AI prompt:**
  > Work only on BUILD-04. Implement pure pandas/numpy analysis functions for total withdrawals, average daily withdrawals, ATM comparison/ranking, weekday summary, monthly/seasonal summary, and filter application. Follow BR-01…BR-05 and the Step 11 acceptance criteria. The agreed Step 13 test baseline defines average daily withdrawal as the arithmetic mean of valid observed ATM-day withdrawal values; document observed-day counts and do not silently divide by all calendar days. Preserve missing days as missing unless a documented rule says otherwise. Use the physical Step 8 columns and expose stable documented function names/signatures matching tests/test_analysis.py. Include empty-input handling and currency units. Do not create UI code.
- **How to check:** Use tiny deterministic DataFrames; independently hand-calculate totals/averages; confirm weekday order Monday–Sunday; verify month/season labels from date_dim.
- **Tests that must pass:** TC-T-06…TC-T-10, TC-T-23; TC-F-02…TC-F-10 once the UI exists.

### BUILD-05 — Statistical analysis and EDA functions
- **Goal:** Implement descriptive statistics, distribution summaries and safe correlation analysis.
- **Files:** `src/analysis.py`, `tests/test_analysis.py`.
- **Stories / features:** US-06, US-07, US-14; PF-03/PF-05 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-05. Add descriptive_statistics, distribution_summary and correlation_analysis to src/analysis.py. Use pandas/SciPy/statsmodels only where appropriate; report count, mean, median, standard deviation, quartiles, min and max. Define the quantile interpolation/method explicitly. Handle empty, one-value, constant and insufficient samples without crashing. Correlation must use numeric columns only and explain undefined correlations. Do not infer real-bank population effects from synthetic data. Add unit tests with known tiny fixtures.
- **How to check:** For [10,20,30,40], count=4, mean=25, median=25; for [1,2,3,4,100], quartiles match the chosen pandas method; perfect positive correlation fixture returns 1.0.
- **Tests that must pass:** TC-T-18, TC-T-19, TC-T-20.

### BUILD-06 — Forecasting and chronological evaluation
- **Goal:** Provide reproducible per-ATM future estimates and honest forecast evaluation against a naive baseline.
- **Files:** `src/forecasting.py`, `tests/test_forecasting.py`, `tests/test_analysis.py`.
- **Stories / features:** US-08, US-09, US-12, US-14; PF-03, PF-04, PF-05 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-06. Read the BRD, TRD, Step 8 forecast schema and Step 11 US-08/US-09/US-12/US-14 acceptance criteria. Implement a simple reproducible forecasting baseline first, then at most one justified candidate model. Split chronologically; fit preprocessing and models on training data only; compare model MAE with a naive baseline; report MAE, RMSE, evaluation dates, sample count, model name/version, training window and limitations. Forecast output must match the physical atm_forecast_fact schema. Support explicit model_version/generated_at selection. Never evaluate by joining all forecast runs together. Return a clear insufficient-history result. Do not claim the forecast meets the BRD accuracy target until measured evidence shows MAE(model) < MAE(baseline).
- **How to check:** Actual=[100,200], predicted=[110,180] gives MAE=15 and RMSE=sqrt(250); repeated same seed/config gives reproducible outputs; verify no future-data leakage and correct run selection.
- **Tests that must pass:** TC-T-11, TC-T-14 and forecast-specific tests; TC-F-11…TC-F-15, TC-F-27 when UI is ready.

### BUILD-07 — Shared UI components and global state
- **Goal:** Build reusable header, KPI cards, filters, chart wrappers, empty/error states and common layout.
- **Files:** `src/ui.py`, `.streamlit/config.toml`, `app.py` (minimal shell only).
- **Stories / features:** Shared foundation for US-01…US-14; provisional PF-01…PF-05.
- **Exact AI prompt:**
  > Work only on BUILD-07. Follow Step 12 UI Framework exactly. Refine src/ui.py into reusable page header, Tailwind-styled presentational header/KPI cards, shared sidebar filters, chart container, warning/insight/empty-state helpers. Keep all interactive controls in native Streamlit, and store shared selections in st.session_state using the Step 12 keys: selected_start_date, selected_end_date, selected_atm, selected_region, selected_site_type, selected_metric, selected_target_date and selected_model_version. Populate region/site/ATM options from actual distinct values. Validate date order. Tailwind CDN must be optional; app remains usable with native Streamlit fallback. Escape values inserted into HTML. Do not implement individual pages.
- **How to check:** Run app shell; change filters and confirm state survives reruns; test narrow layout; block CDN and confirm fallback.
- **Tests that must pass:** UI smoke check; relevant filter tests; verify shared state and no iframe-dependent business logic.

### BUILD-08 — UI-01 Overview / KPIs page
- **Goal:** Answer OQ-01, OQ-02 and support OQ-05 at a glance.
- **Files:** `app.py`, `pages/1_Overview.py`.
- **Stories / features:** US-01, US-02, US-03, US-04, US-05, US-14; PF-02/PF-05 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-08. Build UI-01 Overview using Step 12 wireframe and shared components. Show total withdrawn, average daily withdrawal, ATMs covered and a forecast/network KPI only when a valid selected forecast exists. Include daily withdrawal line chart, ATM ranking bar chart and summary table. All outputs must respond to shared ATM/date/region/site filters. Show INR units, active period, observed-day counts, synthetic-data notice and explicit no-data states. Do not show missing data as zero.
- **How to check:** Compare displayed totals and averages with SQL/pandas results for same filters; empty date window shows message; all ATM/single ATM and reset work.
- **Tests that must pass:** TC-F-02…TC-F-08, TC-F-21, TC-F-25; TC-T-06…TC-T-08.

### BUILD-09 — UI-02 Trend Analysis page
- **Goal:** Answer OQ-03 and OQ-04 with weekday, monthly and seasonal patterns.
- **Files:** `pages/2_Trend_Analysis.py`.
- **Stories / features:** US-02, US-06, US-07; PF-03 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-09. Build UI-02 Trend Analysis using the shared filters and analysis functions. Show daily line, ordered weekday bar, monthly line and seasonal grouped bar charts. Use the agreed calendar dimension, clear units, labels, selected filters and no-data messages. Do not infer missing dates as zero and do not duplicate aggregation logic inside the page.
- **How to check:** Hand-check a tiny known fixture; verify Monday–Sunday order and monthly grouping; change filters and confirm all charts update.
- **Tests that must pass:** TC-F-09, TC-F-10, TC-F-26; TC-T-09, TC-T-10.

### BUILD-10 — UI-03 ATM Comparison page
- **Goal:** Answer OQ-05 fairly and show coverage/observation counts.
- **Files:** `pages/3_ATM_Comparison.py`.
- **Stories / features:** US-02, US-05; PF-02 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-10. Build UI-03 ATM Comparison with date, region, site-type and ATM multiselect filters. Show sorted horizontal bar chart, comparison table with total, average and observed days, and optional box plot. Exclude or label ATMs with no valid observations as unavailable; do not rank them as zero usage. Use shared analysis functions.
- **How to check:** Compare ATM totals to a direct groupby; no-observation ATM is unavailable; filters affect chart and table identically.
- **Tests that must pass:** TC-F-07, TC-F-08, TC-F-21; TC-T-08.

### BUILD-11 — UI-04 EDA & Statistics page
- **Goal:** Give a controlled view of distributions and descriptive statistics.
- **Files:** `pages/4_EDA_Statistics.py`.
- **Stories / features:** US-02, US-06, US-07; PF-03 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-11. Build UI-04 EDA & Statistics with histogram, box plot by weekday, descriptive statistics table and optional numeric-only correlation heatmap. State selected measure and date/ATM filters. Handle empty/small/constant samples safely; include a concise interpretation without claiming synthetic findings apply to real banks.
- **How to check:** Compare summary values with pandas; confirm chart labels/units; test empty and one-row samples.
- **Tests that must pass:** TC-T-18, TC-T-19, TC-T-20; UI render smoke test.

### BUILD-12 — UI-05 Forecast & Insights page
- **Goal:** Answer OQ-06…OQ-10 and show forecast context.
- **Files:** `pages/5_Forecast_Insights.py`, `src/forecasting.py`, `src/insights.py`.
- **Stories / features:** US-08, US-09, US-10, US-11, US-12, US-14; PF-03/PF-04/PF-05 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-12. Build UI-05 Forecast & Insights. Include target date, ATM and explicit model-version/run selectors; selected ATM forecast KPI; network forecast KPI and included/excluded ATM coverage; actual-vs-forecast time series and MAE/RMSE; anomaly candidate table with rule/reason; replenished-vs-withdrawn comparison. Show model version, training/evaluation window, sample count, baseline comparison, synthetic-data notice and limitations. Keep anomaly flags as review candidates, not fraud findings. Missing replenishment stays unavailable. Do not combine multiple forecast runs.
- **How to check:** Verify MAE/RMSE with tiny fixture; network total sums only eligible forecasts; no forecast and no matched actuals produce clear messages; model run selector changes results.
- **Tests that must pass:** TC-F-11…TC-F-18, TC-F-20, TC-F-27; TC-T-11…TC-T-14.

### BUILD-13 — UI-06 Data Explorer & Download page
- **Goal:** Allow safe inspection and export of filtered synthetic source records.
- **Files:** `pages/6_Data_Explorer.py`.
- **Stories / features:** US-01, US-02; PF-01 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-13. Build UI-06 Data Explorer & Download. Provide source-table selector, date/ATM filters, column selector, row/column counts, bounded table preview and CSV/XLSX downloads. Use allow-listed table names and parameterised queries. Export exactly the filtered dataset shown, with headers and stable types. Never expose secrets or add customer-identifying data.
- **How to check:** Download CSV and reopen it; row count and columns match filtered preview; invalid table/column selections are rejected safely.
- **Tests that must pass:** TC-F-21, TC-F-22, TC-F-24, TC-T-23, TC-T-24.

### BUILD-14 — UI-07 Data Quality page
- **Goal:** Make completeness, validity, duplicates and referential integrity visible.
- **Files:** `pages/7_Data_Quality.py`, `src/validation.py`, `src/cleaning.py`.
- **Stories / features:** US-01, US-13; PF-01/PF-05 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-14. Build UI-07 Data Quality from the structured validation report. Show quality KPIs, missingness by field, validation table, failed checks, duplicate candidates and documented handling decisions. Distinguish source issue counts from cleaned-row counts. Missing replenishment is unavailable, not zero; candidate duplicates remain review items unless an explicit cleaning rule resolves them.
- **How to check:** UI counts reconcile exactly to validation report; filter by table/check type; no misleading 100% quality score when unresolved issues remain.
- **Tests that must pass:** TC-F-01, TC-F-19, TC-F-23; TC-T-01…TC-T-05, TC-T-22.

### BUILD-15 — UI-08 About & Methodology page
- **Goal:** Explain provenance, definitions, assumptions and limitations.
- **Files:** `pages/8_About_Methodology.py`.
- **Stories / features:** US-14; PF-05 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-15. Build UI-08 About & Methodology using the Step 1, BRD, TRD and Step 12 documents. Explain the academic purpose, synthetic data provenance, data grain, KPI definitions, forecast method/version, chronological evaluation, MAE/RMSE, anomaly rule, assumptions, known limitations and out-of-scope production functions. Do not imply real bank deployment or actual operational savings.
- **How to check:** Cross-check each definition against documents and displayed app calculations; synthetic-data and non-production notices are visible.
- **Tests that must pass:** TC-F-20; app page render smoke test.

### BUILD-16 — Insights layer and business interpretation
- **Goal:** Generate evidence-based, caveated insights shared across relevant pages.
- **Files:** `src/insights.py`, integration updates to pages UI-01…UI-05.
- **Stories / features:** US-06…US-14; PF-03/PF-04/PF-05 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-16. Implement reusable insight functions that describe patterns only when supported by computed data: weekday/month differences, high/low ATM usage, anomaly candidates, replenishment comparison and forecast coverage/error. Include the metric, period, comparison basis and caveat. Do not hard-code synthetic patterns as universal facts and do not claim causation. Keep text reproducible from the filtered dataset.
- **How to check:** For each insight, trace the numbers to a table/chart and test with a fixture where the pattern is absent or reversed.
- **Tests that must pass:** Relevant TC-F-09…TC-F-20 and analysis tests; no unsupported static claim.

### BUILD-17 — Full integration, AppTest and performance
- **Goal:** Run all tests, render all pages, verify interactions and measure performance.
- **Files:** `tests/conftest.py`, `tests/test_data.py`, `tests/test_analysis.py`, `tests/test_app.py`, `tests/test_forecasting.py`, app/pages/modules as needed.
- **Stories / features:** US-01…US-14; PF-01…PF-05 provisional.
- **Exact AI prompt:**
  > Work only on BUILD-17. Integrate and execute every test in Step 13. Remove temporary xfail/skip markers only when the implementation exists and the test is meaningful. Add Streamlit AppTest smoke coverage for app.py and all eight pages; add tests for navigation, filters, empty states and downloads where supported. Fix defects rather than weakening assertions. Measure common filtered dashboard render time against the TRD target ≤3 seconds and forecast runtime target ≤5 seconds; record machine, Python version, dataset size and cold/warm cache. Report passed, failed, skipped and blocked tests honestly.
- **How to check:** `python -m pytest -q`; app starts; all eight pages render; run TC-F cases manually and update statuses with evidence; inspect performance record.
- **Tests that must pass:** TC-T-01…TC-T-24 and all automated AppTest cases; all critical functional tests must pass before deployment.

### BUILD-18 — README, reproducibility and documentation
- **Goal:** Make the repository understandable and reproducible by a reviewer.
- **Files:** `README.md`, `BUILD_PLAN.md`, `docs/` index or project guide.
- **Stories / features:** Supports US-01…US-14; all provisional PF references.
- **Exact AI prompt:**
  > Work only on BUILD-18. Write README.md for this exact repository. Include project summary, synthetic-data disclaimer, features mapped to OQ/BR, architecture, final folder structure, Python 3.12 setup, install/run/test commands, data regeneration and database initialisation, forecast/evaluation method, screenshots if available, limitations, test evidence, and deployment URL placeholder until deployment succeeds. Link the project documents by relative path. Clearly disclose Step 6 PRD was skipped and feature IDs are provisional. Do not claim unrun tests or unverified performance.
- **How to check:** Follow README from a clean clone/venv; commands work; links resolve; no secrets or private data.
- **Tests that must pass:** Clean-environment install, `pip check`, `python -m pytest -q`, local app launch.

### BUILD-19 — GitHub and Streamlit Community Cloud deployment
- **Goal:** Deploy a restart-safe public academic demo and verify it after deployment.
- **Files:** repository commit, `README.md`, `.streamlit/config.toml`, deployment settings.
- **Stories / features:** Demonstrates all US-01…US-14; provisional PF references.
- **Exact AI prompt:**
  > Work only on BUILD-19. Prepare the GitHub repository and deploy app.py to Streamlit Community Cloud using Python 3.12 and requirements.txt. Ensure data/app.db can be recreated from synthetic source files/schema after restart. Check paths are project-root-relative; secrets are not committed; all eight pages, filters, charts, forecast workflow, data-quality page and downloads work in the hosted app. Run a post-deployment smoke test and update README with the verified live URL, deployment date and limitations. Do not claim deployment succeeded until the hosted URL is opened and checked.
- **How to check:** Open deployed URL in a fresh browser session; test navigation, filters, empty states, data loading, one forecast, evaluation, download and restart/rebuild behaviour.
- **Tests that must pass:** Full local automated suite before deployment; hosted smoke tests after deployment. App live URL must be verified.

---

## 4. Definition of Done (DoD)

The project is complete only when all of the following are evidenced:

- [ ] All seven Must BRs are implemented: BR-01, BR-02, BR-03, BR-04, BR-05, BR-06 and BR-07.
- [ ] Supporting BR-08…BR-12 are implemented or explicitly documented with an approved scope decision; no silent omission.
- [ ] OQ-01…OQ-10 have a working page/output or a clear documented limitation.
- [ ] US-01…US-14 acceptance criteria are implemented and checked.
- [ ] Data loading, validation, cleaning, SQLite constraints and quality reporting are reproducible.
- [ ] Forecast uses chronological split, no leakage, MAE/RMSE, naive baseline comparison and explicit model/run selection.
- [ ] All eight pages UI-01…UI-08 render; filters, navigation, empty states and downloads work.
- [ ] All required automated tests pass; functional cases are executed and recorded. No unexplained xfail/skip remains.
- [ ] Common filtered dashboard render meets TRD target ≤3 seconds and forecast runtime target ≤5 seconds on a documented test environment, or deviations are disclosed.
- [ ] README contains clean setup/run/test instructions, data provenance, limitations and verified deployment URL.
- [ ] GitHub repository contains no secrets or real personal/banking data.
- [ ] Streamlit Community Cloud app is live and has passed post-deployment smoke checks.
- [ ] Final RTM links OQ → HMW → BR → provisional feature → US → DB → UI → TC without changing IDs; provisional feature status is clearly labelled.

**Important:** The BRD proposes MAE(model) < MAE(naive baseline). This is a success target, not an achieved result. If the model does not beat the baseline, report the result honestly and explain the limitation rather than manipulating the test period.

---

## 5. Commands

Run from the repository root.

### Create and activate a Python 3.12 virtual environment

**Windows PowerShell**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python --version
```

**macOS / Linux**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
python --version
```

### Install dependencies and verify

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
pip check
```

### Run the application

```bash
streamlit run app.py
```

### Run all automated tests

```bash
python -m pytest -q
```

### Run a specific test module

```bash
python -m pytest tests/test_data.py -q
python -m pytest tests/test_analysis.py -q
python -m pytest tests/test_app.py -q
```

### Optional coverage report (install pytest-cov first if used)

```bash
python -m pip install pytest-cov
python -m pytest --cov=src --cov-report=term-missing
```

---

## 6. Viva notes — 10 likely questions with short answers

1. **What problem does the project solve?**  
   It analyses historical ATM withdrawals and estimates future daily demand to support more consistent cash replenishment planning.

2. **Why is the data synthetic?**  
   This is an academic prototype without authorised real bank data. Synthetic data protects privacy and allows reproducible testing.

3. **What is the grain of `atm_daily_fact`?**  
   One row per ATM per calendar date, identified by the composite key `(atm_id, date_key)`.

4. **Why use SQLite?**  
   It is lightweight, file-based and sufficient for a reproducible academic prototype with a small synthetic dataset.

5. **What is the difference between total and average daily withdrawal?**  
   Total is the sum over the selected period; average daily withdrawal is the mean of valid observed ATM-day withdrawals under the documented missing-day rule.

6. **Why use a chronological train/test split?**  
   It simulates forecasting the future and prevents future observations from leaking into model training.

7. **What are MAE and RMSE?**  
   MAE is the average absolute prediction error; RMSE is the square root of mean squared error and penalises larger errors more strongly. Both use the same currency unit as the target.

8. **Why compare with a naive baseline?**  
   A complex model is useful only if it performs better than a simple reference forecast on the same held-out dates.

9. **Why can forecasts have multiple rows for the same ATM and target date?**  
   Different model versions or generated runs are retained. Evaluation must select one explicit run/version to avoid duplicate actual matches.

10. **Can this app automatically decide how much cash a bank should load?**  
    No. It is a synthetic-data academic decision-support prototype. A human reviews estimates; live bank integration, automated orders and production controls are out of scope.

---

## 7. Build execution protocol for STEP 15

1. Start at BUILD-01 and do not skip ahead.
2. Before each task, read the referenced source documents and inspect the existing repository files.
3. Make only the changes listed for the current BUILD task.
4. Show the files created/changed and explain key implementation choices.
5. Run the task's checks and tests; include the actual command and result.
6. If blocked by missing source, schema mismatch, dependency incompatibility or a failing prior test, stop and report the blocker. Do not silently guess.
7. Update `BUILD_PLAN.md` only to record a verified decision or completion status; preserve BUILD IDs and all OQ/HMW/BR/FR/US/UI/TC identifiers.
8. Ask before proceeding to the next BUILD task if the user is controlling the step-by-step sequence.

**Next action:** STEP 15 begins with BUILD-01 only.
