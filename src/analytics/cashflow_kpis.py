"""Cash flow intelligence, capital allocation classification, and quality metrics."""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple

def classify_capital_allocation(cfo: float, cfi: float, cff: float) -> Tuple[str, str, str, str]:
    """
    Classify 8 sign patterns of (CFO, CFI, CFF) into descriptive capital allocation labels.
    Returns: (cfo_sign, cfi_sign, cff_sign, pattern_label)
    """
    s_cfo = "+" if cfo >= 0 else "-"
    s_cfi = "+" if cfi >= 0 else "-"
    s_cff = "+" if cff >= 0 else "-"

    pattern = (s_cfo, s_cfi, s_cff)

    labels = {
        ('+', '-', '-'): 'Reinvestor & Shareholder Returns',
        ('+', '-', '+'): 'Growth via External Capital',
        ('+', '+', '-'): 'Divestment & Debt Repayment',
        ('+', '+', '+'): 'Cash Hoarding',
        ('-', '-', '+'): 'Distress / External Funding',
        ('-', '-', '-'): 'Rapid Cash Burn',
        ('-', '+', '+'): 'Asset Sale & Debt Funding',
        ('-', '+', '-'): 'Restructuring & Contraction'
    }

    label = labels.get(pattern, 'Unclassified')
    return s_cfo, s_cfi, s_cff, label

def compute_cashflow_kpis(cf_df: pd.DataFrame, pl_df: pd.DataFrame, bs_df: pd.DataFrame) -> pd.DataFrame:
    """Compute comprehensive cash flow and capital allocation metrics per company-year."""
    # Merge CF with P&L and BS on company_id, year
    merged = cf_df.merge(
        pl_df[['company_id', 'year', 'sales', 'operating_profit', 'net_profit']], 
        on=['company_id', 'year'], 
        how='left'
    ).merge(
        bs_df[['company_id', 'year', 'borrowings']], 
        on=['company_id', 'year'], 
        how='left'
    )
    
    # Sort for lag calculations
    merged = merged.sort_values(by=['company_id', 'year']).reset_index(drop=True)
    
    records = []
    for _, row in merged.iterrows():
        cid = row['company_id']
        yr = row['year']
        cfo = row.get('operating_activity') or 0.0
        cfi = row.get('investing_activity') or 0.0
        cff = row.get('financing_activity') or 0.0
        sales = row.get('sales') or 0.0
        ebitda = row.get('operating_profit') or 0.0
        pat = row.get('net_profit') or 0.0

        fcf = cfo + cfi
        capex = abs(cfi)

        # CFO Quality Score (CFO / PAT)
        cfo_pat = (cfo / pat) if pat and pat != 0 else np.nan
        quality_score = "High Quality Earnings" if cfo_pat and cfo_pat > 1.0 else ("Accrual Risk" if cfo_pat and cfo_pat < 0.5 else "Moderate")

        # CapEx Intensity
        capex_intensity = (capex / sales * 100.0) if sales > 0 else np.nan
        intensity_label = "Asset-Light" if capex_intensity and capex_intensity < 3.0 else ("Capital Intensive" if capex_intensity and capex_intensity > 8.0 else "Balanced")

        # FCF Conversion Rate
        fcf_conv = (fcf / ebitda * 100.0) if ebitda > 0 else np.nan

        # Distress & Deleveraging flags
        distress_signal = (cfo < 0 and cff > 0)

        s_cfo, s_cfi, s_cff, cap_label = classify_capital_allocation(cfo, cfi, cff)

        records.append({
            'company_id': cid,
            'year': yr,
            'cfo_cr': round(cfo, 2),
            'cfi_cr': round(cfi, 2),
            'cff_cr': round(cff, 2),
            'free_cash_flow_cr': round(fcf, 2),
            'capex_cr': round(capex, 2),
            'cfo_pat_ratio': round(cfo_pat, 2) if pd.notnull(cfo_pat) else None,
            'cfo_quality_label': quality_score,
            'capex_intensity_pct': round(capex_intensity, 2) if pd.notnull(capex_intensity) else None,
            'capex_intensity_label': intensity_label,
            'fcf_conversion_rate': round(fcf_conv, 2) if pd.notnull(fcf_conv) else None,
            'distress_signal': distress_signal,
            'cfo_sign': s_cfo,
            'cfi_sign': s_cfi,
            'cff_sign': s_cfi,
            'cff_sign_actual': s_cff,
            'capital_allocation_pattern': cap_label
        })

    return pd.DataFrame(records)
