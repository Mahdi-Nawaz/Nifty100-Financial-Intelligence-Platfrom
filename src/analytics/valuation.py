"""Valuation & Market Data Module: multiples, sector comparisons, and overvaluation flags."""
import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any

sys.path.insert(0, os.path.abspath("."))
from src.analytics.screener.engine import get_latest_screener_universe

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"

def compute_valuation_module(db_path: str = DB_PATH) -> pd.DataFrame:
    """Compute valuation multiples, 5yr medians, sector relatives, and valuation flags."""
    universe = get_latest_screener_universe(db_path)
    
    with sqlite3.connect(db_path) as conn:
        mc_hist = pd.read_sql_query("SELECT company_id, year, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct FROM market_cap", conn)
        sec_df = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)

    # 5-year medians per company
    mc_5yr = mc_hist[mc_hist['year'] >= 2019].groupby('company_id').agg({
        'pe_ratio': 'median',
        'pb_ratio': 'median',
        'ev_ebitda': 'median',
        'dividend_yield_pct': 'median'
    }).reset_index().rename(columns={
        'pe_ratio': 'pe_5yr_median',
        'pb_ratio': 'pb_5yr_median',
        'ev_ebitda': 'ev_ebitda_5yr_median',
        'dividend_yield_pct': 'div_yield_5yr_median'
    })

    val_df = universe.merge(mc_5yr, left_on='ticker', right_on='company_id', how='left')

    # Sector median P/E and EV/EBITDA
    sector_medians = val_df.groupby('broad_sector').agg({
        'pe_ratio': 'median',
        'ev_ebitda': 'median',
        'pb_ratio': 'median'
    }).rename(columns={
        'pe_ratio': 'sector_pe_median',
        'ev_ebitda': 'sector_ev_ebitda_median',
        'pb_ratio': 'sector_pb_median'
    })

    val_df = val_df.merge(sector_medians, on='broad_sector', how='left')

    # Valuation flags
    # P/E > (sector_median * 1.5) -> Caution
    # P/E < (sector_median * 0.7) -> Discount
    flags = []
    rationale = []

    for _, row in val_df.iterrows():
        pe = row.get('pe_ratio')
        sec_pe = row.get('sector_pe_median')
        if pd.notnull(pe) and pd.notnull(sec_pe) and sec_pe > 0:
            if pe > (sec_pe * 1.5):
                flags.append('Caution')
                rationale.append(f"P/E {pe:.1f}x is >1.5x of sector median {sec_pe:.1f}x")
            elif pe < (sec_pe * 0.7):
                flags.append('Discount')
                rationale.append(f"P/E {pe:.1f}x is <0.7x of sector median {sec_pe:.1f}x")
            else:
                flags.append('Fair Value')
                rationale.append("Within standard sector valuation band")
        else:
            flags.append('Unclassified')
            rationale.append("Incomplete valuation multiple data")

    val_df['valuation_flag'] = flags
    val_df['flag_rationale'] = rationale

    # Sector rank by P/E
    val_df['sector_pe_rank'] = val_df.groupby('broad_sector')['pe_ratio'].rank(ascending=True)

    # Save valuation summary Excel
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    summary_cols = [
        'ticker', 'company_name', 'broad_sector', 'market_cap_crore', 'enterprise_value_crore',
        'pe_ratio', 'pe_5yr_median', 'sector_pe_median', 'sector_pe_rank',
        'pb_ratio', 'pb_5yr_median', 'ev_ebitda', 'ev_ebitda_5yr_median',
        'dividend_yield_pct', 'fcf_yield', 'valuation_flag', 'flag_rationale'
    ]
    val_export = val_df[[c for c in summary_cols if c in val_df.columns]].copy()
    val_export.to_excel(os.path.join(OUTPUT_DIR, "valuation_summary.xlsx"), index=False)

    # Save valuation flags CSV
    flagged = val_df[val_df['valuation_flag'].isin(['Caution', 'Discount'])][
        ['ticker', 'company_name', 'broad_sector', 'pe_ratio', 'sector_pe_median', 'valuation_flag', 'flag_rationale']
    ]
    flagged.to_csv(os.path.join(OUTPUT_DIR, "valuation_flags.csv"), index=False)

    print(f"Valuation module generated valuation_summary.xlsx and valuation_flags.csv ({len(flagged)} flagged).")
    return val_df

if __name__ == "__main__":
    compute_valuation_module()
