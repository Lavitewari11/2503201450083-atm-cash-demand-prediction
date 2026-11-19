"""
Utility and helper functions for formatting, date parsing, and visual themes.
"""
from datetime import datetime, date
from typing import Union, Optional
import pandas as pd


def date_to_key(d: Union[str, date, datetime, pd.Timestamp]) -> int:
    """Convert a date object or ISO string to integer YYYYMMDD."""
    if isinstance(d, str):
        d = datetime.fromisoformat(d.strip()).date()
    elif isinstance(d, datetime):
        d = d.date()
    elif isinstance(d, pd.Timestamp):
        d = d.date()
    return int(d.strftime("%Y%m%d"))


def key_to_date(k: Union[int, str]) -> date:
    """Convert integer or string YYYYMMDD to datetime.date object."""
    s = str(k).strip()
    return datetime.strptime(s, "%Y%m%d").date()


def format_inr(val: Optional[Union[int, float]], compact: bool = False) -> str:
    """Format numeric value into Indian Rupee (INR ₹) representation."""
    if val is None or pd.isna(val):
        return "N/A"
    try:
        val = float(val)
    except (ValueError, TypeError):
        return "N/A"

    if compact:
        abs_val = abs(val)
        sign = "-" if val < 0 else ""
        if abs_val >= 10000000:
            return f"{sign}₹{abs_val / 10000000:.2f} Cr"
        if abs_val >= 100000:
            return f"{sign}₹{abs_val / 100000:.2f} Lakh"
        if abs_val >= 1000:
            return f"{sign}₹{abs_val / 1000:.1f} K"
        return f"{sign}₹{abs_val:.2f}"

    # Indian number formatting system (xx,xx,xxx.xx)
    is_neg = val < 0
    val_abs = abs(val)
    parts = f"{val_abs:.2f}".split(".")
    int_part = parts[0]
    dec_part = parts[1]

    if len(int_part) <= 3:
        formatted = int_part
    else:
        last3 = int_part[-3:]
        remaining = int_part[:-3]
        chunks = []
        while remaining:
            chunks.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        formatted = ",".join(chunks) + "," + last3

    sign_str = "-" if is_neg else ""
    return f"{sign_str}₹{formatted}.{dec_part}"


def format_number(val: Optional[Union[int, float]], decimals: int = 0) -> str:
    """Format standard integer or float with commas."""
    if val is None or pd.isna(val):
        return "N/A"
    if decimals == 0:
        return f"{int(round(val)):,}"
    return f"{val:,.{decimals}f}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers handling division by zero or NaN."""
    if denominator == 0 or pd.isna(denominator) or pd.isna(numerator):
        return default
    return numerator / denominator


# Color definitions for charts
PALETTE = {
    "primary": "#1f77b4",
    "secondary": "#ff7f0e",
    "success": "#2ca02c",
    "danger": "#d62728",
    "warning": "#e377c2",
    "info": "#17becf",
    "dark": "#2c3e50",
    "light": "#ecf0f1",
    "accent": "#9467bd",
}
