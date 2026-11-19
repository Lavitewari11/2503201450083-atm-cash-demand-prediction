"""Streamlit smoke tests. Activate when Step 15 page entry points are available."""
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"
PAGES = [
    "pages/1_Overview.py",
    "pages/2_Trend_Analysis.py",
    "pages/3_ATM_Comparison.py",
    "pages/4_EDA_Statistics.py",
    "pages/5_Forecast_Insights.py",
    "pages/6_Data_Explorer.py",
    "pages/7_Data_Quality.py",
    "pages/8_About_Methodology.py",
]

def test_app_entry_point_exists():
    if not APP.exists():
        pytest.xfail("app.py is scheduled for implementation in Step 15")
    assert APP.is_file()

def test_all_page_entry_points_exist():
    missing = [p for p in PAGES if not (ROOT / p).is_file()]
    if missing:
        pytest.xfail("Streamlit pages are scheduled for implementation in Step 15: " + ", ".join(missing))
    assert not missing

def test_streamlit_apptest_smoke():
    streamlit_testing = pytest.importorskip("streamlit.testing.v1")
    if not APP.exists():
        pytest.xfail("app.py is scheduled for implementation in Step 15")
    at = streamlit_testing.AppTest.from_file(str(APP), default_timeout=3).run()
    assert not at.exception
