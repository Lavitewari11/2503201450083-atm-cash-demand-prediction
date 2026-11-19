"""
Generate the ATM Cash Demand Prediction synthetic dataset.
Reproducible seed: 42
Run from repository root: python src/generate_data.py
All records are fictional and synthetic.
"""
from pathlib import Path
import sqlite3
import random
from datetime import date, datetime, timedelta
import numpy as np
import pandas as pd

SEED = 42
random.seed(SEED)
rng = np.random.default_rng(SEED)

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

TABLE_COLUMNS = {
    "atm_master": ["atm_id", "atm_name", "area_name", "site_type", "is_active", "install_date"],
    "date_dim": ["date_key", "date_value", "day_of_month", "day_of_week_num",
                 "day_of_week_name", "week_of_year", "month_num", "month_name",
                 "quarter_num", "year_num", "season_name", "is_weekend", "is_holiday"],
    "atm_daily_fact": ["atm_id", "date_key", "withdrawal_amount_inr",
                       "replenished_amount_inr", "transaction_count", "opening_balance_inr",
                       "closing_balance_inr", "source_batch_id", "record_created_at"],
    "atm_forecast_fact": ["atm_id", "target_date_key", "predicted_withdrawal_inr",
                          "model_name", "model_version", "generated_at",
                          "training_start_key", "training_end_key", "evaluation_split", "is_baseline"],
}

DDL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS atm_master (
 atm_id TEXT PRIMARY KEY NOT NULL,
 atm_name TEXT NOT NULL UNIQUE,
 area_name TEXT NOT NULL,
 site_type TEXT NOT NULL CHECK(site_type IN ('Branch','Market','Transit','Residential','Office')),
 is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1)),
 install_date TEXT CHECK(install_date IS NULL OR date(install_date) IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS date_dim (
 date_key INTEGER PRIMARY KEY NOT NULL CHECK(date_key BETWEEN 19000101 AND 29991231),
 date_value TEXT NOT NULL UNIQUE CHECK(date(date_value) IS NOT NULL),
 day_of_month INTEGER NOT NULL CHECK(day_of_month BETWEEN 1 AND 31),
 day_of_week_num INTEGER NOT NULL CHECK(day_of_week_num BETWEEN 1 AND 7),
 day_of_week_name TEXT NOT NULL CHECK(day_of_week_name IN ('Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')),
 week_of_year INTEGER NOT NULL CHECK(week_of_year BETWEEN 1 AND 53),
 month_num INTEGER NOT NULL CHECK(month_num BETWEEN 1 AND 12),
 month_name TEXT NOT NULL CHECK(month_name IN ('January','February','March','April','May','June','July','August','September','October','November','December')),
 quarter_num INTEGER NOT NULL CHECK(quarter_num BETWEEN 1 AND 4),
 year_num INTEGER NOT NULL CHECK(year_num BETWEEN 1900 AND 2999),
 season_name TEXT CHECK(season_name IS NULL OR season_name IN ('Summer','Monsoon','Winter','Other')),
 is_weekend INTEGER NOT NULL CHECK(is_weekend IN (0,1)),
 is_holiday INTEGER CHECK(is_holiday IS NULL OR is_holiday IN (0,1))
);

CREATE TABLE IF NOT EXISTS atm_daily_fact (
 atm_id TEXT NOT NULL,
 date_key INTEGER NOT NULL,
 withdrawal_amount_inr REAL NOT NULL CHECK(withdrawal_amount_inr >= 0),
 replenished_amount_inr REAL CHECK(replenished_amount_inr IS NULL OR replenished_amount_inr >= 0),
 transaction_count INTEGER CHECK(transaction_count IS NULL OR transaction_count >= 0),
 opening_balance_inr REAL CHECK(opening_balance_inr IS NULL OR opening_balance_inr >= 0),
 closing_balance_inr REAL CHECK(closing_balance_inr IS NULL OR closing_balance_inr >= 0),
 source_batch_id TEXT,
 record_created_at TEXT NOT NULL,
 PRIMARY KEY(atm_id,date_key),
 FOREIGN KEY(atm_id) REFERENCES atm_master(atm_id) ON UPDATE CASCADE ON DELETE RESTRICT,
 FOREIGN KEY(date_key) REFERENCES date_dim(date_key) ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS atm_forecast_fact (
 atm_id TEXT NOT NULL,
 target_date_key INTEGER NOT NULL,
 predicted_withdrawal_inr REAL NOT NULL CHECK(predicted_withdrawal_inr >= 0),
 model_name TEXT NOT NULL CHECK(length(trim(model_name)) > 0),
 model_version TEXT NOT NULL CHECK(length(trim(model_version)) > 0),
 generated_at TEXT NOT NULL,
 training_start_key INTEGER,
 training_end_key INTEGER,
 evaluation_split TEXT CHECK(evaluation_split IS NULL OR evaluation_split IN ('train','validation','test','production_demo')),
 is_baseline INTEGER NOT NULL DEFAULT 0 CHECK(is_baseline IN (0,1)),
 PRIMARY KEY(atm_id,target_date_key,model_version,generated_at),
 FOREIGN KEY(atm_id) REFERENCES atm_master(atm_id) ON UPDATE CASCADE ON DELETE RESTRICT,
 FOREIGN KEY(target_date_key) REFERENCES date_dim(date_key) ON UPDATE CASCADE ON DELETE RESTRICT,
 FOREIGN KEY(training_start_key) REFERENCES date_dim(date_key) ON UPDATE CASCADE ON DELETE SET NULL,
 FOREIGN KEY(training_end_key) REFERENCES date_dim(date_key) ON UPDATE CASCADE ON DELETE SET NULL,
 CHECK(training_start_key IS NULL OR training_end_key IS NULL OR training_start_key <= training_end_key)
);

CREATE INDEX IF NOT EXISTS idx_daily_date ON atm_daily_fact(date_key);
CREATE INDEX IF NOT EXISTS idx_forecast_target ON atm_forecast_fact(target_date_key);
CREATE INDEX IF NOT EXISTS idx_atm_area ON atm_master(area_name);

CREATE VIEW IF NOT EXISTS vw_atm_daily_analysis AS
SELECT f.atm_id,a.atm_name,a.area_name,a.site_type,a.is_active,a.install_date,
 d.date_key,d.date_value,d.day_of_month,d.day_of_week_num,d.day_of_week_name,
 d.week_of_year,d.month_num,d.month_name,d.quarter_num,d.year_num,d.season_name,
 d.is_weekend,d.is_holiday,
 f.withdrawal_amount_inr,f.replenished_amount_inr,f.transaction_count,
 f.opening_balance_inr,f.closing_balance_inr,f.source_batch_id,f.record_created_at,
 p.predicted_withdrawal_inr,p.model_name,p.model_version,p.generated_at,
 p.training_start_key,p.training_end_key,p.evaluation_split,p.is_baseline
FROM atm_daily_fact f
JOIN atm_master a ON a.atm_id=f.atm_id
JOIN date_dim d ON d.date_key=f.date_key
LEFT JOIN atm_forecast_fact p ON p.atm_id=f.atm_id AND p.target_date_key=f.date_key;
"""

AREAS = ["Sector 18, Noida", "Sector 62, Noida", "Indirapuram, Ghaziabad",
         "Vaishali, Ghaziabad", "Raj Nagar, Ghaziabad", "Sector 137, Noida",
         "Crossings Republik, Ghaziabad", "Sector 50, Noida", "Kaushambi, Ghaziabad",
         "Sector 15, Noida"]
SITE_TYPES = ["Branch", "Market", "Transit", "Residential", "Office"]
NAME_BITS = ["Aarav", "Ishita", "Kabir", "Meera", "Vihaan", "Anaya", "Reyansh",
             "Saanvi", "Advait", "Diya", "Arjun", "Myra", "Vivaan", "Aadhya",
             "Rohan", "Kiara", "Ishaan", "Tara", "Dev", "Naina"]
SUFFIXES = ["Digital Point", "Cash Hub", "Metro Kiosk", "Market ATM", "Banking Point"]

def date_key(d):
    return int(d.strftime("%Y%m%d"))

def season_for(month):
    if month in (3, 4, 5, 6): return "Summer"
    if month in (7, 8, 9): return "Monsoon"
    if month in (11, 12, 1, 2): return "Winter"
    return "Other"

def main():
    # 50 fictional ATM master rows
    atms = []
    for i in range(50):
        area = AREAS[i % len(AREAS)]
        site = SITE_TYPES[(i * 3 + i // 5) % len(SITE_TYPES)]
        atms.append({
            "atm_id": f"ATM-{i+1:03d}",
            "atm_name": f"{NAME_BITS[i % len(NAME_BITS)]} {SUFFIXES[i % len(SUFFIXES)]} {i+1:02d}",
            "area_name": area,
            "site_type": site,
            "is_active": 0 if i in (47, 49) else 1,
            "install_date": (date(2019, 1, 1) + timedelta(days=int(rng.integers(0, 1800)))).isoformat()
        })
    atm_df = pd.DataFrame(atms, columns=TABLE_COLUMNS["atm_master"])

    # 730 consecutive dates: 2024-01-01 through 2025-12-30
    start = date(2024, 1, 1)
    dates = [start + timedelta(days=i) for i in range(730)]
    holidays = {(1, 26), (8, 15), (10, 2)}
    date_rows = []
    for d in dates:
        iso_week = d.isocalendar()
        # Illustrative synthetic holiday labels; NULL means calendar status unknown.
        holiday_flag = 1 if (d.month, d.day) in holidays else (None if d.day == 13 and d.month in (2, 6, 9) else 0)
        date_rows.append({
            "date_key": date_key(d), "date_value": d.isoformat(),
            "day_of_month": d.day, "day_of_week_num": d.isoweekday(),
            "day_of_week_name": d.strftime("%A"), "week_of_year": iso_week.week,
            "month_num": d.month, "month_name": d.strftime("%B"),
            "quarter_num": (d.month - 1)//3 + 1, "year_num": d.year,
            "season_name": season_for(d.month), "is_weekend": int(d.weekday() >= 5),
            "is_holiday": holiday_flag
        })
    date_df = pd.DataFrame(date_rows, columns=TABLE_COLUMNS["date_dim"])

    # 250 ATM-date observations, spread over 50 ATMs and 24 months.
    # Sampling is deterministic and covers all weekdays/months for pattern discovery.
    chosen_pairs = []
    for atm_i in range(50):
        candidate_days = np.linspace(0, 729, 5, dtype=int)
        jitter = rng.integers(-18, 19, size=5)
        for day_i, j in zip(candidate_days, jitter):
            idx = int(np.clip(day_i + int(j), 0, 729))
            chosen_pairs.append((atm_i, idx))
    # Ensure unique ATM/date pairs.
    unique = {}
    for ai, di in chosen_pairs:
        unique[(ai, di)] = True
    pairs = list(unique.keys())
    while len(pairs) < 250:
        ai = int(rng.integers(0, 50)); di = int(rng.integers(0, 730))
        if (ai, di) not in unique:
            unique[(ai, di)] = True; pairs.append((ai, di))
    pairs = pairs[:250]

    daily_rows = []
    atm_base = rng.uniform(18000, 62000, size=50)
    high_volume = {2, 7, 12, 17, 22, 27}  # deliberately stronger transit/market cohort
    for n, (ai, di) in enumerate(pairs):
        d = dates[di]
        atm = atms[ai]
        base_amt = atm_base[ai] * (1.28 if ai in high_volume else 1.0)
        weekday_factor = [0.90, 0.94, 0.98, 1.00, 1.08, 1.24, 1.16][d.weekday()]
        # Seasonal demand: summer higher; monsoon mildly lower; winter moderate.
        seasonal = 1.16 if d.month in (4, 5, 6) else (0.91 if d.month in (7, 8, 9) else 1.0)
        month_end = 1.13 if d.day >= 25 else 1.0
        festival_window = 1.22 if (d.month in (10, 11) and 5 <= d.day <= 20) else 1.0
        noise = float(rng.normal(1.0, 0.085))
        withdrawal = max(2500.0, base_amt * weekday_factor * seasonal * month_end * festival_window * noise)
        # A handful of deliberately high but valid demand outliers.
        if n in (19, 103, 211):
            withdrawal *= 2.7
        tx_count = max(1, int(withdrawal / rng.uniform(950, 1450)))
        replenished = max(0.0, withdrawal * float(rng.uniform(0.78, 1.24)))
        opening = float(rng.uniform(80000, 180000))
        closing = max(0.0, opening + replenished - withdrawal)
        daily_rows.append({
            "atm_id": atm["atm_id"], "date_key": date_key(d),
            "withdrawal_amount_inr": round(withdrawal, 2),
            "replenished_amount_inr": round(replenished, 2),
            "transaction_count": tx_count,
            "opening_balance_inr": round(opening, 2),
            "closing_balance_inr": round(closing, 2),
            "source_batch_id": f"BATCH-{d:%Y%m}-{(n%4)+1:02d}",
            "record_created_at": datetime.combine(d, datetime.min.time()).replace(hour=22, minute=15).isoformat(sep=" ")
        })
    daily_df = pd.DataFrame(daily_rows, columns=TABLE_COLUMNS["atm_daily_fact"])

    # Add controlled NULLs only to nullable fields: roughly 2-3% of optional cells.
    optional_cols = ["replenished_amount_inr", "transaction_count",
                     "opening_balance_inr", "closing_balance_inr", "source_batch_id"]
    null_targets = [(3, "replenished_amount_inr"), (31, "transaction_count"),
                    (76, "opening_balance_inr"), (142, "closing_balance_inr"),
                    (205, "source_batch_id"), (224, "replenished_amount_inr")]
    for row_i, col in null_targets:
        daily_df.loc[row_i, col] = None

    # Forecasts: 75 rows for 15 target dates x 5 selected ATMs.
    forecast_rows = []
    target_indices = [720, 722, 724, 726, 728]
    selected_atms = [0, 2, 7, 12, 17, 22, 27, 32, 37, 42, 47, 49, 5, 10, 15]
    # 15 x 5 = 75, five ATMs each target date; deterministic rotating sample.
    for ti, di in enumerate(target_indices):
        target = dates[di]
        for j in range(15):
            ai = selected_atms[(j + ti) % len(selected_atms)]
            base_amt = atm_base[ai] * (1.28 if ai in high_volume else 1.0)
            weekday_factor = [0.90, 0.94, 0.98, 1.00, 1.08, 1.24, 1.16][target.weekday()]
            pred = base_amt * weekday_factor * (1.10 if target.month in (4,5,6) else 1.0) * float(rng.normal(1.0,0.035))
            forecast_rows.append({
                "atm_id": atms[ai]["atm_id"], "target_date_key": date_key(target),
                "predicted_withdrawal_inr": round(max(0.0, pred), 2),
                "model_name": "Seasonal Naive Baseline" if j % 3 == 0 else "Moving Average",
                "model_version": "v1.0-baseline" if j % 3 == 0 else "v1.0-ma7",
                "generated_at": datetime(2025, 12, 20, 9, 0).isoformat(sep=" "),
                "training_start_key": date_key(dates[0]),
                "training_end_key": date_key(dates[699]),
                "evaluation_split": "production_demo" if target > dates[699] else "test",
                "is_baseline": 1 if j % 3 == 0 else 0
            })
    forecast_df = pd.DataFrame(forecast_rows, columns=TABLE_COLUMNS["atm_forecast_fact"])

    # Data-quality examples are kept OUTSIDE constrained production tables:
    # 3 duplicate candidates in a separate raw QA file so PKs remain valid.
    duplicate_rows = daily_df.iloc[[5, 55, 155]].copy()
    duplicate_rows["source_batch_id"] = "QA-DUPLICATE-CANDIDATE"
    duplicate_rows["qa_issue"] = "Duplicate ATM-date candidate; reject/deduplicate before SQLite load"
    duplicate_rows.to_csv(DATA_DIR / "duplicate_candidates_for_cleaning.csv", index=False)

    # Export clean tables to CSV.
    frames = {"atm_master": atm_df, "date_dim": date_df,
              "atm_daily_fact": daily_df, "atm_forecast_fact": forecast_df}
    for table, frame in frames.items():
        frame.to_csv(DATA_DIR / f"{table}.csv", index=False)

    # Create SQLite DB with the exact Step 8 DDL and load valid rows.
    db_path = DATA_DIR / "app.db"
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    con.executescript(DDL)
    atm_df.to_sql("atm_master", con, if_exists="append", index=False)
    date_df.to_sql("date_dim", con, if_exists="append", index=False)
    daily_df.to_sql("atm_daily_fact", con, if_exists="append", index=False)
    forecast_df.to_sql("atm_forecast_fact", con, if_exists="append", index=False)
    con.commit()

    # Build workbook: one sheet per table, plus QA notes and view preview.
    xlsx_path = DATA_DIR / "atm_cash_demand_prediction_data.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        for table, frame in frames.items():
            frame.to_excel(writer, sheet_name=table[:31], index=False)
        duplicate_rows.to_excel(writer, sheet_name="QA_Duplicate_Candidates", index=False)
        pd.read_sql_query("SELECT * FROM vw_atm_daily_analysis LIMIT 100", con).to_excel(
            writer, sheet_name="Joined_View_Preview", index=False)
    con.close()

    # Validation report
    con = sqlite3.connect(db_path)
    con.execute("PRAGMA foreign_keys = ON")
    fk_violations = con.execute("PRAGMA foreign_key_check").fetchall()
    counts = {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLE_COLUMNS}
    view_cols = [r[1] for r in con.execute("PRAGMA table_info(vw_atm_daily_analysis)").fetchall()]
    range_checks = {
        "withdrawal_nonnegative": con.execute("SELECT COUNT(*) FROM atm_daily_fact WHERE withdrawal_amount_inr < 0").fetchone()[0] == 0,
        "forecast_nonnegative": con.execute("SELECT COUNT(*) FROM atm_forecast_fact WHERE predicted_withdrawal_inr < 0").fetchone()[0] == 0,
        "allowed_site_types": con.execute("SELECT COUNT(*) FROM atm_master WHERE site_type NOT IN ('Branch','Market','Transit','Residential','Office')").fetchone()[0] == 0,
        "date_key_matches_date": con.execute("SELECT COUNT(*) FROM date_dim WHERE date_key != CAST(REPLACE(date_value,'-','') AS INTEGER)").fetchone()[0] == 0,
        "unique_daily_grain": con.execute("SELECT COUNT(*) FROM (SELECT atm_id,date_key,COUNT(*) c FROM atm_daily_fact GROUP BY atm_id,date_key HAVING c>1)").fetchone()[0] == 0,
    }
    report = [
        "ATM CASH DEMAND PREDICTION — DATA VALIDATION REPORT",
        f"Seed: {SEED}",
        "All records are synthetic and fictional.",
        "",
        "ROW COUNTS"
    ]
    report += [f"{k}: {v}" for k,v in counts.items()]
    report += ["", f"Joined view column count: {len(view_cols)}",
               f"Foreign-key violations: {len(fk_violations)}",
               f"Foreign-key check: {'PASS' if not fk_violations else 'FAIL'}",
               "", "RANGE / KEY CHECKS"]
    report += [f"{k}: {'PASS' if v else 'FAIL'}" for k,v in range_checks.items()]
    report += ["", "DATA-QUALITY ISSUES INTENTIONALLY INCLUDED",
               "1. Six NULL values across nullable daily-fact fields (about 2.4% of 250 fact rows).",
               "2. Three duplicate ATM-date candidates in duplicate_candidates_for_cleaning.csv; excluded from constrained base tables.",
               "3. Three unusually high withdrawal observations (2.7x uplift), still non-negative and valid under DDL.",
               "", "PATTERNS INTENTIONALLY EMBEDDED",
               "1. Saturday/Sunday demand is generally higher than Monday–Thursday.",
               "2. Summer demand (April–June) is elevated; monsoon (July–September) is softer.",
               "3. Month-end demand (day 25 onward) is elevated.",
               "4. A selected high-volume ATM cohort has a higher underlying demand level.",
               "5. A pre-festival October/November window has a demand uplift.",
               "", "NOTE: The Joined_View preview may contain repeated daily rows when multiple forecast runs exist for the same ATM/date. Filter to one selected run before daily-grain aggregation.",
               f"SQLite database: {db_path.name}",
               f"Excel workbook: {xlsx_path.name}"]
    report_path = DATA_DIR / "validation_report.txt"
    report_path.write_text("\\n".join(report), encoding="utf-8")
    con.close()
    print("\\n".join(report))
    print("\\nCreated files:")
    for path in sorted(DATA_DIR.iterdir()):
        if path.is_file():
            print(f"- {path.name} ({path.stat().st_size:,} bytes)")

if __name__ == "__main__":
    main()
