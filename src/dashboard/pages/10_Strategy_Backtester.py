"""Screen 10: Quantitative Strategy Backtesting & Alpha Simulation."""
import os
import sys
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath("."))
from src.analytics.backtester import run_strategy_backtest, run_all_presets_backtest

st.set_page_config(page_title="Quantitative Backtester - Nifty 100", page_icon="📈", layout="wide")

st.title("📈 Quantitative Strategy Backtester & Alpha Simulator")
st.markdown("""
**Institutional Longitudinal Backtest (2020–2024)**: Evaluates multi-factor screener strategies against the 
**Nifty 100 Equal-Weighted Constituent Benchmark**. Computes Strategy CAGR, Benchmark Alpha ($\alpha$), 
Risk-adjusted returns (**Sharpe & Sortino Ratios**), and Maximum Drawdown (**MDD**).
""")

# Strategy Controls
c1, c2, c3 = st.columns([2, 1, 1])
with c1:
    preset_choice = st.selectbox(
        "Select Screener Strategy Preset:",
        [
            ("quality_compounder", "Quality Compounder (High ROE, Low Debt, Cash Flow Rich)"),
            ("value_pick", "Value Pick (Low P/E, Low P/B, High FCF Yield)"),
            ("growth_accelerator", "Growth Accelerator (High Revenue & PAT Momentum)"),
            ("dividend_champion", "Dividend Champion (High Yield, Sustainable Payout)"),
            ("debt_free_blue_chip", "Debt-Free Blue Chip (Zero Leverage, Large Cap)")
        ],
        format_func=lambda x: x[1]
    )[0]
with c2:
    top_k_choice = st.slider("Constituent Portfolio Size (Top K):", min_value=5, max_value=25, value=10, step=5)
with c3:
    init_cap = st.number_input("Initial Investment (₹):", min_value=10000, max_value=10000000, value=100000, step=10000)

# Run Backtest
with st.spinner("Running longitudinal quantitative backtest across annual rebalances..."):
    res = run_strategy_backtest(preset_name=preset_choice, top_k=top_k_choice, initial_capital=float(init_cap))

# Top KPI Metric Cards
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.metric("Portfolio CAGR", f"{res['portfolio_cagr_pct']}%")
with k2:
    st.metric("Benchmark CAGR", f"{res['benchmark_cagr_pct']}%")
with k3:
    alpha_val = res['alpha_pct']
    st.metric("Alpha (α)", f"{alpha_val}%", delta=f"{alpha_val}% vs N100", delta_color="normal" if alpha_val >= 0 else "inverse")
with k4:
    st.metric("Sharpe Ratio", f"{res['sharpe_ratio']}", help="Indian Risk-Free Rate benchmarked at 6.5%")
with k5:
    st.metric("Sortino Ratio", f"{res['sortino_ratio']}", help="Downside volatility adjusted")
with k6:
    st.metric("Max Drawdown", f"{res['max_drawdown_pct']}%")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Cumulative Wealth Trajectory", "📅 Annual Returns & Attribution", "🏆 Multi-Strategy Leaderboard"])

with tab1:
    st.subheader("Growth of ₹1,00,000: Strategy vs Benchmark")
    breakdown_df = pd.DataFrame(res['yearly_breakdown'])

    # Build wealth trajectory line chart
    wealth_dates = [2020] + breakdown_df['year'].tolist()
    port_vals = [init_cap] + breakdown_df['portfolio_value'].tolist()
    bench_vals = [init_cap] + breakdown_df['benchmark_value'].tolist()

    fig_wealth = go.Figure()
    fig_wealth.add_trace(go.Scatter(
        x=wealth_dates, y=port_vals,
        mode='lines+markers', name='Screener Strategy Portfolio',
        line=dict(color='#10B981', width=3)
    ))
    fig_wealth.add_trace(go.Scatter(
        x=wealth_dates, y=bench_vals,
        mode='lines+markers', name='Nifty 100 Benchmark',
        line=dict(color='#94A3B8', width=2, dash='dash')
    ))
    fig_wealth.update_layout(
        template="plotly_dark",
        height=450,
        yaxis_title="Portfolio Value (₹)",
        xaxis_title="Rebalance Year",
        hovermode="x unified"
    )
    st.plotly_chart(fig_wealth, use_container_width=True)

with tab2:
    st.subheader("Year-over-Year Performance Breakdown")
    fig_bar = px.bar(
        breakdown_df,
        x="year",
        y=["portfolio_return_pct", "benchmark_return_pct"],
        barmode="group",
        labels={"value": "Annual Return (%)", "year": "Year", "variable": "Series"},
        color_discrete_map={"portfolio_return_pct": "#38BDF8", "benchmark_return_pct": "#64748B"},
        title="Annual Strategy vs Benchmark Returns"
    )
    fig_bar.update_layout(template="plotly_dark", height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

    st.write("**Constituent Rebalance Selection & Performance Table:**")
    st.dataframe(breakdown_df, use_container_width=True)

with tab3:
    st.subheader("Quantitative Strategy Comparison Leaderboard")
    if st.button("Generate Complete Leaderboard across all 5 Presets"):
        with st.spinner("Computing multi-strategy matrix..."):
            lb_df = run_all_presets_backtest()
            st.dataframe(lb_df, use_container_width=True)
    else:
        lb_path = "output/backtest_leaderboard.csv"
        if os.path.exists(lb_path):
            lb_df = pd.read_csv(lb_path)
            st.dataframe(lb_df, use_container_width=True)
        else:
            st.info("Click the button above to simulate all 5 strategies simultaneously.")
