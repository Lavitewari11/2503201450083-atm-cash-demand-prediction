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


def inject_custom_css() -> None:
    """Inject global CSS rules to ensure consistent typography, comfortable spacing, and readability."""
    st.markdown("""
    <style>
      /* Global Typography & Content Container */
      .block-container {
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: 3rem !important;
        padding-right: 3rem !important;
        max-width: 95% !important;
      }
      html, body, [class*="css"], .stMarkdown {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        font-size: 15.5px !important;
        color: #0F172A !important;
        line-height: 1.6 !important;
      }
      /* Hierarchy Headings */
      h1 {
        font-size: 28px !important;
        font-weight: 700 !important;
        color: #0F172A !important;
        letter-spacing: -0.02em !important;
        margin-bottom: 0.75rem !important;
      }
      h2 {
        font-size: 23px !important;
        font-weight: 600 !important;
        color: #0F172A !important;
        margin-top: 1.25rem !important;
        margin-bottom: 0.6rem !important;
      }
      h3 {
        font-size: 20px !important;
        font-weight: 600 !important;
        color: #1E293B !important;
        margin-top: 1.1rem !important;
        margin-bottom: 0.5rem !important;
      }
      h4 {
        font-size: 18px !important;
        font-weight: 600 !important;
        color: #334155 !important;
      }
      .stCaption, caption {
        font-size: 13.5px !important;
        color: #64748B !important;
      }
      /* Left Sidebar Polish */
      section[data-testid="stSidebar"] {
        background-color: #F8FAFC !important;
        border-right: 1px solid #E2E8F0 !important;
        padding-top: 1rem !important;
      }
      section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
        font-size: 15px !important;
        font-weight: 500 !important;
        padding: 8px 12px !important;
        border-radius: 8px !important;
        margin-bottom: 3px !important;
        transition: all 0.15s ease-in-out !important;
      }
      section[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
        background-color: #EDF2F7 !important;
      }
      section[data-testid="stSidebar"] [aria-current="page"] {
        background-color: rgba(15, 118, 110, 0.12) !important;
        color: #0F766E !important;
        font-weight: 600 !important;
      }
      section[data-testid="stSidebar"] label {
        font-size: 14.5px !important;
        font-weight: 600 !important;
        color: #1E293B !important;
      }
      /* Tab and Dataframe Polish */
      button[data-baseweb="tab"] {
        font-size: 15.5px !important;
        font-weight: 600 !important;
        padding: 10px 18px !important;
      }
      [data-testid="stDataFrame"] {
        font-size: 14.5px !important;
        border: 1px solid #E2E8F0 !important;
        border-radius: 8px !important;
      }
      .stButton > button {
        font-size: 15px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
      }
    </style>
    """, unsafe_allow_html=True)


def render_header(title: str, subtitle: str = "ATM Cash Demand Prediction") -> None:
    """Render a modern enterprise header and inject global responsive styles."""
    inject_custom_css()
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle)
    html_content = f"""
    <!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="{TAILWIND_CDN}"></script>
    </head><body class="bg-transparent m-0 p-0 font-sans">
      <header class="rounded-xl px-6 py-5 text-white shadow-sm" style="background: linear-gradient(135deg, #0A2540 0%, #0F766E 100%);">
        <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-white m-0" style="font-size: 26px; line-height: 1.2;">{safe_title}</h1>
            <p class="text-sm sm:text-base text-slate-100 mt-1 m-0" style="font-size: 15px;">{safe_subtitle}</p>
          </div>
          <span class="rounded-full px-4 py-1.5 text-xs font-semibold self-start sm:self-auto uppercase tracking-wider" style="background: rgba(255,255,255,0.18); border: 1px solid rgba(255,255,255,0.25);">
            Enterprise Analytics
          </span>
        </div>
      </header>
    </body></html>"""
    try:
        st.components.v1.html(html_content, height=115, scrolling=False)
    except Exception:
        st.markdown(f"## {title}\n*{subtitle}*")


def render_kpi_card(label: str, value: str, helper: str = "") -> None:
    """Render one high-contrast, comfortably proportioned KPI card."""
    safe_label = html.escape(label)
    safe_value = html.escape(value)
    safe_helper = html.escape(helper)
    html_content = f"""
    <!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="{TAILWIND_CDN}"></script>
    </head><body class="bg-transparent m-0 p-0 font-sans">
      <section class="rounded-xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition" style="box-shadow: 0 1px 4px rgba(0,0,0,0.06);">
        <p class="font-semibold uppercase tracking-wider text-slate-500 m-0" style="font-size: 13.5px; letter-spacing: 0.05em;">{safe_label}</p>
        <p class="font-bold text-slate-900 m-0 break-words" style="font-size: 30px; margin-top: 6px; margin-bottom: 4px; line-height: 1.1;">{safe_value}</p>
        <p class="text-slate-500 m-0" style="font-size: 13px; line-height: 1.3;">{safe_helper}</p>
      </section>
    </body></html>"""
    try:
        st.components.v1.html(html_content, height=135, scrolling=False)
    except Exception:
        st.metric(label=label, value=value, help=helper)


def render_insight_box(finding: str, evidence: str = "", caveat: str = "") -> None:
    """Render an evidence-based insight box styled with clear typography."""
    safe_finding = html.escape(finding)
    safe_evidence = html.escape(evidence)
    safe_caveat = html.escape(caveat)
    evidence_html = f'<p class="mt-1 text-teal-900" style="font-size: 14px;"><strong>Evidence:</strong> {safe_evidence}</p>' if evidence else ''
    caveat_html = f'<p class="mt-1 text-amber-900" style="font-size: 13.5px;"><strong>Caveat:</strong> {safe_caveat}</p>' if caveat else ''
    html_content = f"""
    <!doctype html><html><head>
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <script src="{TAILWIND_CDN}"></script>
    </head><body class="bg-transparent m-0 p-0 font-sans">
      <div class="rounded-xl border-l-4 border-teal-600 bg-teal-50 p-4 shadow-sm" style="background-color: #F0FDFA; border-left: 5px solid #0F766E;">
        <p class="font-bold text-teal-950 m-0" style="font-size: 16px; color: #115E59;">{safe_finding}</p>
        {evidence_html}
        {caveat_html}
      </div>
    </body></html>"""
    try:
        st.components.v1.html(html_content, height=130, scrolling=False)
    except Exception:
        st.info(f"**{finding}**\n\n*Evidence:* {evidence}\n\n*Caveat:* {caveat}")


def apply_chart_theme(
    fig: Any,
    height: int = 420,
    title: Optional[str] = None,
    xaxis_title: Optional[str] = None,
    yaxis_title: Optional[str] = None,
    show_legend: bool = True
) -> Any:
    """Applies a consistent, enterprise-grade Plotly layout theme across all dashboard charts."""
    layout_update: Dict[str, Any] = dict(
        height=height,
        font=dict(family="'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif", size=13, color="#1E293B"),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=45, r=25, t=55 if title else 25, b=45),
        showlegend=show_legend,
        hoverlabel=dict(bgcolor="#0F172A", font_size=13, font_color="#FFFFFF", font_family="'Segoe UI', sans-serif"),
        xaxis=dict(
            showgrid=True,
            gridcolor="#F1F5F9",
            linecolor="#CBD5E1",
            tickfont=dict(size=12.5, color="#475569"),
            title=dict(font=dict(size=14, color="#334155", family="'Segoe UI', sans-serif"))
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#E2E8F0",
            linecolor="#CBD5E1",
            tickfont=dict(size=12.5, color="#475569"),
            title=dict(font=dict(size=14, color="#334155", family="'Segoe UI', sans-serif"))
        )
    )
    if title:
        layout_update["title"] = dict(
            text=title,
            font=dict(size=19, color="#0F172A", family="'Segoe UI', sans-serif"),
            x=0.01,
            y=0.97
        )
    if xaxis_title:
        layout_update["xaxis"]["title"]["text"] = xaxis_title
    if yaxis_title:
        layout_update["yaxis"]["title"]["text"] = yaxis_title
    if show_legend:
        layout_update["legend"] = dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=13, color="#334155")
        )

    fig.update_layout(**layout_update)
    return fig


def render_empty_state(message: str = "No records match the current filter selection.") -> None:
    """Render a clean empty state alert with reset filters guidance."""
    st.warning(f"ℹ️ {message}\n\n*Tip: Try expanding the Historical Date Range or resetting the sidebar filters to 'All'.*")


def ensure_pages_registered() -> None:
    """
    Ensure all application pages are fully registered in Streamlit's PagesManager
    with guaranteed 'url_pathname' fields to eliminate KeyError: 'url_pathname'.
    """
    try:
        from pathlib import Path
        import hashlib
        from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx
        from streamlit.source_util import page_sort_key, page_icon_and_name

        ctx = get_script_run_ctx()
        if not ctx or not ctx.pages_manager:
            return

        pages = ctx.pages_manager.get_pages()
        needs_reg = any("url_pathname" not in p for p in pages.values()) or len(pages) <= 1
        if needs_reg:
            root_dir = Path(__file__).resolve().parents[1]
            pages_folder = root_dir / "pages"
            if pages_folder.exists():
                pages_dict = {}
                main_hash = ctx.pages_manager.main_script_hash or "main"
                pages_dict[main_hash] = {
                    "page_script_hash": main_hash,
                    "page_name": "Home",
                    "icon": "🏠",
                    "script_path": str(root_dir / "app.py"),
                    "url_pathname": ""
                }
                for p in sorted(pages_folder.glob("*.py"), key=page_sort_key):
                    if p.name.endswith(".py") and not p.name.startswith(".") and p.name != "__init__.py":
                        icon, name = page_icon_and_name(p)
                        p_hash = hashlib.md5(str(p.resolve()).encode("utf-8")).hexdigest()
                        pages_dict[p_hash] = {
                            "page_script_hash": p_hash,
                            "page_name": name.replace("_", " "),
                            "icon": icon,
                            "script_path": str(p.resolve()),
                            "url_pathname": name
                        }
                ctx.pages_manager.set_pages(pages_dict)

        # Defensive pass: guarantee url_pathname is present on every single entry
        for p in ctx.pages_manager.get_pages().values():
            if "url_pathname" not in p:
                p["url_pathname"] = p.get("page_name", "")
    except Exception:
        pass


def safe_page_link(
    page: Any,
    label: str,
    icon: Optional[str] = None,
    help: Optional[str] = None,
    use_container_width: bool = True
) -> None:
    """Safely render st.page_link with support for st.Page objects, strings, guaranteed registration, and defensive fallback."""
    ensure_pages_registered()
    try:
        st.page_link(page, label=label, icon=icon, help=help, use_container_width=use_container_width)
    except Exception:
        # Fallback when running outside active multipage router context
        if isinstance(page, str):
            route = page.replace("pages/", "").replace(".py", "")
            if route == "app":
                route = "Home Hub"
        else:
            route = getattr(page, "title", str(page))
        st.caption(f"{icon or '🔗'} **{label}** (`{route}`)")



def render_top_nav(current_page: str = "") -> None:
    """Render top breadcrumb and navigation back to the homepage hub and between modules."""
    col_nav1, col_nav2 = st.columns([2.5, 7.5])
    with col_nav1:
        safe_page_link("app.py", label="Home Hub", icon="🏠", help="Return to Main Analytics Hub", use_container_width=False)
    with col_nav2:
        if current_page:
            st.caption(f"📍 Location: **Home Hub** › **{current_page}**")


def render_bottom_nav(
    prev_page: Optional[tuple[str, str, str]] = None,
    next_page: Optional[tuple[str, str, str]] = None
) -> None:
    """Render bottom navigation controls between pages and back to the homepage."""
    st.markdown("---")
    c_prev, c_home, c_next = st.columns([4, 2, 4])
    with c_prev:
        if prev_page:
            safe_page_link(prev_page[0], label=f"⬅️ {prev_page[1]}", icon=prev_page[2], use_container_width=True)
    with c_home:
        safe_page_link("app.py", label="Home Hub", icon="🏠", use_container_width=True)
    with c_next:
        if next_page:
            safe_page_link(next_page[0], label=f"{next_page[1]} ➡️", icon=next_page[2], use_container_width=True)




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
        if st.button("🔄 Reset All Filters", use_container_width=True, key="btn_reset_filters"):
            st.session_state["selected_start_date"] = default_start
            st.session_state["selected_end_date"] = default_end
            st.session_state["selected_atm"] = "All ATMs"
            st.session_state["selected_region"] = "All regions"
            st.session_state["selected_site_type"] = "All site types"
            st.rerun()

        st.caption("⚠️ **Notice (BR-12):** Academic decision-support prototype. Data is fictional and synthetic.")

    return {
        "start_date": st.session_state["selected_start_date"],
        "end_date": st.session_state["selected_end_date"],
        "atm_id": None if st.session_state["selected_atm"] == "All ATMs" else st.session_state["selected_atm"],
        "region": None if st.session_state["selected_region"] == "All regions" else st.session_state["selected_region"],
        "site_type": None if st.session_state["selected_site_type"] == "All site types" else st.session_state["selected_site_type"]
    }
