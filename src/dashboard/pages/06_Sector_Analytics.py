"""Streamlit Screen 6: Sector Benchmarks & Bubble Analytics."""
import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import load_db_universe

st.set_page_config(page_title="Sector Analytics", page_icon="🏭", layout="wide")

st.title("🏭 Sector Benchmarks & Relative Positioning")
st.markdown("Macro sector aggregation, valuation multiples, and constituent bubble distributions.")

df_universe = load_db_universe()
sectors = sorted(df_universe['broad_sector'].dropna().unique().tolist())

selected_sector = st.selectbox("Select Sector:", sectors)
sector_cos = df_universe[df_universe['broad_sector'] == selected_sector]

# Sector Report PDF download link
safe_name = selected_sector.replace("/", "_").replace(" ", "_")
sec_pdf = os.path.join("reports/sector", f"{safe_name}_report.pdf")
if os.path.exists(sec_pdf):
    with open(sec_pdf, "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label=f"📄 Download {selected_sector} Sector Intelligence Report (PDF)",
        data=pdf_bytes,
        file_name=f"{safe_name}_report.pdf",
        mime="application/pdf"
    )

# Summary metrics
s1, s2, s3, s4 = st.columns(4)
s1.metric("Constituents", f"{len(sector_cos)} cos")
s1.metric("Median ROE", f"{sector_cos['return_on_equity_pct'].median():.1f}%")
s3.metric("Median P/E", f"{sector_cos['pe_ratio'].median():.1f}x")
s4.metric("Total Sector Mkt Cap", f"₹{sector_cos['market_cap_crore'].sum():,.0f} Cr")

st.markdown("<br/>", unsafe_allow_html=True)

# Bubble chart: Sales vs ROE, size = market cap
fig_bubble = px.scatter(
    sector_cos,
    x='sales',
    y='return_on_equity_pct',
    size='market_cap_crore',
    color='sub_sector',
    hover_name='company_name',
    text='ticker',
    title=f"{selected_sector}: Revenue vs Return on Equity (Bubble size = Market Cap)",
    labels={'sales': 'Latest Sales (₹ Cr)', 'return_on_equity_pct': 'ROE %', 'sub_sector': 'Sub-Sector'}
)
fig_bubble.update_traces(textposition='top center')
fig_bubble.update_layout(margin=dict(t=40, b=20, l=20, r=20))
st.plotly_chart(fig_bubble, use_container_width=True)

# Sector constituents table
st.subheader("📋 Sector Constituents")
st.dataframe(sector_cos[[
    'ticker', 'company_name', 'sub_sector', 'market_cap_crore',
    'return_on_equity_pct', 'pe_ratio', 'debt_to_equity', 'composite_score'
]].rename(columns={
    'ticker': 'Ticker',
    'company_name': 'Company Name',
    'sub_sector': 'Sub-Sector',
    'market_cap_crore': 'Mkt Cap (₹ Cr)',
    'return_on_equity_pct': 'ROE %',
    'pe_ratio': 'P/E',
    'debt_to_equity': 'D/E',
    'composite_score': 'Score'
}), use_container_width=True)
