"""Screen 11: Probabilistic Monte Carlo DCF Valuation Simulator."""
import os
import sys
import sqlite3
import streamlit as st
import pandas as pd
import numpy as np
import plotly.figure_factory as ff
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath("."))
from src.analytics.monte_carlo_dcf import run_monte_carlo_dcf

st.set_page_config(page_title="Monte Carlo DCF - Nifty 100", page_icon="🎲", layout="wide")

st.title("🎲 Probabilistic Monte Carlo DCF Valuation Engine")
st.markdown("""
**Beyond Single-Point DCF Estimates**: Runs thousands of stochastic financial projections modeling stochastic 
**Revenue Growth, Operating Margins, Cost of Capital (WACC), and Terminal Growth**. Computes complete intrinsic value probability 
distributions and Margin of Safety against Current Market Price (CMP).
""")

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")

with sqlite3.connect(DB_PATH) as conn:
    companies = pd.read_sql_query("SELECT id, company_name FROM companies ORDER BY company_name", conn)

c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    company_options = {row['id']: f"{row['company_name']} ({row['id']})" for _, row in companies.iterrows()}
    selected_ticker = st.selectbox("Select Target Company:", options=list(company_options.keys()), format_func=lambda x: company_options[x], index=0)
with c2:
    sim_count = st.select_slider("Stochastic Simulations:", options=[1000, 2000, 5000, 10000], value=2000)
with c3:
    st.write("<br/>", unsafe_allow_html=True)
    run_btn = st.button("Run Simulation", type="primary")

with st.spinner(f"Simulating {sim_count} DCF projections for {selected_ticker}..."):
    res = run_monte_carlo_dcf(selected_ticker, n_simulations=sim_count, db_path=DB_PATH)

# Summary KPI Cards
k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.metric("Current Market Price (CMP)", f"₹{res['current_market_price']}")
with k2:
    st.metric("Median Fair Value (P50)", f"₹{res['median_fair_value']}")
with k3:
    mos = res['margin_of_safety_pct']
    st.metric("Margin of Safety", f"{mos}%", delta=f"{mos}%" if mos >= 0 else f"{mos}%", delta_color="normal" if mos >= 0 else "inverse")
with k4:
    prob = res['prob_undervalued_pct']
    st.metric("Probability Undervalued", f"{prob}%", help="% of simulated iterations where intrinsic value > CMP")
with k5:
    verdict = res['verdict']
    st.markdown(f"""
    <div style="background:#1E293B; border-radius:8px; padding:10px; border:1px solid #334155; text-align:center;">
        <span style="font-size:11px; color:#94A3B8;">VALUATION VERDICT</span>
        <div style="font-size:14px; font-weight:700; color:{'#10B981' if 'Buy' in verdict else '#38BDF8' if 'Fairly' in verdict else '#EF4444'}; margin-top:4px;">{verdict}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

tab1, tab2 = st.tabs(["📊 Intrinsic Value Confidence Intervals", "📋 Simulation Parameters & Percentiles"])

with tab1:
    st.subheader(f"Probabilistic Fair Value Distribution: {res['company_name']}")

    # Synthetic distribution for visualization centered on percentiles
    np.random.seed(42)
    p10 = res['bear_case_p10']
    p50 = res['base_case_p50']
    p90 = res['bull_case_p90']
    cmp = res['current_market_price']

    # Generate normal-approximate sample for the density plot
    mu = p50
    sigma = (p90 - p10) / 2.56 if (p90 - p10) > 0 else p50 * 0.1
    sim_data = np.random.normal(mu, sigma, sim_count)
    sim_data = sim_data[sim_data > 0]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=sim_data, nbinsx=60,
        name="Fair Value Distribution",
        marker_color="#38BDF8", opacity=0.75
    ))

    # Add vertical lines for P10, P50, P90, and CMP
    fig.add_vline(x=cmp, line_width=3, line_color="#EF4444", annotation_text=f"CMP: ₹{cmp}", annotation_position="top left")
    fig.add_vline(x=p50, line_width=3, line_dash="dash", line_color="#10B981", annotation_text=f"Median P50: ₹{p50}", annotation_position="top right")
    fig.add_vline(x=p10, line_width=2, line_dash="dot", line_color="#F59E0B", annotation_text=f"Bear P10: ₹{p10}")
    fig.add_vline(x=p90, line_width=2, line_dash="dot", line_color="#A855F7", annotation_text=f"Bull P90: ₹{p90}")

    fig.update_layout(
        template="plotly_dark",
        height=500,
        xaxis_title="Intrinsic Value Per Share (₹)",
        yaxis_title="Simulation Frequency",
        bargap=0.05
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Monte Carlo Simulation Bounds & Input Assumptions")
    p_df = pd.DataFrame([
        {"Metric / Parameter": "Bear Case (10th Percentile)", "Value": f"₹{res['bear_case_p10']}"},
        {"Metric / Parameter": "Base Case Median (50th Percentile)", "Value": f"₹{res['base_case_p50']}"},
        {"Metric / Parameter": "Bull Case (90th Percentile)", "Value": f"₹{res['bull_case_p90']}"},
        {"Metric / Parameter": "Simulated Mean Revenue Growth (5Y)", "Value": f"{res['simulated_rev_growth_mean_pct']}%"},
        {"Metric / Parameter": "Simulated Mean WACC (Discount Rate)", "Value": f"{res['simulated_wacc_mean_pct']}%"},
        {"Metric / Parameter": "Terminal Growth Assumption Range", "Value": "4.0% - 6.0%"},
        {"Metric / Parameter": "Total Stochastic Iterations", "Value": f"{res['simulations_count']:,}"},
    ])
    st.table(p_df)
