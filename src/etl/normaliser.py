"""Data normalisation utilities for Nifty 100 Financial Intelligence Platform."""
import re
from typing import Any, Optional

MONTH_MAP = {
    'JAN': '01', 'JANUARY': '01',
    'FEB': '02', 'FEBRUARY': '02',
    'MAR': '03', 'MARCH': '03',
    'APR': '04', 'APRIL': '04',
    'MAY': '05',
    'JUN': '06', 'JUNE': '06',
    'JUL': '07', 'JULY': '07',
    'AUG': '08', 'AUGUST': '08',
    'SEP': '09', 'SEPTEMBER': '09',
    'OCT': '10', 'OCTOBER': '10',
    'NOV': '11', 'NOVEMBER': '11',
    'DEC': '12', 'DECEMBER': '12'
}

def normalize_ticker(ticker: Any) -> str:
    """Normalise ticker to uppercase stripped string preserving valid characters."""
    if ticker is None:
        return ""
    ticker_str = str(ticker).strip().upper()
    return ticker_str

def normalize_year(year_val: Any) -> str:
    """Standardise various financial year representations to 'YYYY-MM' format."""
    if year_val is None:
        return "PARSE_ERROR"
    
    val_str = str(year_val).strip()
    if not val_str or val_str.lower() in ('nan', 'none', 'null', 'nat'):
        return "PARSE_ERROR"
    
    # Already normalised 'YYYY-MM'
    if re.match(r'^\d{4}-\d{2}$', val_str):
        return val_str
    
    # Pure integer or float year e.g. 2023 or 2023.0
    int_match = re.match(r'^(\d{4})(\.0+)?$', val_str)
    if int_match:
        return f"{int_match.group(1)}-03"
    
    # FY prefix e.g. FY23, FY2023, FY 24
    fy_match = re.match(r'^FY\s*(\d{2,4})$', val_str, re.IGNORECASE)
    if fy_match:
        yr = fy_match.group(1)
        if len(yr) == 2:
            yr = f"20{yr}"
        return f"{yr}-03"

    # Pattern: Month and Year separated by space, hyphen, slash e.g. Mar-23, Mar 2014, Dec-22, March-2023
    m_match = re.match(r'^([A-Za-z]+)[\s\-_/]*(\d{2,4})$', val_str)
    if m_match:
        mon_str = m_match.group(1).upper()
        yr_str = m_match.group(2)
        if len(yr_str) == 2:
            yr_str = f"20{yr_str}"
        if mon_str in MONTH_MAP:
            return f"{yr_str}-{MONTH_MAP[mon_str]}"

    # Pattern: Year and Month e.g. 2023-Mar or 2023Mar
    ym_match = re.match(r'^(\d{4})[\s\-_/]*([A-Za-z]+)$', val_str)
    if ym_match:
        yr_str = ym_match.group(1)
        mon_str = ym_match.group(2).upper()
        if mon_str in MONTH_MAP:
            return f"{yr_str}-{MONTH_MAP[mon_str]}"

    return "PARSE_ERROR"
