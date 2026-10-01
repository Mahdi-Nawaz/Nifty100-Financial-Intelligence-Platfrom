"""Streamlit Screen 2: Comprehensive Company Profile."""
import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import load_db_universe, query_db, get_all_tickers
from src.dashboard.utils.charts import plot_company_financials

st.set_page_config(page_title="Company Profile", page_icon="🏢", layout="wide")

tickers_df = get_all_tickers()
ticker_options = [f"{r['id']} - {r['company_name']}" for _, r in tickers_df.iterrows()]

selected_str = st.sidebar.selectbox("Select Company:", ticker_options, index=0)
selected_ticker = selected_str.split(" - ")[0]

# Load company details
universe = load_db_universe()
comp_info = universe[universe['ticker'] == selected_ticker].iloc[0]

# Fetch full statement history
pl_df = query_db("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC", (selected_ticker,))
bs_df = query_db("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year ASC", (selected_ticker,))
cf_df = query_db("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year ASC", (selected_ticker,))
ratios_df = query_db("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year ASC", (selected_ticker,))
about_res = query_db("SELECT about_company, website FROM companies WHERE id = ?", (selected_ticker,))

# Header
st.title(f"🏢 {comp_info['company_name']} ({selected_ticker})")
st.markdown(f"**Sector:** {comp_info.get('broad_sector', 'N/A')} | **Sub-Sector:** {comp_info.get('sub_sector', 'N/A')} | **Category:** {comp_info.get('market_cap_category', 'Large Cap')}")

if not about_res.empty and pd.notnull(about_res.iloc[0]['about_company']):
    st.info(f"**Business Profile:** {about_res.iloc[0]['about_company']}")

# Tearsheet PDF download link
tearsheet_path = os.path.join("reports/tearsheets", f"{selected_ticker}_tearsheet.pdf")
if os.path.exists(tearsheet_path):
    with open(tearsheet_path, "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label="📄 Download Institutional Tearsheet (2-Page PDF)",
        data=pdf_bytes,
        file_name=f"{selected_ticker}_tearsheet.pdf",
        mime="application/pdf"
    )

st.markdown("---")

# 6 KPI Tiles
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Market Cap", f"₹{comp_info.get('market_cap_crore', 0):,.0f} Cr")
k2.metric("P/E Ratio", f"{comp_info.get('pe_ratio', 0):.1f}x")
k3.metric("ROE %", f"{comp_info.get('return_on_equity_pct', 0):.1f}%")
k4.metric("Debt to Equity", f"{comp_info.get('debt_to_equity', 0):.2f}x")
k5.metric("Free Cash Flow", f"₹{comp_info.get('free_cash_flow_cr', 0):,.0f} Cr")
k6.metric("Health Score", f"{comp_info.get('composite_score', 0):.1f}/100")

st.markdown("<br/>", unsafe_allow_html=True)

# Historical Charts
c1, c2 = st.columns(2)
with c1:
    fig_pl = plot_company_financials(pl_df)
    st.plotly_chart(fig_pl, use_container_width=True)

with c2:
    fig_bs = go.Figure()
    bs_tail = bs_df.tail(8)
    fig_bs.add_trace(go.Bar(x=bs_tail['year'], y=bs_tail['total_assets'], name='Total Assets', marker_color='#1E88E5'))
    fig_bs.add_trace(go.Bar(x=bs_tail['year'], y=bs_tail['borrowings'], name='Borrowings / Debt', marker_color='#E53935'))
    fig_bs.update_layout(title="Asset Expansion vs Debt (₹ Cr)", barmode='group', margin=dict(t=40, b=20, l=20, r=20))
    st.plotly_chart(fig_bs, use_container_width=True)

# Qualitative Pros and Cons
st.markdown("---")
st.subheader("💡 Qualitative Investment Insights")

p_col, c_col = st.columns(2)
if os.path.exists("output/pros_cons_generated.csv"):
    pc_df = pd.read_csv("output/pros_cons_generated.csv")
    pros = pc_df[(pc_df['company_id'] == selected_ticker) & (pc_df['type'] == 'pro')]['text'].tolist()
    cons = pc_df[(pc_df['company_id'] == selected_ticker) & (pc_df['type'] == 'con')]['text'].tolist()
    
    with p_col:
        st.markdown("#### ✅ Strengths (Pros)")
        for p in pros[:4]:
            st.success(f"• {p}")
            
    with c_col:
        st.markdown("#### ⚠️ Risks (Cons)")
        for c in cons[:4]:
            st.error(f"• {c}")
