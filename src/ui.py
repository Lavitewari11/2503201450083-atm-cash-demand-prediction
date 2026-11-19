"""
UI Framework and Reusable Components (conforms strictly to Step 12 UI Framework & BUILD-07).
Provides Tailwind-styled presentation headers, KPI cards, shared sidebar filters, and insight boxes.
"""
from __future__ import annotations
import html
from datetime import date
from typing import Dict, Any, Optional
import streamlit as st
import pandas as pd

TAILWIND_CDN = "https://cdn.tailwindcss.com"


def render_header(title: str, subtitle: str = "ATM Cash Demand Prediction") -> None:
    """Render a Tailwind-styled, presentational header in an HTML iframe with clean native fallback."""
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    html_content = f"""
    <!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="{TAILWIND_CDN}"></script>
    </head><body class="bg-slate-50 m-0 p-0 font-sans">
      <header class="rounded-xl bg-[#12304A] px-5 py-4 text-white shadow-sm">
        <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 class="text-xl font-bold tracking-tight">{safe_title}</h1>
            <p class="text-sm text-slate-200 mt-0.5">{safe_subtitle}</p>
          </div>
          <span class="rounded-full bg-teal-700 px-3 py-1 text-xs font-medium self-start sm:self-auto">
            Analytics workspace
          </span>
        </div>
      </header>
    </body></html>"""
    try:
        st.components.v1.html(html_content, height=105, scrolling=False)
    except Exception:
        # Fallback to native Streamlit markdown
        st.markdown(f"## {title}\n*{subtitle}*")


def render_kpi_card(label: str, value: str, helper: str = "") -> None:
    """Render one Tailwind KPI card in an HTML iframe."""
    safe_label = html.escape(label)
    safe_value = html.escape(value)
    safe_helper = html.escape(helper)
    html_content = f"""
    <!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="{TAILWIND_CDN}"></script>
    </head><body class="bg-transparent m-0 p-0 font-sans">
      <section class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:shadow-md transition">
        <p class="text-xs font-semibold uppercase tracking-wider text-slate-500">{safe_label}</p>
        <p class="mt-2 break-words text-2xl font-bold text-slate-900">{safe_value}</p>
        <p class="mt-1 text-xs text-slate-500">{safe_helper}</p>
      </section>
    </body></html>"""
    try:
        st.components.v1.html(html_content, height=125, scrolling=False)
    except Exception:
        st.metric(label=label, value=value, help=helper)


def render_insight_box(finding: str, evidence: str = "", caveat: str = "") -> None:
    """Render an evidence-based insight box styled per Step 12 Table 1."""
    safe_finding = html.escape(finding)
    safe_evidence = html.escape(evidence)
    safe_caveat = html.escape(caveat)
    evidence_html = f'<p class="mt-1 text-xs text-teal-800"><strong>Evidence:</strong> {safe_evidence}</p>' if evidence else ''
    caveat_html = f'<p class="mt-1 text-xs text-amber-800"><strong>Caveat:</strong> {safe_caveat}</p>' if caveat else ''
    html_content = f"""
    <!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="{TAILWIND_CDN}"></script>
    </head><body class="bg-transparent m-0 p-0 font-sans">
      <div class="rounded-xl border-l-4 border-teal-600 bg-teal-50 p-4 text-sm text-teal-950 shadow-sm">
        <p class="font-semibold text-teal-900">{safe_finding}</p>
        {evidence_html}
        {caveat_html}
      </div>
    </body></html>"""
    try:
        st.components.v1.html(html_content, height=115, scrolling=False)
    except Exception:
        st.info(f"**{finding}**\n\n*Evidence:* {evidence}\n\n*Caveat:* {caveat}")


def render_empty_state(message: str = "No records match the current filter selection.") -> None:
    """Render a clean empty state alert."""
    st.warning(f"ℹ️ {message}")


def init_shared_filters(
    atms_df: Optional[pd.DataFrame] = None,
    calendar_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Create shared filters using Streamlit session state (Step 12 & BUILD-07).
    Keys managed:
    - selected_start_date
    - selected_end_date
    - selected_atm
    - selected_region
    - selected_site_type
    - selected_metric
    - selected_target_date
    - selected_model_version
    """
    default_start = date(2024, 1, 1)
    default_end = date(2025, 12, 30)

    if calendar_df is not None and not calendar_df.empty:
        if "date_value" in calendar_df.columns:
            d_vals = pd.to_datetime(calendar_df["date_value"]).dt.date
            default_start = min(d_vals)
            default_end = max(d_vals)

    defaults = {
        "selected_start_date": default_start,
        "selected_end_date": default_end,
        "selected_atm": "All ATMs",
        "selected_region": "All regions",
        "selected_site_type": "All site types",
        "selected_metric": "Total Withdrawn",
        "selected_target_date": date(2026, 1, 5),
        "selected_model_version": "v1.0-baseline"
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    with st.sidebar:
        st.markdown("### 🏦 ATM Cash Analytics")
        st.caption("Fictional Noida Bank Network (~50 ATMs)")
        st.markdown("---")
        st.subheader("Filter Scope")

        # Date Range Filter
        d_range = st.date_input(
            "Historical Date Range",
            value=(st.session_state["selected_start_date"], st.session_state["selected_end_date"]),
            min_value=default_start,
            max_value=default_end,
            key="_ui_date_range"
        )
        if isinstance(d_range, tuple) and len(d_range) == 2:
            st.session_state["selected_start_date"] = d_range[0]
            st.session_state["selected_end_date"] = d_range[1]
        elif isinstance(d_range, tuple) and len(d_range) == 1:
            st.session_state["selected_start_date"] = d_range[0]
            st.session_state["selected_end_date"] = d_range[0]

        # ATM Selector
        atm_opts = ["All ATMs"]
        if atms_df is not None and not atms_df.empty:
            atm_opts += sorted(atms_df["atm_id"].unique().tolist())
        current_atm = st.session_state.get("selected_atm", "All ATMs")
        atm_idx = atm_opts.index(current_atm) if current_atm in atm_opts else 0
        st.session_state["selected_atm"] = st.selectbox("ATM ID", atm_opts, index=atm_idx)

        # Region / Area Selector
        reg_opts = ["All regions"]
        if atms_df is not None and not atms_df.empty and "area_name" in atms_df.columns:
            reg_opts += sorted(atms_df["area_name"].dropna().unique().tolist())
        current_reg = st.session_state.get("selected_region", "All regions")
        reg_idx = reg_opts.index(current_reg) if current_reg in reg_opts else 0
        st.session_state["selected_region"] = st.selectbox("Region / Area", reg_opts, index=reg_idx)

        # Site Type Selector
        site_opts = ["All site types"]
        if atms_df is not None and not atms_df.empty and "site_type" in atms_df.columns:
            site_opts += sorted(atms_df["site_type"].dropna().unique().tolist())
        current_site = st.session_state.get("selected_site_type", "All site types")
        site_idx = site_opts.index(current_site) if current_site in site_opts else 0
        st.session_state["selected_site_type"] = st.selectbox("Site Type", site_opts, index=site_idx)

        st.markdown("---")
        st.caption("⚠️ **Notice (BR-12):** Academic decision-support prototype. Data is fictional and synthetic.")

    return {
        "start_date": st.session_state["selected_start_date"],
        "end_date": st.session_state["selected_end_date"],
        "atm_id": None if st.session_state["selected_atm"] == "All ATMs" else st.session_state["selected_atm"],
        "region": None if st.session_state["selected_region"] == "All regions" else st.session_state["selected_region"],
        "site_type": None if st.session_state["selected_site_type"] == "All site types" else st.session_state["selected_site_type"]
    }
