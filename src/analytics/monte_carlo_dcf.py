"""Probabilistic Monte Carlo Discounted Cash Flow (DCF) Valuation Engine.

Runs 5,000 stochastic simulations per company incorporating:
- Normal distribution for 5-Year Revenue Growth based on historical mean & volatility
- Stochastic Operating Profit Margin (OPM) distribution
- Triangular distribution for WACC (Weighted Average Cost of Capital)
- Uniform distribution for Terminal Growth Rate
- Intrinsic value confidence intervals (P10, P25, P50, P75, P90)
- Probability of Undervaluation at Current Market Price (Margin of Safety)
"""
import os
import sys
import sqlite3
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath("."))

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"


def run_monte_carlo_dcf(
    ticker: str,
    n_simulations: int = 5000,
    db_path: str = DB_PATH
) -> Dict[str, Any]:
    """Run Monte Carlo DCF simulation for a single company."""
    with sqlite3.connect(db_path) as conn:
        comp_df = pd.read_sql_query("SELECT id, company_name FROM companies WHERE id = ?", conn, params=(ticker,))
        pl_df = pd.read_sql_query("SELECT * FROM profitandloss WHERE company_id = ? ORDER BY year", conn, params=(ticker,))
        bs_df = pd.read_sql_query("SELECT * FROM balancesheet WHERE company_id = ? ORDER BY year", conn, params=(ticker,))
        cf_df = pd.read_sql_query("SELECT * FROM cashflow WHERE company_id = ? ORDER BY year", conn, params=(ticker,))
        mc_df = pd.read_sql_query("SELECT * FROM market_cap WHERE company_id = ? ORDER BY year DESC LIMIT 1", conn, params=(ticker,))
        price_df = pd.read_sql_query("SELECT close_price FROM stock_prices WHERE company_id = ? ORDER BY date DESC LIMIT 1", conn, params=(ticker,))

    if comp_df.empty or pl_df.empty:
        raise ValueError(f"Company {ticker} not found in database.")

    cname = comp_df['company_name'].iloc[0]
    cmp = float(price_df['close_price'].iloc[0]) if not price_df.empty else 1000.0

    # Historical base parameters
    latest_pl = pl_df.iloc[-1]
    latest_bs = bs_df.iloc[-1] if not bs_df.empty else pd.Series()

    base_sales = float(latest_pl.get('sales') or 1000.0)
    base_opm = float(latest_pl.get('opm_percentage') or 15.0) / 100.0
    tax_rate = float(latest_pl.get('tax_percentage') or 25.0) / 100.0
    tax_rate = np.clip(tax_rate, 0.15, 0.35)

    # Historical sales growth mean and std
    sales_hist = pl_df['sales'].dropna().astype(float)
    if len(sales_hist) >= 3:
        growth_rates = sales_hist.pct_change().dropna()
        mu_growth = float(growth_rates.mean())
        sigma_growth = float(growth_rates.std())
    else:
        mu_growth = 0.10
        sigma_growth = 0.05

    mu_growth = np.clip(mu_growth, 0.02, 0.25)
    sigma_growth = np.clip(sigma_growth, 0.02, 0.15)

    # Debt and Cash/Investments
    borrowings = float(latest_bs.get('borrowings') or 0.0) if not latest_bs.empty else 0.0
    investments = float(latest_bs.get('investments') or 0.0) if not latest_bs.empty else 0.0
    net_debt = borrowings - investments

    # Estimate proxy shares outstanding via Market Cap / CMP or equity capital
    mkt_cap_cr = float(mc_df['market_cap_crore'].iloc[0]) if not mc_df.empty else (base_sales * 2.0)
    shares_proxy = (mkt_cap_cr * 10000000.0) / cmp if cmp > 0 else 10000000.0

    # -------------------------------------------------------------
    # STOCHASTIC SIMULATION (Vectorized NumPy for maximum speed)
    # -------------------------------------------------------------
    np.random.seed(42)

    # Sample stochastic parameters
    sim_rev_growth = np.random.normal(mu_growth, sigma_growth, (n_simulations, 5))
    sim_rev_growth = np.clip(sim_rev_growth, -0.10, 0.35)

    sim_opm = np.random.normal(base_opm, base_opm * 0.15, n_simulations)
    sim_opm = np.clip(sim_opm, 0.05, 0.50)

    # WACC: Triangular distribution (min=10%, mode=12%, max=15%)
    sim_wacc = np.random.triangular(0.10, 0.12, 0.15, n_simulations)

    # Terminal growth rate: Uniform distribution (4% to 6%)
    sim_terminal_g = np.random.uniform(0.04, 0.06, n_simulations)

    # Reinvestment rate proxy
    reinvestment_rate = 0.30

    # Project 5-year revenues: shape (n_simulations, 5)
    revenues = np.zeros((n_simulations, 5))
    curr_rev = np.full(n_simulations, base_sales)
    for t in range(5):
        curr_rev = curr_rev * (1.0 + sim_rev_growth[:, t])
        revenues[:, t] = curr_rev

    # Project FCFF for each year
    # FCFF = EBIT * (1 - tax) * (1 - reinvestment_rate)
    pv_fcff_total = np.zeros(n_simulations)
    last_year_fcff = np.zeros(n_simulations)

    for t in range(5):
        year_ebit = revenues[:, t] * sim_opm
        year_nopat = year_ebit * (1.0 - tax_rate)
        year_fcff = year_nopat * (1.0 - reinvestment_rate)
        discount_factor = (1.0 + sim_wacc) ** (t + 1)
        pv_fcff_total += (year_fcff / discount_factor)
        if t == 4:
            last_year_fcff = year_fcff

    # Terminal Value: TV = [FCFF_5 * (1 + g)] / (WACC - g)
    denom = np.maximum(sim_wacc - sim_terminal_g, 0.02)
    terminal_val = (last_year_fcff * (1.0 + sim_terminal_g)) / denom
    pv_terminal_val = terminal_val / ((1.0 + sim_wacc) ** 5)

    # Enterprise Value & Equity Value (in INR Crores)
    enterprise_value_cr = pv_fcff_total + pv_terminal_val
    equity_value_cr = enterprise_value_cr - net_debt

    # Convert to per-share intrinsic value (in INR)
    sim_intrinsic_values = (equity_value_cr * 10000000.0) / shares_proxy
    sim_intrinsic_values = np.clip(sim_intrinsic_values, 1.0, cmp * 5.0)

    # Statistical summaries
    p10 = float(np.percentile(sim_intrinsic_values, 10))
    p25 = float(np.percentile(sim_intrinsic_values, 25))
    p50 = float(np.percentile(sim_intrinsic_values, 50))  # Median Fair Value
    p75 = float(np.percentile(sim_intrinsic_values, 75))
    p90 = float(np.percentile(sim_intrinsic_values, 90))

    prob_undervalued = float(np.mean(sim_intrinsic_values > cmp) * 100.0)
    margin_of_safety = float(((p50 - cmp) / cmp) * 100.0)

    if prob_undervalued >= 70.0:
        verdict = "Attractive Buy (High Margin of Safety)"
    elif prob_undervalued >= 40.0:
        verdict = "Fairly Valued"
    else:
        verdict = "Overvalued / Premium Pricing"

    return {
        'company_id': ticker,
        'company_name': cname,
        'current_market_price': round(cmp, 2),
        'median_fair_value': round(p50, 2),
        'bear_case_p10': round(p10, 2),
        'base_case_p50': round(p50, 2),
        'bull_case_p90': round(p90, 2),
        'prob_undervalued_pct': round(prob_undervalued, 1),
        'margin_of_safety_pct': round(margin_of_safety, 1),
        'simulated_wacc_mean_pct': round(float(np.mean(sim_wacc)) * 100, 1),
        'simulated_rev_growth_mean_pct': round(float(np.mean(sim_rev_growth)) * 100, 1),
        'verdict': verdict,
        'simulations_count': n_simulations
    }


def run_monte_carlo_universe(db_path: str = DB_PATH) -> pd.DataFrame:
    """Run Monte Carlo DCF simulations across all companies in the universe."""
    with sqlite3.connect(db_path) as conn:
        tickers = pd.read_sql_query("SELECT id FROM companies", conn)['id'].tolist()

    results = []
    for t in tickers:
        try:
            res = run_monte_carlo_dcf(t, n_simulations=2000, db_path=db_path)
            results.append(res)
        except Exception as e:
            continue

    df = pd.DataFrame(results)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_csv(os.path.join(OUTPUT_DIR, "monte_carlo_valuation_summary.csv"), index=False)

    # Persist in SQLite
    with sqlite3.connect(db_path) as conn:
        df.to_sql("monte_carlo_valuation", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mc_val_cid ON monte_carlo_valuation(company_id);")

    print(f"Completed Monte Carlo DCF for {len(df)} companies.")
    return df


if __name__ == "__main__":
    run_monte_carlo_universe()
