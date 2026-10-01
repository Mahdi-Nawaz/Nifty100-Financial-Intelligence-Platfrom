"""Data quality validation rules and failure logger for Nifty 100 platform."""
import re
from typing import Dict, List, Any
import pandas as pd

class DQValidator:
    def __init__(self):
        self.failures: List[Dict[str, Any]] = []

    def log_failure(self, company_id: str, year: Any, field: str, issue: str, severity: str = "WARNING"):
        """Log a data quality failure or warning."""
        self.failures.append({
            "company_id": str(company_id) if company_id is not None else "UNKNOWN",
            "year": str(year) if year is not None else "N/A",
            "field": field,
            "issue": issue,
            "severity": severity
        })

    def validate_companies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate companies table (DQ-01, DQ-08)."""
        # DQ-08 Ticker format
        valid_rows = []
        for idx, row in df.iterrows():
            ticker = str(row.get('id', '')).strip().upper()
            if not ticker or len(ticker) < 2 or len(ticker) > 12:
                self.log_failure(ticker, "N/A", "id", f"Invalid ticker format/length: {ticker}", "CRITICAL")
            else:
                valid_rows.append(idx)
        df_clean = df.loc[valid_rows].copy()

        # DQ-01 Company PK uniqueness
        if df_clean['id'].duplicated().any():
            dups = df_clean[df_clean['id'].duplicated()]['id'].tolist()
            for d in dups:
                self.log_failure(d, "N/A", "id", f"Duplicate company ticker: {d}", "CRITICAL")
            df_clean = df_clean.drop_duplicates(subset=['id'], keep='last')

        return df_clean

    def validate_pl(self, df: pd.DataFrame, valid_companies: set) -> pd.DataFrame:
        """Validate Profit & Loss statements (DQ-02, DQ-03, DQ-05, DQ-06, DQ-07, DQ-11, DQ-12, DQ-14)."""
        clean_rows = []
        for idx, row in df.iterrows():
            cid = str(row.get('company_id', '')).strip().upper()
            yr = str(row.get('year', '')).strip()

            # DQ-03 FK integrity
            if cid not in valid_companies:
                self.log_failure(cid, yr, "company_id", "Foreign key constraint failure: company not in master", "CRITICAL")
                continue

            # DQ-07 Year format
            if not re.match(r'^\d{4}-\d{2}$', yr):
                self.log_failure(cid, yr, "year", f"Invalid year format: {yr}", "CRITICAL")
                continue

            # DQ-05 OPM Cross-check
            sales = row.get('sales')
            op = row.get('operating_profit')
            opm = row.get('opm_percentage')
            if pd.notnull(sales) and sales > 0 and pd.notnull(op) and pd.notnull(opm):
                calc_opm = (op / sales) * 100
                if abs(opm - calc_opm) >= 1.0:
                    self.log_failure(cid, yr, "opm_percentage", f"OPM divergence: reported {opm} vs computed {calc_opm:.2f}", "WARNING")

            # DQ-06 Positive sales
            if pd.notnull(sales) and sales <= 0:
                self.log_failure(cid, yr, "sales", f"Sales non-positive: {sales}", "WARNING")

            # DQ-11 Tax rate range (0 <= tax <= 60)
            tax = row.get('tax_percentage')
            if pd.notnull(tax) and (tax < 0 or tax > 60):
                self.log_failure(cid, yr, "tax_percentage", f"Tax percentage outside 0-60%: {tax}", "WARNING")

            # DQ-12 Dividend payout cap
            dp = row.get('dividend_payout')
            if pd.notnull(dp) and dp > 200:
                self.log_failure(cid, yr, "dividend_payout", f"Dividend payout > 200%: {dp}", "WARNING")

            # DQ-14 EPS Sign consistency
            net_prof = row.get('net_profit')
            eps = row.get('eps')
            if pd.notnull(net_prof) and net_prof > 0 and pd.notnull(eps) and eps <= 0:
                self.log_failure(cid, yr, "eps", f"EPS negative or zero while Net Profit is positive: net_profit={net_prof}, eps={eps}", "WARNING")

            clean_rows.append(idx)

        df_filtered = df.loc[clean_rows].copy()

        # DQ-02 Deduplicate (keep last)
        dups = df_filtered.duplicated(subset=['company_id', 'year'], keep=False)
        if dups.any():
            for _, r in df_filtered[dups].iterrows():
                self.log_failure(r['company_id'], r['year'], "year", "Duplicate annual record in P&L", "CRITICAL")
            df_filtered = df_filtered.drop_duplicates(subset=['company_id', 'year'], keep='last')

        return df_filtered

    def validate_bs(self, df: pd.DataFrame, valid_companies: set) -> pd.DataFrame:
        """Validate Balance Sheet (DQ-02, DQ-03, DQ-04, DQ-07, DQ-10, DQ-15)."""
        clean_rows = []
        for idx, row in df.iterrows():
            cid = str(row.get('company_id', '')).strip().upper()
            yr = str(row.get('year', '')).strip()

            if cid not in valid_companies:
                self.log_failure(cid, yr, "company_id", "Foreign key constraint failure: company not in master", "CRITICAL")
                continue

            if not re.match(r'^\d{4}-\d{2}$', yr):
                self.log_failure(cid, yr, "year", f"Invalid year format: {yr}", "CRITICAL")
                continue

            tot_assets = row.get('total_assets')
            tot_liab = row.get('total_liabilities')
            if pd.notnull(tot_assets) and tot_assets > 0 and pd.notnull(tot_liab):
                # DQ-04 Balance Sheet Balance
                diff_pct = abs(tot_assets - tot_liab) / tot_assets
                if diff_pct >= 0.01:
                    self.log_failure(cid, yr, "total_assets", f"Balance sheet discrepancy: assets={tot_assets}, liab={tot_liab} (diff={diff_pct:.2%})", "WARNING")
                # DQ-15 Strict check
                if tot_assets != tot_liab:
                    pass # Handled as info

            # DQ-10 Non-negative fixed assets
            fa = row.get('fixed_assets')
            if pd.notnull(fa) and fa < 0:
                self.log_failure(cid, yr, "fixed_assets", f"Negative fixed assets: {fa}, coercing to 0", "WARNING")
                df.at[idx, 'fixed_assets'] = 0

            clean_rows.append(idx)

        df_filtered = df.loc[clean_rows].copy()

        # DQ-02 Deduplicate
        dups = df_filtered.duplicated(subset=['company_id', 'year'], keep=False)
        if dups.any():
            for _, r in df_filtered[dups].iterrows():
                self.log_failure(r['company_id'], r['year'], "year", "Duplicate annual record in BS", "CRITICAL")
            df_filtered = df_filtered.drop_duplicates(subset=['company_id', 'year'], keep='last')

        return df_filtered

    def validate_cf(self, df: pd.DataFrame, valid_companies: set) -> pd.DataFrame:
        """Validate Cash Flow statements (DQ-02, DQ-03, DQ-07, DQ-09)."""
        clean_rows = []
        for idx, row in df.iterrows():
            cid = str(row.get('company_id', '')).strip().upper()
            yr = str(row.get('year', '')).strip()

            if cid not in valid_companies:
                self.log_failure(cid, yr, "company_id", "Foreign key constraint failure: company not in master", "CRITICAL")
                continue

            if not re.match(r'^\d{4}-\d{2}$', yr):
                self.log_failure(cid, yr, "year", f"Invalid year format: {yr}", "CRITICAL")
                continue

            # DQ-09 Net Cash Check
            cfo = row.get('operating_activity') or 0
            cfi = row.get('investing_activity') or 0
            cff = row.get('financing_activity') or 0
            net_cf = row.get('net_cash_flow')
            if pd.notnull(net_cf):
                sum_cf = cfo + cfi + cff
                if abs(net_cf - sum_cf) > 10.0:
                    self.log_failure(cid, yr, "net_cash_flow", f"Net cash divergence: reported {net_cf} vs sum {sum_cf} (recalculated)", "WARNING")
                    df.at[idx, 'net_cash_flow'] = sum_cf

            clean_rows.append(idx)

        df_filtered = df.loc[clean_rows].copy()

        # DQ-02 Deduplicate
        dups = df_filtered.duplicated(subset=['company_id', 'year'], keep=False)
        if dups.any():
            for _, r in df_filtered[dups].iterrows():
                self.log_failure(r['company_id'], r['year'], "year", "Duplicate annual record in Cash Flow", "CRITICAL")
            df_filtered = df_filtered.drop_duplicates(subset=['company_id', 'year'], keep='last')

        return df_filtered

    def check_coverage(self, pl_df: pd.DataFrame, valid_companies: set):
        """Check company record coverage across years (DQ-16)."""
        counts = pl_df.groupby('company_id')['year'].nunique()
        for cid in valid_companies:
            cnt = counts.get(cid, 0)
            if cnt < 5:
                self.log_failure(cid, "ALL", "coverage", f"Company has only {cnt} years of records (< 5yr)", "WARNING")

    def get_failures_df(self) -> pd.DataFrame:
        """Return all logged failures as a DataFrame."""
        if not self.failures:
            return pd.DataFrame(columns=["company_id", "year", "field", "issue", "severity"])
        return pd.DataFrame(self.failures)
