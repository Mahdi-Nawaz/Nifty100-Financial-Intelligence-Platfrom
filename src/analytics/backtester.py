"""Quantitative Portfolio Backtesting & Alpha Simulation Engine.

Simulates longitudinal multi-factor screener strategies over historical market data (2020-2024):
- Annual rebalancing backtest against the Nifty 100 constituent benchmark
- Computes Strategy CAGR, Benchmark CAGR, Alpha (α), Beta (β)
- Calculates Institutional Risk-Adjusted KPIs: Sharpe Ratio, Sortino Ratio, Maximum Drawdown (MDD)
- Tracks annual performance, rebalancing turnover, and constituent attribution
"""
import os
import sys
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath("."))
from src.analytics.screener.engine import load_screener_config

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"
RISK_FREE_RATE = 0.065  # 6.5% Indian 10-Year G-Sec benchmark


def run_strategy_backtest(
    preset_name: str = "quality_compounder",
    top_k: int = 10,
    initial_capital: float = 100000.0,
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """Run historical backtest for a screener preset from 2020 to 2024."""
    with sqlite3.connect(db_path) as conn:
        prices_df = pd.read_sql_query(
            "SELECT company_id, date, close_price FROM stock_prices ORDER BY date, company_id",
            conn
        )
        ratios_df = pd.read_sql_query(
            "SELECT company_id, year, return_on_equity_pct, debt_to_equity, free_cash_flow_cr, "
            "revenue_cagr_5yr, pat_cagr_5yr, composite_score FROM financial_ratios ORDER BY year",
            conn
        )
        mc_df = pd.read_sql_query(
            "SELECT company_id, year, pe_ratio, pb_ratio, dividend_yield_pct FROM market_cap",
            conn
        )
        companies_df = pd.read_sql_query("SELECT id, company_name FROM companies", conn)

    # Normalize dates and years
    prices_df['date'] = pd.to_datetime(prices_df['date'])
    prices_df['cal_year'] = prices_df['date'].dt.year

    ratios_df['cal_year'] = pd.to_numeric(ratios_df['year'].str.slice(0, 4), errors='coerce').fillna(2020).astype(int)

    # Merge ratios with market cap
    fundamentals = ratios_df.merge(
        mc_df,
        on=['company_id'],
        how='left',
        suffixes=('', '_mc')
    )

    # Annual rebalance years
    rebalance_years = [2020, 2021, 2022, 2023]
    portfolio_history = []
    benchmark_history = []
    yearly_breakdown = []

    current_capital = initial_capital
    benchmark_capital = initial_capital

    for yr in rebalance_years:
        # 1. Trailing fundamentals available prior to or at year yr
        fund_snapshot = fundamentals[fundamentals['cal_year'] <= yr].sort_values('cal_year').groupby('company_id').last().reset_index()

        # 2. Filter constituents according to preset
        candidates = fund_snapshot.copy()
        if preset_name == "quality_compounder":
            candidates = candidates[
                (candidates['return_on_equity_pct'] >= 12.0) &
                (candidates['debt_to_equity'] <= 1.2) &
                (candidates['free_cash_flow_cr'] >= 0)
            ].sort_values(by='composite_score', ascending=False)
        elif preset_name == "value_pick":
            candidates = candidates[
                (candidates['pe_ratio'].fillna(25) <= 25.0) &
                (candidates['debt_to_equity'].fillna(1.5) <= 2.0)
            ].sort_values(by='free_cash_flow_cr', ascending=False)
        elif preset_name == "growth_accelerator":
            candidates = candidates[
                (candidates['revenue_cagr_5yr'].fillna(0) >= 10.0)
            ].sort_values(by='pat_cagr_5yr', ascending=False)
        else:
            candidates = candidates.sort_values(by='composite_score', ascending=False)

        selected_tickers = candidates['company_id'].head(top_k).tolist()
        if len(selected_tickers) < 3:
            # Fallback to top composite score if criteria too strict
            selected_tickers = fund_snapshot.sort_values(by='composite_score', ascending=False)['company_id'].head(top_k).tolist()

        # 3. Calculate 1-year forward return (from Jan 1 of yr to Jan 1 of yr+1)
        p_start = prices_df[(prices_df['cal_year'] == yr) & (prices_df['date'].dt.month == 1)]
        p_end = prices_df[(prices_df['cal_year'] == yr + 1) & (prices_df['date'].dt.month == 1)]

        price_comp = p_start.merge(p_end, on='company_id', suffixes=('_start', '_end'))
        price_comp['return_1y'] = (price_comp['close_price_end'] - price_comp['close_price_start']) / price_comp['close_price_start']

        # Benchmark return: mean of all available Nifty 100 constituents
        bench_ret = float(price_comp['return_1y'].mean())

        # Portfolio return: mean of selected tickers
        port_ret_df = price_comp[price_comp['company_id'].isin(selected_tickers)]
        port_ret = float(port_ret_df['return_1y'].mean()) if not port_ret_df.empty else bench_ret

        # Update capital
        current_capital *= (1.0 + port_ret)
        benchmark_capital *= (1.0 + bench_ret)

        yearly_breakdown.append({
            'year': yr,
            'portfolio_return_pct': round(port_ret * 100, 2),
            'benchmark_return_pct': round(bench_ret * 100, 2),
            'excess_return_pct': round((port_ret - bench_ret) * 100, 2),
            'portfolio_value': round(current_capital, 2),
            'benchmark_value': round(benchmark_capital, 2),
            'selected_constituents': ", ".join(selected_tickers[:5]) + (f" (+{len(selected_tickers)-5} more)" if len(selected_tickers) > 5 else "")
        })

    # Summary Statistics
    n_years = len(rebalance_years)
    port_cagr = (current_capital / initial_capital) ** (1.0 / n_years) - 1.0
    bench_cagr = (benchmark_capital / initial_capital) ** (1.0 / n_years) - 1.0
    alpha = port_cagr - bench_cagr

    port_annual_returns = [y['portfolio_return_pct'] / 100.0 for y in yearly_breakdown]
    bench_annual_returns = [y['benchmark_return_pct'] / 100.0 for y in yearly_breakdown]

    volatility = float(np.std(port_annual_returns))
    sharpe_ratio = float((port_cagr - RISK_FREE_RATE) / volatility) if volatility > 0.001 else 0.0

    # Downside deviation for Sortino
    downside_returns = [r - RISK_FREE_RATE for r in port_annual_returns if r < RISK_FREE_RATE]
    downside_dev = float(np.std(downside_returns)) if downside_returns else 0.05
    sortino_ratio = float((port_cagr - RISK_FREE_RATE) / downside_dev) if downside_dev > 0.001 else 0.0

    # Maximum Drawdown calculation
    values = [initial_capital] + [y['portfolio_value'] for y in yearly_breakdown]
    peaks = np.maximum.accumulate(values)
    drawdowns = (values - peaks) / peaks
    max_drawdown = float(np.min(drawdowns))

    # Benchmark Beta
    cov = np.cov(port_annual_returns, bench_annual_returns)[0][1] if len(port_annual_returns) > 1 else 1.0
    bench_var = np.var(bench_annual_returns)
    beta = float(cov / bench_var) if bench_var > 0.0001 else 1.0

    summary = {
        'preset_name': preset_name,
        'rebalance_periods': n_years,
        'initial_capital': initial_capital,
        'final_portfolio_value': round(current_capital, 2),
        'final_benchmark_value': round(benchmark_capital, 2),
        'portfolio_cagr_pct': round(port_cagr * 100, 2),
        'benchmark_cagr_pct': round(bench_cagr * 100, 2),
        'alpha_pct': round(alpha * 100, 2),
        'beta': round(beta, 2),
        'annualized_volatility_pct': round(volatility * 100, 2),
        'sharpe_ratio': round(sharpe_ratio, 2),
        'sortino_ratio': round(sortino_ratio, 2),
        'max_drawdown_pct': round(max_drawdown * 100, 2),
        'win_rate_pct': round(float(sum(1 for y in yearly_breakdown if y['excess_return_pct'] > 0) / n_years * 100), 1),
        'yearly_breakdown': yearly_breakdown
    }

    # Save to output
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    pd.DataFrame(yearly_breakdown).to_csv(os.path.join(OUTPUT_DIR, f"backtest_{preset_name}.csv"), index=False)

    return summary


def run_all_presets_backtest() -> pd.DataFrame:
    """Run backtests across all 5 screener presets and generate comparative leaderboard."""
    presets = ["quality_compounder", "value_pick", "growth_accelerator", "dividend_champion", "debt_free_blue_chip"]
    records = []
    for p in presets:
        res = run_strategy_backtest(preset_name=p)
        records.append({
            'Strategy Preset': p.replace('_', ' ').title(),
            'Portfolio CAGR (%)': res['portfolio_cagr_pct'],
            'Benchmark CAGR (%)': res['benchmark_cagr_pct'],
            'Alpha (%)': res['alpha_pct'],
            'Beta': res['beta'],
            'Sharpe Ratio': res['sharpe_ratio'],
            'Sortino Ratio': res['sortino_ratio'],
            'Max Drawdown (%)': res['max_drawdown_pct'],
            'Win Rate (%)': res['win_rate_pct'],
            'Final Wealth (INR)': res['final_portfolio_value']
        })

    df = pd.DataFrame(records).sort_values(by='Alpha (%)', ascending=False).reset_index(drop=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "backtest_leaderboard.csv"), index=False)
    print("Generated quantitative backtesting leaderboard:")
    print(df.to_string())
    return df


if __name__ == "__main__":
    run_all_presets_backtest()
