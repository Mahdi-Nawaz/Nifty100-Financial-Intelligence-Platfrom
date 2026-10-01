"""Streamlit Screen 4: Peer Comparison & Radar Analytics."""
import os
import sys
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import query_db, load_db_universe
from src.dashboard.utils.charts import plot_radar_comparison

st.set_page_config(page_title="Peer Comparison", page_icon="⚖️", layout="wide")

st.title("⚖️ Peer Comparison Engine")
st.markdown("Compare industry peers across 20 fundamental metrics with interactive radar benchmarks and percentile distributions.")

# Fetch unique peer groups
pg_list = query_db("SELECT DISTINCT peer_group_name FROM peer_groups ORDER BY peer_group_name")
groups = pg_list['peer_group_name'].tolist()

selected_group = st.selectbox("Select Peer Group:", groups)

# Fetch group members
members_df = query_db("""
    SELECT pg.company_id, pg.is_benchmark, c.company_name
    FROM peer_groups pg
    JOIN companies c ON pg.company_id = c.id
    WHERE pg.peer_group_name = ?
""", (selected_group,))

tickers = members_df['company_id'].tolist()
st.info(f"**Peer Group Members ({len(tickers)}):** {', '.join(tickers)}")

# Benchmark
bench_row = members_df[members_df['is_benchmark'] == 1]
benchmark_ticker = bench_row.iloc[0]['company_id'] if not bench_row.empty else tickers[0]

# Universe data
universe = load_db_universe()
grp_data = universe[universe['ticker'].isin(tickers)]

# Select primary company for radar
comp_choice = st.selectbox("Select Target Company for Radar Benchmark:", tickers, index=0)

radar_metrics = ['return_on_equity_pct', 'operating_profit_margin_pct', 'net_profit_margin_pct', 'revenue_cagr_5yr', 'pat_cagr_5yr', 'composite_score']
target_row = grp_data[grp_data['ticker'] == comp_choice].iloc[0]

comp_metrics = {m.replace('_pct', '').replace('_5yr', '').replace('_', ' ').upper(): float(target_row.get(m) or 0.0) for m in radar_metrics}
peer_medians = {m.replace('_pct', '').replace('_5yr', '').replace('_', ' ').upper(): float(grp_data[m].median() or 0.0) for m in radar_metrics}

col_chart, col_details = st.columns([1, 1])
with col_chart:
    fig_radar = plot_radar_comparison(comp_metrics, peer_medians, comp_choice, selected_group)
    st.plotly_chart(fig_radar, use_container_width=True)

with col_details:
    st.subheader(f"📊 {comp_choice} vs {selected_group} Median")
    comp_table = []
    for k in comp_metrics.keys():
        cv = comp_metrics[k]
        pv = peer_medians[k]
        delta = cv - pv
        comp_table.append({
            'Metric': k,
            f'{comp_choice}': f"{cv:.1f}",
            f'{selected_group} Median': f"{pv:.1f}",
            'Delta': f"{'+' if delta >= 0 else ''}{delta:.1f}"
        })
    st.table(pd.DataFrame(comp_table))

st.markdown("---")
st.subheader("📋 Peer Group Comparison Table")
display_cols = ['ticker', 'company_name', 'composite_score', 'return_on_equity_pct', 'operating_profit_margin_pct', 'debt_to_equity', 'pe_ratio', 'free_cash_flow_cr', 'revenue_cagr_5yr']
st.dataframe(grp_data[display_cols].rename(columns={
    'ticker': 'Ticker',
    'company_name': 'Name',
    'composite_score': 'Score',
    'return_on_equity_pct': 'ROE %',
    'operating_profit_margin_pct': 'OPM %',
    'debt_to_equity': 'D/E',
    'pe_ratio': 'P/E',
    'free_cash_flow_cr': 'FCF (₹ Cr)',
    'revenue_cagr_5yr': '5Y Rev CAGR %'
}), use_container_width=True)
