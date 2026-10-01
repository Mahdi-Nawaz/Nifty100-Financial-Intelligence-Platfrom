"""Investment Screener Engine supporting preset screens and dynamic queries."""
import os
import sys
import yaml
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath("."))

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
CONFIG_PATH = "config/screener_config.yaml"
OUTPUT_DIR = "output"

def load_screener_config(config_path: str = CONFIG_PATH) -> Dict[str, Any]:
    """Load screener configuration YAML."""
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_latest_screener_universe(db_path: str = DB_PATH) -> pd.DataFrame:
    """Extract latest completed annual fundamental, valuation, and sector dataset for all companies."""
    with sqlite3.connect(db_path) as conn:
        query = """
        WITH latest_ratios AS (
            SELECT r.*, ROW_NUMBER() OVER (
                PARTITION BY r.company_id 
                ORDER BY (r.return_on_equity_pct IS NOT NULL) DESC, r.year DESC
            ) as rn
            FROM financial_ratios r
        ),
        latest_mc AS (
            SELECT m.*, ROW_NUMBER() OVER (PARTITION BY m.company_id ORDER BY m.year DESC) as rn
            FROM market_cap m
        ),
        latest_pl AS (
            SELECT p.company_id, p.sales, p.operating_profit, p.net_profit, p.dividend_payout,
                   ROW_NUMBER() OVER (PARTITION BY p.company_id ORDER BY p.year DESC) as rn
            FROM profitandloss p
        )
        SELECT 
            c.id AS ticker,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            s.market_cap_category,
            r.year,
            r.net_profit_margin_pct,
            r.operating_profit_margin_pct,
            r.return_on_equity_pct,
            r.debt_to_equity,
            r.interest_coverage,
            r.asset_turnover,
            r.free_cash_flow_cr,
            r.capex_cr,
            r.earnings_per_share,
            r.book_value_per_share,
            r.dividend_payout_ratio_pct,
            r.revenue_cagr_3yr,
            r.revenue_cagr_5yr,
            r.revenue_cagr_10yr,
            r.pat_cagr_3yr,
            r.pat_cagr_5yr,
            r.cfo_pat_ratio,
            r.capex_intensity,
            r.capital_allocation_pattern,
            r.composite_score,
            mc.market_cap_crore,
            mc.enterprise_value_crore,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.ev_ebitda,
            mc.dividend_yield_pct,
            pl.sales,
            CASE 
                WHEN mc.market_cap_crore > 0 AND r.free_cash_flow_cr IS NOT NULL 
                THEN (r.free_cash_flow_cr / mc.market_cap_crore) * 100.0 
                ELSE NULL 
            END AS fcf_yield
        FROM companies c
        LEFT JOIN latest_ratios r ON c.id = r.company_id AND r.rn = 1
        LEFT JOIN latest_mc mc ON c.id = mc.company_id AND mc.rn = 1
        LEFT JOIN latest_pl pl ON c.id = pl.company_id AND pl.rn = 1
        LEFT JOIN sectors s ON c.id = s.company_id
        """
        df = pd.read_sql_query(query, conn)
    return df

def run_preset_screener(preset_key: str, df: pd.DataFrame, config: Dict[str, Any]) -> pd.DataFrame:
    """Run a specific preset screener on the dataset."""
    preset = config.get("presets", {}).get(preset_key)
    if not preset:
        raise ValueError(f"Unknown preset screener: {preset_key}")

    filters = preset.get("filters", {})
    res = df.copy()

    # Financial carve-out: do not disqualify banks/NBFCs strictly on D/E
    if "min_roe" in filters:
        res = res[res['return_on_equity_pct'].fillna(-999) >= filters["min_roe"]]
    if "max_de" in filters:
        max_de = filters["max_de"]
        is_fin = res['broad_sector'].isin(['Financials', 'Financial Services'])
        if max_de == 0:
            res = res[res['debt_to_equity'].fillna(999) == 0]
        else:
            res = res[(res['debt_to_equity'].fillna(999) <= max_de) | is_fin]
    if "min_fcf" in filters:
        res = res[res['free_cash_flow_cr'].fillna(-999999) > filters["min_fcf"]]
    if "min_rev_cagr_5yr" in filters:
        res = res[res['revenue_cagr_5yr'].fillna(-999) >= filters["min_rev_cagr_5yr"]]
    if "min_rev_cagr_3yr" in filters:
        res = res[res['revenue_cagr_3yr'].fillna(-999) >= filters["min_rev_cagr_3yr"]]
    if "min_pat_cagr_5yr" in filters:
        res = res[res['pat_cagr_5yr'].fillna(-999) >= filters["min_pat_cagr_5yr"]]
    if "max_pe" in filters:
        res = res[(res['pe_ratio'].fillna(999) <= filters["max_pe"]) & (res['pe_ratio'] > 0)]
    if "max_pb" in filters:
        res = res[res['pb_ratio'].fillna(999) <= filters["max_pb"]]
    if "min_div_yield" in filters:
        res = res[res['dividend_yield_pct'].fillna(0) >= filters["min_div_yield"]]
    if "max_payout" in filters:
        res = res[res['dividend_payout_ratio_pct'].fillna(999) <= filters["max_payout"]]
    if "min_sales" in filters:
        res = res[res['sales'].fillna(0) >= filters["min_sales"]]

    # Rank results
    rank_col = preset.get("ranking_metric", "composite_score")
    asc = preset.get("ranking_ascending", False)
    if rank_col in res.columns:
        res = res.sort_values(by=rank_col, ascending=asc)

    return res

def export_all_screeners(db_path: str = DB_PATH) -> Dict[str, pd.DataFrame]:
    """Execute all 6 preset screeners and export to screener_output.xlsx."""
    config = load_screener_config()
    df = get_latest_screener_universe(db_path)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "screener_output.xlsx")

    results = {}
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        for p_key in config.get("presets", {}).keys():
            p_name = config["presets"][p_key]["name"]
            sheet_title = p_name[:31] # Excel sheet name limit
            res_df = run_preset_screener(p_key, df, config)
            res_df.to_excel(writer, sheet_name=sheet_title, index=False)
            results[p_key] = res_df
            print(f"Preset '{p_name}': {len(res_df)} companies matched.")

    return results

if __name__ == "__main__":
    export_all_screeners()
