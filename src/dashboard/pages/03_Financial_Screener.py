"""Streamlit Screen 3: Multi-Parameter Financial Screener."""
import os
import sys
import streamlit as st
import pandas as pd
import io

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import load_db_universe
from src.analytics.screener.engine import load_screener_config, run_preset_screener

st.set_page_config(page_title="Financial Screener", page_icon="🔍", layout="wide")

st.title("🔍 Multi-Parameter Investment Screener")
st.markdown("Filter and rank all 92 Nifty 100 companies based on custom institutional thresholds or pre-built quantitative presets.")

df_universe = load_db_universe()
config = load_screener_config()

# Presets
presets = config.get("presets", {})
preset_choices = ["Custom Filter"] + [presets[k]["name"] for k in presets.keys()]
selected_preset_name = st.selectbox("Select Preset Screener:", preset_choices)

st.sidebar.header("🛠️ Screener Filters")

# Sector filter
sectors = ["All Sectors"] + sorted(df_universe['broad_sector'].dropna().unique().tolist())
sel_sector = st.sidebar.selectbox("Sector:", sectors)

# Sidebar Sliders
min_roe = st.sidebar.slider("Minimum ROE (%)", min_value=-10.0, max_value=60.0, value=15.0 if selected_preset_name == "Quality Compounder" else 0.0)
max_de = st.sidebar.slider("Maximum Debt to Equity (D/E)", min_value=0.0, max_value=10.0, value=1.0 if selected_preset_name == "Quality Compounder" else 5.0)
min_fcf = st.sidebar.number_input("Minimum Free Cash Flow (₹ Cr)", value=0.0 if selected_preset_name == "Quality Compounder" else -50000.0)
min_rev_cagr = st.sidebar.slider("Minimum 5Y Revenue CAGR (%)", min_value=-20.0, max_value=50.0, value=10.0 if selected_preset_name == "Quality Compounder" else -20.0)
max_pe = st.sidebar.slider("Maximum P/E Ratio", min_value=5.0, max_value=100.0, value=25.0 if selected_preset_name == "Value Pick" else 100.0)
min_div_yield = st.sidebar.slider("Minimum Dividend Yield (%)", min_value=0.0, max_value=6.0, value=2.0 if selected_preset_name == "Dividend Champion" else 0.0)

# Filter logic
filtered = df_universe.copy()

if sel_sector != "All Sectors":
    filtered = filtered[filtered['broad_sector'] == sel_sector]

is_fin = filtered['broad_sector'].isin(['Financials', 'Financial Services'])

if selected_preset_name != "Custom Filter":
    # Find preset key
    p_key = next((k for k, v in presets.items() if v["name"] == selected_preset_name), None)
    if p_key:
        filtered = run_preset_screener(p_key, df_universe, config)
else:
    filtered = filtered[
        (filtered['return_on_equity_pct'].fillna(-999) >= min_roe) &
        ((filtered['debt_to_equity'].fillna(999) <= max_de) | is_fin) &
        (filtered['free_cash_flow_cr'].fillna(-999999) >= min_fcf) &
        (filtered['revenue_cagr_5yr'].fillna(-999) >= min_rev_cagr) &
        (filtered['pe_ratio'].fillna(999) <= max_pe) &
        (filtered['dividend_yield_pct'].fillna(0) >= min_div_yield)
    ]
    filtered = filtered.sort_values(by='composite_score', ascending=False)

st.success(f"**Found {len(filtered)} matching companies** based on selected criteria.")

cols_to_show = [
    'ticker', 'company_name', 'broad_sector', 'composite_score',
    'return_on_equity_pct', 'debt_to_equity', 'free_cash_flow_cr',
    'revenue_cagr_5yr', 'pat_cagr_5yr', 'pe_ratio', 'dividend_yield_pct'
]

display_table = filtered[cols_to_show].rename(columns={
    'ticker': 'Ticker',
    'company_name': 'Company Name',
    'broad_sector': 'Sector',
    'composite_score': 'Score (0-100)',
    'return_on_equity_pct': 'ROE %',
    'debt_to_equity': 'D/E',
    'free_cash_flow_cr': 'FCF (₹ Cr)',
    'revenue_cagr_5yr': '5Y Rev CAGR %',
    'pat_cagr_5yr': '5Y PAT CAGR %',
    'pe_ratio': 'P/E',
    'dividend_yield_pct': 'Div Yield %'
})

st.dataframe(display_table, use_container_width=True, height=450)

# Export buttons (CSV and Excel)
col_exp1, col_exp2 = st.columns([1, 1])
with col_exp1:
    csv_data = display_table.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Screener Results (CSV)",
        data=csv_data,
        file_name="screener_results.csv",
        mime="text/csv",
        key="btn_csv_export"
    )

with col_exp2:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        display_table.to_excel(writer, sheet_name='Screener Results', index=False)
    st.download_button(
        label="📊 Download Screener Results (Excel)",
        data=buffer.getvalue(),
        file_name="screener_results.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="btn_excel_export"
    )
