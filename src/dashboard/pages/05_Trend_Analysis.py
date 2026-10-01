"""Streamlit Screen 5: Multi-Year Trend & Growth Analytics."""
import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import query_db, get_all_tickers

st.set_page_config(page_title="Trend Analytics", page_icon="📈", layout="wide")

st.title("📈 Historical Trend & Growth Analytics")
st.markdown("Track 10–13 year growth trajectories, margin trends, and financial performance over time.")

tickers_df = get_all_tickers()
ticker_options = [f"{r['id']} - {r['company_name']}" for _, r in tickers_df.iterrows()]
selected_str = st.sidebar.selectbox("Select Company:", ticker_options, index=0)
selected_ticker = selected_str.split(" - ")[0]

# Load time series
pl_df = query_db("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year ASC", (selected_ticker,))
ratios_df = query_db("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year ASC", (selected_ticker,))

merged_ts = pl_df.merge(ratios_df, on=['company_id', 'year'], how='outer', suffixes=('', '_r'))
merged_ts = merged_ts.sort_values(by='year').reset_index(drop=True)

metrics_available = [
    ('sales', 'Revenue / Sales (₹ Cr)'),
    ('operating_profit', 'Operating Profit (₹ Cr)'),
    ('net_profit', 'Net Profit / PAT (₹ Cr)'),
    ('opm_percentage', 'Operating Profit Margin (%)'),
    ('return_on_equity_pct', 'Return on Equity (%)'),
    ('free_cash_flow_cr', 'Free Cash Flow (₹ Cr)'),
    ('debt_to_equity', 'Debt to Equity Ratio')
]

col_choices = [m[1] for m in metrics_available]
sel_metrics = st.multiselect("Select Metrics to Overlay:", col_choices, default=[col_choices[0], col_choices[2]])

if sel_metrics:
    fig = go.Figure()
    for m_label in sel_metrics:
        raw_col = next(k for k, v in metrics_available if v == m_label)
        if raw_col in merged_ts.columns:
            fig.add_trace(go.Scatter(
                x=merged_ts['year'],
                y=merged_ts[raw_col],
                mode='lines+markers',
                name=m_label,
                line=dict(width=2.5)
            ))
    fig.update_layout(
        title=f"Historical Multi-Metric Trend for {selected_ticker}",
        xaxis_title="Financial Year",
        hovermode="x unified",
        margin=dict(t=40, b=20, l=20, r=20)
    )
    st.plotly_chart(fig, use_container_width=True)

# Historical Statement Table
st.markdown("---")
st.subheader("📜 Historical Financial Record Table")
st.dataframe(merged_ts[['year', 'sales', 'operating_profit', 'net_profit', 'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr']], use_container_width=True)
