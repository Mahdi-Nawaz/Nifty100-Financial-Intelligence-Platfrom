"""Cached database loader for Streamlit Dashboard."""
import os
import sqlite3
import pandas as pd
import streamlit as st

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")

@st.cache_data(ttl=600)
def load_db_universe():
    """Load latest universe fundamental and valuation dataset."""
    from src.analytics.screener.engine import get_latest_screener_universe
    return get_latest_screener_universe(DB_PATH)

@st.cache_data(ttl=600)
def query_db(query: str, params: tuple = ()):
    """Run read query against SQLite database."""
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)

@st.cache_data(ttl=600)
def get_all_tickers():
    """Get sorted list of all 92 ticker IDs and company names."""
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT id, company_name FROM companies ORDER BY id ASC", conn)
    return df
