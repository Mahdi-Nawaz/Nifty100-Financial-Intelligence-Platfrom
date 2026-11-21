"""Cached database loader for Streamlit Dashboard."""
import os
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")

def get_connection():
    """Create optimized, thread-safe SQLite connection."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    try:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA busy_timeout = 5000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
    except Exception:
        pass
    return conn

@st.cache_data(ttl=600)
def load_db_universe():
    """Load latest universe fundamental and valuation dataset."""
    from src.analytics.screener.engine import get_latest_screener_universe
    return get_latest_screener_universe(DB_PATH)

@st.cache_data(ttl=600)
def query_db(query: str, params: tuple = ()):
    """Run read query against SQLite database."""
    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)

@st.cache_data(ttl=600)
def get_all_tickers():
    """Get sorted list of all 92 ticker IDs and company names."""
    with get_connection() as conn:
        df = pd.read_sql_query("SELECT id, company_name FROM companies ORDER BY id ASC", conn)
    return df

