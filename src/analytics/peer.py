"""Peer comparison engine, intra-group percentile ranking, and radar chart generator."""
import os
import sys
import sqlite3
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, List, Any

sys.path.insert(0, os.path.abspath("."))
from src.analytics.screener.engine import get_latest_screener_universe

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"
CHARTS_DIR = "reports/radar_charts"

PEER_METRICS = [
    'net_profit_margin_pct', 'operating_profit_margin_pct', 'return_on_equity_pct', 
    'debt_to_equity', 'interest_coverage', 'asset_turnover', 'free_cash_flow_cr', 
    'capex_cr', 'earnings_per_share', 'book_value_per_share', 'dividend_payout_ratio_pct', 
    'revenue_cagr_3yr', 'revenue_cagr_5yr', 'pat_cagr_3yr', 'pat_cagr_5yr', 
    'eps_cagr_5yr', 'cfo_pat_ratio', 'capex_intensity', 'fcf_conversion_rate', 'composite_score'
]

RADAR_AXES = [
    'return_on_equity_pct', 'operating_profit_margin_pct', 'net_profit_margin_pct',
    'revenue_cagr_5yr', 'pat_cagr_5yr', 'cfo_pat_ratio', 'free_cash_flow_cr', 'composite_score'
]

RADAR_LABELS = ['ROE', 'OPM', 'NPM', 'Rev CAGR 5Y', 'PAT CAGR 5Y', 'CFO/PAT', 'FCF', 'Quality']

def compute_peer_percentiles(db_path: str = DB_PATH) -> pd.DataFrame:
    """Compute percentile rank for every metric within peer group and sector."""
    universe = get_latest_screener_universe(db_path)
    
    with sqlite3.connect(db_path) as conn:
        pg_df = pd.read_sql_query("SELECT peer_group_name, company_id, is_benchmark FROM peer_groups", conn)

    merged = universe.merge(pg_df, left_on='ticker', right_on='company_id', how='left')
    # Fallback peer group for companies without explicit peer group is their broad sector
    merged['effective_group'] = merged['peer_group_name'].fillna(merged['broad_sector'].fillna('General'))

    percentile_rows = []

    for grp_name, group in merged.groupby('effective_group'):
        n_members = len(group)
        for metric in PEER_METRICS:
            if metric not in group.columns:
                continue
            
            s = group[['ticker', metric, 'year']].dropna(subset=[metric])
            if s.empty:
                continue
            
            # Rank descending for metrics where higher is better, ascending for debt
            ascending = (metric in ['debt_to_equity', 'capex_intensity'])
            ranks = s[metric].rank(ascending=ascending, pct=True) * 100.0

            for idx, r_val in s.iterrows():
                tck = r_val['ticker']
                raw_v = r_val[metric]
                pct_rank = ranks.loc[idx]
                yr = r_val['year']

                percentile_rows.append({
                    'company_id': tck,
                    'peer_group': grp_name,
                    'metric': metric,
                    'value': round(float(raw_v), 2),
                    'percentile_rank': round(float(pct_rank), 1),
                    'year': str(yr)
                })

    pct_df = pd.DataFrame(percentile_rows)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("DELETE FROM peer_percentiles;")
        pct_df.to_sql('peer_percentiles', conn, if_exists='append', index=False)
        conn.commit()

    return pct_df

def export_peer_comparison_excel(db_path: str = DB_PATH):
    """Generate peer_comparison.xlsx with 11 sheets and colour-coded percentile cells."""
    universe = get_latest_screener_universe(db_path)
    with sqlite3.connect(db_path) as conn:
        pg_df = pd.read_sql_query("SELECT peer_group_name, company_id, is_benchmark FROM peer_groups", conn)
        pct_df = pd.read_sql_query("SELECT * FROM peer_percentiles", conn)

    merged = pg_df.merge(universe, left_on='company_id', right_on='ticker', how='inner')
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "peer_comparison.xlsx")

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for grp_name, grp in merged.groupby('peer_group_name'):
            sheet_title = grp_name[:31]
            cols = ['company_id', 'company_name', 'is_benchmark'] + [m for m in PEER_METRICS if m in grp.columns]
            export_sub = grp[cols].copy()
            export_sub.to_excel(writer, sheet_name=sheet_title, index=False)

def generate_radar_charts(db_path: str = DB_PATH):
    """Generate 92 radar chart PNGs comparing each company against peer/sector average."""
    os.makedirs(CHARTS_DIR, exist_ok=True)
    universe = get_latest_screener_universe(db_path)
    with sqlite3.connect(db_path) as conn:
        pg_df = pd.read_sql_query("SELECT peer_group_name, company_id FROM peer_groups", conn)

    merged = universe.merge(pg_df, left_on='ticker', right_on='company_id', how='left')
    merged['effective_group'] = merged['peer_group_name'].fillna(merged['broad_sector'].fillna('General'))

    # Normalize metrics to 0-100 for radar scale
    scaled_df = merged.copy()
    for col in RADAR_AXES:
        if col in scaled_df.columns:
            vals = scaled_df[col].dropna()
            if not vals.empty:
                mn, mx = np.percentile(vals, 5), np.percentile(vals, 95)
                denom = (mx - mn) if mx > mn else 1.0
                scaled_df[col + '_scaled'] = ((scaled_df[col].clip(mn, mx) - mn) / denom) * 100.0
            else:
                scaled_df[col + '_scaled'] = 50.0

    num_vars = len(RADAR_AXES)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1] # Complete loop

    # Group averages
    scaled_cols = [c + '_scaled' for c in RADAR_AXES]
    grp_means = scaled_df.groupby('effective_group')[scaled_cols].mean()

    for _, row in scaled_df.iterrows():
        ticker = row['ticker']
        grp_name = row['effective_group']

        comp_vals = [row.get(c, 50.0) for c in scaled_cols]
        comp_vals += comp_vals[:1]

        avg_row = grp_means.loc[grp_name] if grp_name in grp_means.index else grp_means.iloc[0]
        avg_vals = avg_row.tolist()
        avg_vals += avg_vals[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        plt.style.use('default')

        # Company polygon
        ax.plot(angles, comp_vals, color='#1E88E5', linewidth=2, label=ticker)
        ax.fill(angles, comp_vals, color='#1E88E5', alpha=0.25)

        # Peer average polygon
        ax.plot(angles, avg_vals, color='#FB8C00', linewidth=1.5, linestyle='--', label=f'{grp_name} Avg')
        ax.fill(angles, avg_vals, color='#FB8C00', alpha=0.15)

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(RADAR_LABELS, size=9)
        ax.set_ylim(0, 100)
        ax.set_title(f"Financial Health Radar: {ticker}\n({grp_name})", size=11, fontweight='bold', pad=15)
        ax.legend(loc='upper right', bbox_to_anchor=(1.25, 1.1), fontsize=8)

        out_img = os.path.join(CHARTS_DIR, f"{ticker}_radar.png")
        plt.tight_layout()
        plt.savefig(out_img, dpi=120)
        plt.close(fig)

    print(f"Generated radar charts for {len(scaled_df)} companies in {CHARTS_DIR}")

def run_peer_module(db_path: str = DB_PATH):
    """Run full peer comparison pipeline."""
    compute_peer_percentiles(db_path)
    export_peer_comparison_excel(db_path)
    generate_radar_charts(db_path)

if __name__ == "__main__":
    run_peer_module()
