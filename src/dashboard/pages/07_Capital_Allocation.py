"""Streamlit Screen 7: Capital Allocation Treemap & Archetypes."""
import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import query_db, load_db_universe

st.set_page_config(page_title="Capital Allocation", page_icon="🗺️", layout="wide")

st.title("🗺️ Capital Allocation & Cash Flow Archetypes")
st.markdown("8-way sign classification (CFO, CFI, CFF) revealing capital deployment strategies across Nifty 100.")

universe = load_db_universe()

# Treemap of companies by pattern
fig_tree = px.treemap(
    universe,
    path=['capital_allocation_pattern', 'broad_sector', 'ticker'],
    values='market_cap_crore',
    color='composite_score',
    color_continuous_scale='Blues',
    title="Capital Allocation Archetype Treemap (Sized by Market Cap, Colored by Health Score)"
)
fig_tree.update_layout(margin=dict(t=40, b=20, l=20, r=20))
st.plotly_chart(fig_tree, use_container_width=True)

# Archetype distribution
st.subheader("📊 Archetype Breakdown")
pat_counts = universe['capital_allocation_pattern'].value_counts().reset_index()
pat_counts.columns = ['Archetype', 'Company Count']
st.table(pat_counts)

# Detailed table
st.subheader("📋 Constituent Allocation Patterns")
st.dataframe(universe[['ticker', 'company_name', 'broad_sector', 'capital_allocation_pattern', 'free_cash_flow_cr', 'cfo_pat_ratio', 'composite_score']].rename(columns={
    'ticker': 'Ticker',
    'company_name': 'Company Name',
    'broad_sector': 'Sector',
    'capital_allocation_pattern': 'Pattern Label',
    'free_cash_flow_cr': 'FCF (₹ Cr)',
    'cfo_pat_ratio': 'CFO/PAT',
    'composite_score': 'Score'
}), use_container_width=True)
