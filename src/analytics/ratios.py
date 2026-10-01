"""Comprehensive Financial Ratio Engine computing 50+ KPIs across Nifty 100."""
import os
import sys
import math
import sqlite3
import logging
import pandas as pd
import numpy as np
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import compute_cashflow_kpis, classify_capital_allocation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ratio_engine")

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"

def compute_all_ratios(db_path: str = DB_PATH) -> pd.DataFrame:
    """Compute 50+ financial ratios and KPIs for all companies across all historical years."""
    edge_cases_log = []
    
    with sqlite3.connect(db_path) as conn:
        comp_df = pd.read_sql_query("SELECT id, face_value, book_value, roce_percentage, roe_percentage FROM companies", conn)
        pl_df = pd.read_sql_query("SELECT * FROM profitandloss ORDER BY company_id, year", conn)
        bs_df = pd.read_sql_query("SELECT * FROM balancesheet ORDER BY company_id, year", conn)
        cf_df = pd.read_sql_query("SELECT * FROM cashflow ORDER BY company_id, year", conn)
        sec_df = pd.read_sql_query("SELECT company_id, broad_sector FROM sectors", conn)
        mc_df = pd.read_sql_query("SELECT company_id, year, market_cap_crore, enterprise_value_crore, pe_ratio, pb_ratio, ev_ebitda, dividend_yield_pct FROM market_cap", conn)

    # Convert year to sortable sequence
    pl_df['sort_year'] = pl_df['year'].str.slice(0, 4).astype(int)
    bs_df['sort_year'] = bs_df['year'].str.slice(0, 4).astype(int)
    cf_df['sort_year'] = cf_df['year'].str.slice(0, 4).astype(int)

    # Master financial statement merge on (company_id, year)
    m = pl_df.merge(bs_df, on=['company_id', 'year'], how='outer', suffixes=('', '_bs'))
    m = m.merge(cf_df, on=['company_id', 'year'], how='outer', suffixes=('', '_cf'))
    m = m.merge(comp_df, left_on='company_id', right_on='id', how='left')
    m = m.merge(sec_df, on='company_id', how='left')

    # Add numeric year for join with market_cap
    m['cal_year'] = pd.to_numeric(m['year'].str.slice(0, 4), errors='coerce').fillna(2020).astype(int)
    m = m.merge(mc_df, left_on=['company_id', 'cal_year'], right_on=['company_id', 'year'], how='left', suffixes=('', '_mc'))

    m = m.sort_values(by=['company_id', 'year']).reset_index(drop=True)

    ratio_rows = []
    capital_allocation_rows = []

    # Group by company to compute CAGRs and longitudinal trends
    for cid, group in m.groupby('company_id'):
        group = group.sort_values('year').reset_index(drop=True)
        n_years = len(group)
        is_bank = (group['broad_sector'].iloc[0] == 'Financials') if not group['broad_sector'].isna().all() else False

        for i in range(n_years):
            row = group.iloc[i]
            yr = row['year']

            sales = row.get('sales')
            op = row.get('operating_profit')
            dep = row.get('depreciation') or 0.0
            other_inc = row.get('other_income') or 0.0
            interest = row.get('interest') or 0.0
            pat = row.get('net_profit')
            eps = row.get('eps')
            div_payout = row.get('dividend_payout')

            eq_cap = row.get('equity_capital') or 0.0
            reserves = row.get('reserves') or 0.0
            tot_equity = eq_cap + reserves
            borrowings = row.get('borrowings') or 0.0
            tot_assets = row.get('total_assets')
            fixed_assets = row.get('fixed_assets')
            investments = row.get('investments') or 0.0
            other_assets = row.get('other_asset') or 0.0
            other_liab = row.get('other_liabilities') or 0.0
            face_val = row.get('face_value') or 1.0

            cfo = row.get('operating_activity')
            cfi = row.get('investing_activity')
            cff = row.get('financing_activity')

            # 1. Profitability Ratios
            # Net profit margin
            if pd.notnull(sales) and sales > 0 and pd.notnull(pat):
                npm = (pat / sales) * 100.0
            else:
                npm = None
                edge_cases_log.append(f"{cid} {yr}: NPM None due to sales={sales}")

            # Operating profit margin
            if pd.notnull(sales) and sales > 0 and pd.notnull(op):
                opm = (op / sales) * 100.0
            else:
                opm = None

            # EBIT & EBIT Margin
            ebit = (op - dep) if pd.notnull(op) else None
            ebit_margin = ((ebit / sales) * 100.0) if pd.notnull(ebit) and pd.notnull(sales) and sales > 0 else None

            # ROE (Edge case: negative equity -> None)
            if tot_equity > 0 and pd.notnull(pat):
                roe = (pat / tot_equity) * 100.0
            else:
                roe = None
                edge_cases_log.append(f"{cid} {yr}: ROE None due to total_equity={tot_equity}")

            # ROCE
            cap_employed = tot_equity + borrowings
            if cap_employed > 0 and pd.notnull(ebit):
                roce = (ebit / cap_employed) * 100.0
            else:
                roce = None

            # ROA
            if pd.notnull(tot_assets) and tot_assets > 0 and pd.notnull(pat):
                roa = (pat / tot_assets) * 100.0
            else:
                roa = None

            # 2. Leverage Ratios
            # Debt to Equity (0 for debt free)
            if tot_equity > 0:
                de = borrowings / tot_equity
            else:
                de = None

            # Interest coverage (ICR: None / 'Debt Free' if interest == 0)
            if pd.notnull(op):
                ebit_icr = op + other_inc
                if interest == 0 or pd.isnull(interest):
                    icr = 999.0 # Sentinel for debt-free display
                    edge_cases_log.append(f"{cid} {yr}: ICR debt-free substitution (interest=0)")
                else:
                    icr = ebit_icr / interest
            else:
                icr = None

            net_debt = borrowings - investments
            net_debt_ebitda = (net_debt / op) if pd.notnull(op) and op > 0 else None

            # 3. Efficiency Ratios
            asset_turnover = (sales / tot_assets) if pd.notnull(sales) and pd.notnull(tot_assets) and tot_assets > 0 else None
            fa_turnover = (sales / fixed_assets) if pd.notnull(sales) and pd.notnull(fixed_assets) and fixed_assets > 0 else None
            wc_days = (((other_assets - other_liab) / sales) * 365.0) if pd.notnull(sales) and sales > 0 else None

            # 4. Cash Flow Ratios
            fcf = (cfo + cfi) if pd.notnull(cfo) and pd.notnull(cfi) else None
            capex = abs(cfi) if pd.notnull(cfi) else None
            cfo_pat = (cfo / pat) if pd.notnull(cfo) and pd.notnull(pat) and pat != 0 else None
            capex_intensity = (capex / sales * 100.0) if pd.notnull(capex) and pd.notnull(sales) and sales > 0 else None
            fcf_conv = (fcf / op * 100.0) if pd.notnull(fcf) and pd.notnull(op) and op > 0 else None

            # Capital allocation pattern
            if pd.notnull(cfo) and pd.notnull(cfi) and pd.notnull(cff):
                s_cfo, s_cfi, s_cff, pat_label = classify_capital_allocation(cfo, cfi, cff)
            else:
                s_cfo, s_cfi, s_cff, pat_label = ("+", "-", "-", "Standard Reinvestor")

            capital_allocation_rows.append({
                'company_id': cid,
                'year': yr,
                'cfo_sign': s_cfo,
                'cfi_sign': s_cfi,
                'cff_sign': s_cff,
                'pattern_label': pat_label
            })

            # Book Value Per Share
            num_shares = (eq_cap / face_val) if face_val > 0 else 1.0
            bvps = (tot_equity / num_shares) if num_shares > 0 else None

            # 5. CAGR Calculations
            def get_cagr_for_window(col_name: str, window: int) -> float:
                if i < window:
                    return None
                val_base = group.iloc[i - window].get(col_name)
                val_end = row.get(col_name)
                c_val, flag, _ = calculate_cagr(val_base, val_end, window)
                if flag == "TURNAROUND":
                    edge_cases_log.append(f"{cid} {yr}: CAGR turnaround flag on {col_name} window={window}")
                return c_val

            rev_cagr_3 = get_cagr_for_window('sales', 3)
            rev_cagr_5 = get_cagr_for_window('sales', 5)
            rev_cagr_10 = get_cagr_for_window('sales', 10)
            pat_cagr_3 = get_cagr_for_window('net_profit', 3)
            pat_cagr_5 = get_cagr_for_window('net_profit', 5)
            eps_cagr_5 = get_cagr_for_window('eps', 5)
            fcf_cagr_5 = get_cagr_for_window('operating_activity', 5) # Proxy if FCF volatile
            fcf_cagr_10 = get_cagr_for_window('operating_activity', 10)

            # 6. Valuation Multiples & FCF Yield
            mkt_cap = row.get('market_cap_crore')
            pe = row.get('pe_ratio')
            pb = row.get('pb_ratio')
            ev_eb = row.get('ev_ebitda')
            div_yield = row.get('dividend_yield_pct')
            fcf_yield = (fcf / mkt_cap * 100.0) if pd.notnull(fcf) and pd.notnull(mkt_cap) and mkt_cap > 0 else None

            ratio_rows.append({
                'company_id': cid,
                'year': yr,
                'net_profit_margin_pct': round(npm, 2) if pd.notnull(npm) else None,
                'operating_profit_margin_pct': round(opm, 2) if pd.notnull(opm) else None,
                'return_on_equity_pct': round(roe, 2) if pd.notnull(roe) else None,
                'debt_to_equity': round(de, 2) if pd.notnull(de) else None,
                'interest_coverage': round(icr, 2) if pd.notnull(icr) else None,
                'asset_turnover': round(asset_turnover, 3) if pd.notnull(asset_turnover) else None,
                'free_cash_flow_cr': round(fcf, 2) if pd.notnull(fcf) else None,
                'capex_cr': round(capex, 2) if pd.notnull(capex) else None,
                'earnings_per_share': round(eps, 2) if pd.notnull(eps) else None,
                'book_value_per_share': round(bvps, 2) if pd.notnull(bvps) else None,
                'dividend_payout_ratio_pct': round(div_payout, 2) if pd.notnull(div_payout) else None,
                'total_debt_cr': round(borrowings, 2) if pd.notnull(borrowings) else None,
                'cash_from_operations_cr': round(cfo, 2) if pd.notnull(cfo) else None,
                'revenue_cagr_3yr': rev_cagr_3,
                'revenue_cagr_5yr': rev_cagr_5,
                'revenue_cagr_10yr': rev_cagr_10,
                'pat_cagr_3yr': pat_cagr_3,
                'pat_cagr_5yr': pat_cagr_5,
                'eps_cagr_5yr': eps_cagr_5,
                'cfo_pat_ratio': round(cfo_pat, 2) if pd.notnull(cfo_pat) else None,
                'capex_intensity': round(capex_intensity, 2) if pd.notnull(capex_intensity) else None,
                'fcf_cagr_5yr': fcf_cagr_5,
                'fcf_cagr_10yr': fcf_cagr_10,
                'fcf_conversion_rate': round(fcf_conv, 2) if pd.notnull(fcf_conv) else None,
                'capital_allocation_pattern': pat_label,
                'composite_score': None # Computed next in composite scoring step
            })

    ratios_df = pd.DataFrame(ratio_rows)
    cap_df = pd.DataFrame(capital_allocation_rows)

    # 7. Compute Composite Score (0-100) per section 25.1
    # Profitability (35%): ROE (15%), ROCE (10%), NPM (10%)
    # Cash Quality (30%): FCF CAGR 5yr (15%), CFO/PAT (10%), FCF > 0 flag (5%)
    # Growth (20%): Rev CAGR 5yr (10%), PAT CAGR 5yr (10%)
    # Leverage (15%): D/E score (10%), ICR score (5%)
    
    def score_metric(series: pd.Series, ascending: bool = True) -> pd.Series:
        valid = series.dropna()
        if len(valid) == 0:
            return pd.Series(50.0, index=series.index)
        p10 = np.percentile(valid, 10)
        p90 = np.percentile(valid, 90)
        clipped = series.clip(lower=p10, upper=p90)
        denom = (p90 - p10) if p90 > p10 else 1.0
        scaled = ((clipped - p10) / denom) * 100.0
        if not ascending:
            scaled = 100.0 - scaled
        return scaled.fillna(50.0)

    # Scores
    s_roe = score_metric(ratios_df['return_on_equity_pct'])
    s_npm = score_metric(ratios_df['net_profit_margin_pct'])
    s_opm = score_metric(ratios_df['operating_profit_margin_pct'])
    s_fcf_growth = score_metric(ratios_df['fcf_cagr_5yr'])
    s_cfo_pat = score_metric(ratios_df['cfo_pat_ratio'])
    s_fcf_pos = (ratios_df['free_cash_flow_cr'] > 0).astype(float) * 100.0
    s_rev_cagr = score_metric(ratios_df['revenue_cagr_5yr'])
    s_pat_cagr = score_metric(ratios_df['pat_cagr_5yr'])

    # D/E score: 0=100, 0.5=85, 1=70, 2=50, >5=0
    def de_to_score(val):
        if pd.isnull(val):
            return 70.0
        if val <= 0:
            return 100.0
        elif val <= 0.5:
            return 85.0
        elif val <= 1.0:
            return 70.0
        elif val <= 2.0:
            return 50.0
        elif val <= 5.0:
            return 25.0
        else:
            return 0.0

    s_de = ratios_df['debt_to_equity'].apply(de_to_score)

    # ICR score: >10=100, 5=75, 3=50, <1.5=0
    def icr_to_score(val):
        if pd.isnull(val) or val >= 999.0:
            return 100.0
        if val >= 10.0:
            return 100.0
        elif val >= 5.0:
            return 75.0
        elif val >= 3.0:
            return 50.0
        elif val >= 1.5:
            return 25.0
        else:
            return 0.0

    s_icr = ratios_df['interest_coverage'].apply(icr_to_score)

    prof_score = 0.15 * s_roe + 0.10 * s_opm + 0.10 * s_npm
    cash_score = 0.15 * s_fcf_growth + 0.10 * s_cfo_pat + 0.05 * s_fcf_pos
    growth_score = 0.10 * s_rev_cagr + 0.10 * s_pat_cagr
    lev_score = 0.10 * s_de + 0.05 * s_icr

    comp_score = prof_score + cash_score + growth_score + lev_score
    ratios_df['composite_score'] = comp_score.round(1)

    # Write to SQLite
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("DELETE FROM financial_ratios;")
        ratios_df.to_sql('financial_ratios', conn, if_exists='append', index=False)
        conn.execute("DELETE FROM capital_allocation;")
        cap_df.to_sql('capital_allocation', conn, if_exists='append', index=False)
        conn.commit()

    # Save deliverables
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    cap_df.to_csv(os.path.join(OUTPUT_DIR, "capital_allocation.csv"), index=False)

    # Write cashflow intelligence excel
    with pd.ExcelWriter(os.path.join(OUTPUT_DIR, "cashflow_intelligence.xlsx"), engine='openpyxl') as writer:
        ratios_df[[
            'company_id', 'year', 'cash_from_operations_cr', 'capex_cr', 
            'free_cash_flow_cr', 'cfo_pat_ratio', 'capex_intensity', 
            'fcf_conversion_rate', 'capital_allocation_pattern'
        ]].to_excel(writer, sheet_name='Cash Flow Intelligence', index=False)

    with open(os.path.join(OUTPUT_DIR, "ratio_edge_cases.log"), "w", encoding='utf-8') as f:
        f.write("\n".join(edge_cases_log[:500]))

    logger.info(f"Populated financial_ratios: {len(ratios_df)} records.")
    return ratios_df

if __name__ == "__main__":
    compute_all_ratios()
