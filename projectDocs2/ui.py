from __future__ import annotations
import streamlit as st

TAILWIND_CDN = "https://cdn.tailwindcss.com"

def render_header(title: str, subtitle: str = "ATM Cash Demand Prediction") -> None:
    """Render a Tailwind-styled, presentational header in an HTML iframe."""
    html = f"""
    <!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="{TAILWIND_CDN}"></script>
    </head><body class="bg-slate-50">
      <header class="rounded-xl bg-[#12304A] px-5 py-4 text-white shadow-sm">
        <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
          <div><h1 class="text-xl font-bold">{title}</h1>
          <p class="text-sm text-slate-200">{subtitle}</p></div>
          <span class="rounded-full bg-teal-700 px-3 py-1 text-xs">Analytics workspace</span>
        </div>
      </header>
    </body></html>"""
    st.components.v1.html(html, height=112, scrolling=False)

def render_kpi_card(label: str, value: str, helper: str = "") -> None:
    """Render one Tailwind KPI card in an HTML iframe."""
    html = f"""
    <!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="{TAILWIND_CDN}"></script>
    </head><body class="bg-transparent">
      <section class="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
        <p class="text-sm font-medium text-slate-500">{label}</p>
        <p class="mt-2 break-words text-2xl font-semibold text-slate-900">{value}</p>
        <p class="mt-1 text-xs text-slate-500">{helper}</p>
      </section>
    </body></html>"""
    st.components.v1.html(html, height=132, scrolling=False)

def init_shared_filters() -> dict:
    """Create shared filters using Streamlit session state."""
    defaults = {"selected_atm":"All ATMs", "selected_region":"All regions",
                "selected_site_type":"All site types"}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    with st.sidebar:
        st.subheader("Shared filters")
        atm = st.text_input("ATM ID", key="selected_atm")
        region = st.text_input("Region", key="selected_region")
        site_type = st.text_input("Site type", key="selected_site_type")
    return {"atm":atm.strip(), "region":region.strip(), "site_type":site_type.strip()}
