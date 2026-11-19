# ATM Cash Demand Prediction — Viva Voce Examination Guide

**Student:** Lavi Tewari | **Roll No:** 2503201450083  
**Institution:** ABES Engineering College | **Programme:** MCA 2nd Year (Data Analytics)  
**Mentor:** Kalpana Dwivedi  

---

### Q1. What is the business problem addressed by this project?
**Answer:**  
In commercial retail banking, cash management teams face a delicate trade-off:
- If cash demand at an ATM is **underestimated**, the machine experiences a **cash-out (stockout)**, causing customer dissatisfaction, loss of transaction interchange fees, and potential regulatory non-compliance.
- If cash demand is **overestimated**, substantial cash remains **idle** inside the machine, leading to high cost of funds (lost interest), increased insurance costs, and higher cash-in-transit (CIT) handling logistics.  
Our decision-support tool leverages historical demand patterns and machine learning to forecast ATM-wise cash requirements and optimize replenishment planning.

---

### Q2. Why is synthetic data used instead of real banking data?
**Answer:**  
Banking transaction logs, ATM switch data, and account withdrawal records constitute sensitive financial information governed by strict banking privacy laws (e.g., RBI guidelines in India, GDPR, DPDP Act). To build a fully reproducible, shareable, and auditable academic prototype without violating banking secrecy, we generated a mathematically grounded synthetic dataset with realistic calendar dynamics (seasonality, weekend effects, month-end salary uplifts, and high-volume location cohorts) using a fixed seed (42).

---

### Q3. Explain the database schema design and why SQLite was chosen.
**Answer:**  
The database conforms strictly to Step 8 database design and 3NF normalization with four core tables:
1. `atm_master`: ATM location details, site types (`Branch`, `Market`, `Transit`, `Residential`, `Office`), and operational status.
2. `date_dim`: Calendar dimension with pre-calculated calendar attributes (`day_of_week_num`, `month_num`, `season_name`, `is_weekend`, `is_holiday`).
3. `atm_daily_fact`: Stores daily operational aggregates with a composite primary key `(atm_id, date_key)`.
4. `atm_forecast_fact`: Stores multi-model forecast outputs with composite primary key `(atm_id, target_date_key, model_version, generated_at)`.
5. `vw_atm_daily_analysis`: Pre-joined analytical view.

SQLite was selected because it is serverless, zero-configuration, embeds directly into Python, supports full ACID transactions, and enforces referential integrity with `PRAGMA foreign_keys = ON;`.

---

### Q4. Why does `atm_daily_fact` have a composite primary key?
**Answer:**  
The core analytical grain of the system is **one observation per ATM per calendar date**. Using `(atm_id, date_key)` as a composite primary key prevents duplicate records for the same ATM on the same date while guaranteeing data integrity.

---

### Q5. Why is there no mandatory foreign key from `atm_forecast_fact` to `atm_daily_fact`?
**Answer:**  
Forecasts are frequently generated for **future dates** where actual withdrawal data does not yet exist. Enforcing a mandatory foreign key from forecasts to daily facts would erroneously block legitimate forward-looking predictions. Instead, the link is established as an optional analytical join when historical actuals become available.

---

### Q6. How was data leakage prevented in your machine learning workflow?
**Answer:**  
In time-series forecasting, standard random train/test splits (such as `KFold` or random `train_test_split`) cause **future-data leakage**, where the model inadvertently learns from future observations to predict past events.  
To prevent this, we implemented a **strictly chronological holdout split**:
- The earlier 80% of dates were designated as the training set.
- The later 20% of dates were designated as the held-out test set.
- Feature transformations and encodings were fitted exclusively on the training partition.

---

### Q7. How do you evaluate and benchmark the forecast models?
**Answer:**  
We evaluate models using two standard regression metrics:
1. **Mean Absolute Error (MAE):** Represents the expected deviation in Indian Rupees (₹).
2. **Root Mean Squared Error (RMSE):** Penalizes larger outlier prediction errors.

To satisfy **KPI-05**, the machine learning model (Random Forest Regressor) was benchmarked against naive baselines:
- **Seasonal Naive Baseline:** Predicts the ATM's historical average for the target weekday.
- **Moving Average Baseline:** Predicts the ATM's recent historical mean.  
The ML model achieved lower MAE and RMSE than the naive baselines (`MAE(ML) < MAE(Baseline)`), proving the value of learning nonlinear calendar and location interactions.

---

### Q8. What happens if a user requests a forecast for an ATM with insufficient history?
**Answer:**  
Per **BR-06**, the system verifies that at least 3 historical observations exist for the selected ATM. If insufficient data is found, the system returns a clear message stating that the demand estimate is **unavailable due to insufficient history**, rather than outputting a misleading, fabricated prediction.

---

### Q9. How does the application identify demand anomalies (OQ-08)?
**Answer:**  
We implemented two statistical outlier detection methods:
1. **Z-Score Method:** Computes $|Z| = \frac{|x - \mu|}{\sigma}$ and flags observations exceeding the user-configured sensitivity threshold.
2. **Interquartile Range (IQR) Method:** Computes boundaries $Q1 - k \cdot IQR$ and $Q3 + k \cdot IQR$.  
In adherence to **BRULE-10**, flagged observations are labeled as *analytical candidates for investigation* rather than confirmed fraud or operational incidents.

---

### Q10. What is the difference between a stakeholder need and a business requirement?
**Answer:**  
A **stakeholder need** expresses what a user or role requires from their perspective (e.g., "The Cash Analyst needs to know how much cash to load tomorrow"). A **business requirement (BR)** translates that need into a formal, testable capability that the system must provide (e.g., BR-06: "The system must generate a non-negative numeric demand estimate for a valid ATM and target date with documented context and disclaimer").
