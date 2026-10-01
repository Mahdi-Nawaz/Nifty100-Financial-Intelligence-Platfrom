"""Nifty 100 Financial Intelligence Platform - Main Streamlit Dashboard."""
import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import load_db_universe, get_all_tickers
from src.dashboard.utils.charts import plot_sector_donut, plot_health_score_distribution

st.set_page_config(
    page_title="Nifty 100 Financial Intelligence",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich aesthetics
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border-radius: 10px;
        padding: 16px 20px;
        color: white;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title { font-size: 13px; color: #94A3B8; margin-bottom: 4px; font-weight: 500; }
    .metric-val { font-size: 24px; font-weight: 700; color: #38BDF8; }
    .badge-excellent { background-color: #10B981; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-good { background-color: #0EA5E9; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-average { background-color: #EAB308; color: black; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-weak { background-color: #F97316; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
    .badge-poor { background-color: #EF4444; color: white; padding: 3px 8px; border-radius: 4px; font-size: 11px; }
</style>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("📈 N100 Intelligence")
st.sidebar.markdown("**Institutional Fundamental Analytics**")
st.sidebar.markdown("---")
st.sidebar.info("""
**Platform Summary:**
• **92** Nifty 100 Companies  
• **50+** Computed KPIs  
• **13** Interactive Screens  
• **18** Screener Filters  
• **104** Automated PDF Reports  
• **20** REST API Endpoints  
• **Forensic Suite**: Beneish M, Altman Z, Piotroski F  
• **ML Anomaly Engine**: Isolation Forest & 3D PCA  
• **AI Research Copilot**: Natural Language Assistant  
• **Backtest Simulator**: 5-Year Alpha Engine  
• **Monte Carlo DCF**: 5,000 Stochastic Projections  
""")

# Load dataset
df_universe = load_db_universe()

# Top of Main App Section
_logo_path = os.path.join(os.path.abspath("."), "assets", "logo_primary.jpg")
if os.path.exists(_logo_path):
    st.image(_logo_path, width=160)

# Title and Subtitle
st.title("Nifty 100 Financial Intelligence Platform")
st.markdown("Transforming raw annual financial filings into quantitative intelligence, health triage, and institutional research.")

# KPI Banner
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
with kpi1:
    st.markdown("""<div class="metric-card"><div class="metric-title">COMPANIES ANALYZED</div><div class="metric-val">92</div></div>""", unsafe_allow_html=True)
with kpi2:
    tot_mkt = df_universe['market_cap_crore'].sum()
    st.markdown(f"""<div class="metric-card"><div class="metric-title">TOTAL MARKET CAP</div><div class="metric-val">₹{tot_mkt/100000:.1f}L Cr</div></div>""", unsafe_allow_html=True)
with kpi3:
    avg_roe = df_universe['return_on_equity_pct'].mean()
    st.markdown(f"""<div class="metric-card"><div class="metric-title">AVERAGE ROE</div><div class="metric-val">{avg_roe:.1f}%</div></div>""", unsafe_allow_html=True)
with kpi4:
    med_pe = df_universe['pe_ratio'].median()
    st.markdown(f"""<div class="metric-card"><div class="metric-title">MEDIAN P/E RATIO</div><div class="metric-val">{med_pe:.1f}x</div></div>""", unsafe_allow_html=True)
with kpi5:
    avg_score = df_universe['composite_score'].mean()
    st.markdown(f"""<div class="metric-card"><div class="metric-title">AVG HEALTH SCORE</div><div class="metric-val">{avg_score:.1f}/100</div></div>""", unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# Overview Visualizations
col_left, col_right = st.columns(2)
with col_left:
    fig_donut = plot_sector_donut(df_universe)
    st.plotly_chart(fig_donut, use_container_width=True)

with col_right:
    fig_hist = plot_health_score_distribution(df_universe)
    st.plotly_chart(fig_hist, use_container_width=True)

st.markdown("---")

# Quick Filterable Universe Table
st.subheader("📋 Nifty 100 Constituent Directory")

filter_sector = st.multiselect(
    "Filter by Broad Sector:",
    options=sorted(df_universe['broad_sector'].dropna().unique()),
    default=[]
)

display_df = df_universe.copy()
if filter_sector:
    display_df = display_df[display_df['broad_sector'].isin(filter_sector)]

show_cols = [
    'ticker', 'company_name', 'broad_sector', 'market_cap_crore',
    'return_on_equity_pct', 'debt_to_equity', 'pe_ratio',
    'free_cash_flow_cr', 'revenue_cagr_5yr', 'composite_score'
]

formatted_df = display_df[show_cols].rename(columns={
    'ticker': 'Ticker',
    'company_name': 'Company Name',
    'broad_sector': 'Sector',
    'market_cap_crore': 'Mkt Cap (₹ Cr)',
    'return_on_equity_pct': 'ROE %',
    'debt_to_equity': 'D/E',
    'pe_ratio': 'P/E',
    'free_cash_flow_cr': 'FCF (₹ Cr)',
    'revenue_cagr_5yr': '5Y Rev CAGR %',
    'composite_score': 'Health Score (0-100)'
}).sort_values(by='Health Score (0-100)', ascending=False)

st.dataframe(formatted_df, use_container_width=True, height=400)
st.caption(f"Displaying {len(formatted_df)} of 92 companies.")
