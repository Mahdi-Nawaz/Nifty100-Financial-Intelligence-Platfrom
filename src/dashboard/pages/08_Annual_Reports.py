"""Streamlit Screen 8: Primary Documents & Annual Reports Repository."""
import os
import sys
import streamlit as st
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import query_db, get_all_tickers

st.set_page_config(page_title="Annual Reports", page_icon="📑", layout="wide")

st.title("📑 Annual Reports & Corporate Filings")
st.markdown("Direct repository links to verified BSE India annual report PDFs (2010–2024).")

tickers_df = get_all_tickers()
ticker_options = ["All Companies"] + [f"{r['id']} - {r['company_name']}" for _, r in tickers_df.iterrows()]
sel_opt = st.selectbox("Filter by Company:", ticker_options)

query = "SELECT d.company_id, c.company_name, d.Year, d.Annual_Report FROM documents d JOIN companies c ON d.company_id = c.id"
params = []

if sel_opt != "All Companies":
    sel_tick = sel_opt.split(" - ")[0]
    query += " WHERE d.company_id = ?"
    params.append(sel_tick)

query += " ORDER BY d.company_id ASC, d.Year DESC"

docs_df = query_db(query, tuple(params))
st.info(f"Showing **{len(docs_df)} primary source filings**.")

# Display table
st.dataframe(docs_df.rename(columns={
    'company_id': 'Ticker',
    'company_name': 'Company Name',
    'Year': 'Filing Year',
    'Annual_Report': 'BSE India PDF Link'
}), use_container_width=True, height=450)
