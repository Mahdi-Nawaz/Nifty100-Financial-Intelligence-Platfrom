"""Forensic Accounting & Corporate Governance Red Flag Engine.

Implements institutional-grade forensic models across the Nifty 100 universe:
1. Beneish M-Score (8-factor earnings manipulation detection)
2. Altman Z''-Score (Emerging market insolvency & bankruptcy prediction)
3. Piotroski F-Score (9-factor fundamental strength & operational momentum)
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


def compute_forensic_scores(db_path: str = DB_PATH) -> pd.DataFrame:
    """Compute Beneish M-Score, Altman Z''-Score, and Piotroski F-Score for all companies."""
    with sqlite3.connect(db_path) as conn:
        comp_df = pd.read_sql_query("SELECT id, company_name FROM companies", conn)
        sec_df = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
        pl_df = pd.read_sql_query("SELECT * FROM profitandloss ORDER BY company_id, year", conn)
        bs_df = pd.read_sql_query("SELECT * FROM balancesheet ORDER BY company_id, year", conn)
        cf_df = pd.read_sql_query("SELECT * FROM cashflow ORDER BY company_id, year", conn)

    # Merge financial statements
    m = pl_df.merge(bs_df, on=['company_id', 'year'], how='outer', suffixes=('', '_bs'))
    m = m.merge(cf_df, on=['company_id', 'year'], how='outer', suffixes=('', '_cf'))
    m = m.merge(comp_df, left_on='company_id', right_on='id', how='left')
    m = m.merge(sec_df, on='company_id', how='left')

    # Convert year to sortable sequence
    m['sort_year'] = pd.to_numeric(m['year'].astype(str).str.slice(0, 4), errors='coerce').fillna(2000).astype(int)
    m = m.sort_values(by=['company_id', 'sort_year']).reset_index(drop=True)

    results = []

    for cid, group in m.groupby('company_id'):
        group = group.sort_values('sort_year').reset_index(drop=True)
        n = len(group)
        if n < 2:
            continue

        cname = group['company_name'].iloc[0]
        sector = group['broad_sector'].iloc[0]
        is_financial = (sector in ['Financials', 'Financial Services'])

        # Analyze latest period vs previous period
        curr = group.iloc[-1]
        prev = group.iloc[-2]
        latest_year = curr['year']

        # -------------------------------------------------------------
        # 1. BENEISH M-SCORE CALCULATION (8 Factors)
        # -------------------------------------------------------------
        sales_t = float(curr.get('sales') or 0.0)
        sales_t1 = float(prev.get('sales') or 0.0)

        exp_t = float(curr.get('expenses') or 0.0)
        exp_t1 = float(prev.get('expenses') or 0.0)

        dep_t = float(curr.get('depreciation') or 0.0)
        dep_t1 = float(prev.get('depreciation') or 0.0)

        net_profit_t = float(curr.get('net_profit') or 0.0)
        cfo_t = float(curr.get('operating_activity') or 0.0)

        total_assets_t = float(curr.get('total_assets') or 0.0)
        total_assets_t1 = float(prev.get('total_assets') or 0.0)

        fixed_assets_t = float(curr.get('fixed_assets') or 0.0)
        fixed_assets_t1 = float(prev.get('fixed_assets') or 0.0)

        cwip_t = float(curr.get('cwip') or 0.0)
        cwip_t1 = float(prev.get('cwip') or 0.0)

        other_assets_t = float(curr.get('other_asset') or 0.0)
        other_assets_t1 = float(prev.get('other_asset') or 0.0)

        borrowings_t = float(curr.get('borrowings') or 0.0)
        borrowings_t1 = float(prev.get('borrowings') or 0.0)

        other_liab_t = float(curr.get('other_liabilities') or 0.0)
        other_liab_t1 = float(prev.get('other_liabilities') or 0.0)

        # Days Sales in Receivables / Other Assets Index (DSRI)
        dsr_t = (other_assets_t / sales_t) if sales_t > 0 else 1.0
        dsr_t1 = (other_assets_t1 / sales_t1) if sales_t1 > 0 else 1.0
        dsri = float(np.clip(dsr_t / dsr_t1 if dsr_t1 > 0 else 1.0, 0.2, 5.0))

        # Gross Margin Index (GMI)
        gm_t = ((sales_t - exp_t) / sales_t) if sales_t > 0 else 0.2
        gm_t1 = ((sales_t1 - exp_t1) / sales_t1) if sales_t1 > 0 else 0.2
        gmi = float(np.clip(gm_t1 / gm_t if gm_t > 0.01 else 1.0, 0.2, 5.0))

        # Asset Quality Index (AQI)
        nca_t = 1.0 - ((fixed_assets_t + cwip_t) / total_assets_t) if total_assets_t > 0 else 0.5
        nca_t1 = 1.0 - ((fixed_assets_t1 + cwip_t1) / total_assets_t1) if total_assets_t1 > 0 else 0.5
        aqi = float(np.clip(nca_t / nca_t1 if nca_t1 > 0.01 else 1.0, 0.2, 5.0))

        # Sales Growth Index (SGI)
        sgi = float(np.clip(sales_t / sales_t1 if sales_t1 > 0 else 1.0, 0.2, 5.0))

        # Depreciation Index (DEPI)
        depr_rate_t = dep_t / (fixed_assets_t + dep_t) if (fixed_assets_t + dep_t) > 0 else 0.05
        depr_rate_t1 = dep_t1 / (fixed_assets_t1 + dep_t1) if (fixed_assets_t1 + dep_t1) > 0 else 0.05
        depi = float(np.clip(depr_rate_t1 / depr_rate_t if depr_rate_t > 0.001 else 1.0, 0.2, 5.0))

        # Sales General and Admin Expense Index (SGAI)
        sgai = float(np.clip((exp_t / sales_t) / (exp_t1 / sales_t1) if (sales_t > 0 and sales_t1 > 0 and exp_t1 > 0) else 1.0, 0.2, 5.0))

        # Leverage Index (LVGI)
        lev_t = (borrowings_t + other_liab_t) / total_assets_t if total_assets_t > 0 else 0.5
        lev_t1 = (borrowings_t1 + other_liab_t1) / total_assets_t1 if total_assets_t1 > 0 else 0.5
        lvgi = float(np.clip(lev_t / lev_t1 if lev_t1 > 0.01 else 1.0, 0.2, 5.0))

        # Total Accruals to Total Assets (TATA)
        tata = float(np.clip((net_profit_t - cfo_t) / total_assets_t if total_assets_t > 0 else 0.0, -1.0, 1.0))

        # Standard Beneish M-Score Formula
        beneish_m = (-4.84 +
                     0.920 * dsri +
                     0.528 * gmi +
                     0.404 * aqi +
                     0.892 * sgi +
                     0.115 * depi -
                     0.172 * sgai +
                     4.037 * tata +
                     0.0327 * lvgi)

        # Non-financials standard threshold: -1.78. If M > -1.78, higher risk of manipulation
        beneish_flag = "High Risk (Potential Manipulation)" if (beneish_m > -1.78 and not is_financial) else "Low Risk (Unlikely Manipulation)"

        # -------------------------------------------------------------
        # 2. ALTMAN Z''-SCORE (Emerging Market Variant)
        # -------------------------------------------------------------
        # X1: Working Capital / Total Assets
        working_cap = other_assets_t - other_liab_t
        x1 = working_cap / total_assets_t if total_assets_t > 0 else 0.1

        # X2: Retained Earnings (Reserves) / Total Assets
        reserves_t = float(curr.get('reserves') or 0.0)
        x2 = reserves_t / total_assets_t if total_assets_t > 0 else 0.2

        # X3: Operating Profit / Total Assets
        op_t = float(curr.get('operating_profit') or 0.0)
        x3 = op_t / total_assets_t if total_assets_t > 0 else 0.1

        # X4: Book Value of Equity / Total Liabilities
        equity_t = float(curr.get('equity_capital') or 0.0) + reserves_t
        tot_liab = borrowings_t + other_liab_t
        x4 = equity_t / tot_liab if tot_liab > 0 else 2.0

        altman_z = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4

        if is_financial:
            altman_zone = "Financial (Z-Score N/A)"
        elif altman_z > 2.60:
            altman_zone = "Safe Zone"
        elif altman_z >= 1.10:
            altman_zone = "Grey Zone"
        else:
            altman_zone = "Distress Zone"

        # -------------------------------------------------------------
        # 3. PIOTROSKI F-SCORE (9 Binary Signals)
        # -------------------------------------------------------------
        f_score = 0
        signals = {}

        # Signal 1: Positive Net Profit
        s1 = 1 if net_profit_t > 0 else 0
        f_score += s1
        signals['positive_net_profit'] = s1

        # Signal 2: Positive Operating Cash Flow
        s2 = 1 if cfo_t > 0 else 0
        f_score += s2
        signals['positive_cfo'] = s2

        # Signal 3: Higher ROA than previous year
        roa_t = net_profit_t / total_assets_t if total_assets_t > 0 else 0
        roa_t1 = float(prev.get('net_profit') or 0.0) / total_assets_t1 if total_assets_t1 > 0 else 0
        s3 = 1 if roa_t > roa_t1 else 0
        f_score += s3
        signals['higher_roa'] = s3

        # Signal 4: Quality of Earnings (CFO > Net Profit)
        s4 = 1 if cfo_t > net_profit_t else 0
        f_score += s4
        signals['cfo_greater_than_pat'] = s4

        # Signal 5: Lower Long-term Debt Ratio
        dr_t = borrowings_t / total_assets_t if total_assets_t > 0 else 0
        dr_t1 = borrowings_t1 / total_assets_t1 if total_assets_t1 > 0 else 0
        s5 = 1 if dr_t <= dr_t1 else 0
        f_score += s5
        signals['lower_or_equal_leverage'] = s5

        # Signal 6: Higher Current / Working Capital Liquidity
        wc_t = (other_assets_t / other_liab_t) if other_liab_t > 0 else 1.0
        wc_t1 = (other_assets_t1 / other_liab_t1) if other_liab_t1 > 0 else 1.0
        s6 = 1 if wc_t >= wc_t1 else 0
        f_score += s6
        signals['improving_liquidity'] = s6

        # Signal 7: No Share Dilution (Equity Capital not increased)
        eq_t = float(curr.get('equity_capital') or 0.0)
        eq_t1 = float(prev.get('equity_capital') or 0.0)
        s7 = 1 if eq_t <= eq_t1 + 0.01 else 0
        f_score += s7
        signals['no_dilution'] = s7

        # Signal 8: Higher Operating / Gross Margin
        s8 = 1 if gm_t >= gm_t1 else 0
        f_score += s8
        signals['higher_gross_margin'] = s8

        # Signal 9: Higher Asset Turnover
        at_t = sales_t / total_assets_t if total_assets_t > 0 else 0
        at_t1 = sales_t1 / total_assets_t1 if total_assets_t1 > 0 else 0
        s9 = 1 if at_t >= at_t1 else 0
        f_score += s9
        signals['higher_asset_turnover'] = s9

        if f_score >= 7:
            f_category = "Very Strong (7-9)"
        elif f_score >= 5:
            f_category = "Moderate (5-6)"
        else:
            f_category = "Weak (0-4)"

        results.append({
            'company_id': cid,
            'company_name': cname,
            'broad_sector': sector,
            'latest_year': latest_year,
            'beneish_m_score': round(beneish_m, 2),
            'beneish_flag': beneish_flag,
            'dsri': round(dsri, 2),
            'gmi': round(gmi, 2),
            'aqi': round(aqi, 2),
            'sgi': round(sgi, 2),
            'depi': round(depi, 2),
            'sgai': round(sgai, 2),
            'lvgi': round(lvgi, 2),
            'tata': round(tata, 3),
            'altman_z_score': round(altman_z, 2),
            'altman_zone': altman_zone,
            'piotroski_f_score': int(f_score),
            'piotroski_category': f_category
        })

    forensic_df = pd.DataFrame(results)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    forensic_df.to_csv(os.path.join(OUTPUT_DIR, "forensic_audit_summary.csv"), index=False)

    # Persist in SQLite for fast dashboard & API querying
    with sqlite3.connect(db_path) as conn:
        forensic_df.to_sql("forensic_audit", conn, if_exists="replace", index=False)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_forensic_cid ON forensic_audit(company_id);")

    print(f"Computed forensic intelligence for {len(forensic_df)} companies.")
    return forensic_df


if __name__ == "__main__":
    compute_forensic_scores()
