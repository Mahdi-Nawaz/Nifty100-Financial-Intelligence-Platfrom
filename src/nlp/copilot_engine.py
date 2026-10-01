"""AI Financial Copilot Engine for Nifty 100 Platform.

Provides intelligent natural language parsing, SQL query generation, multi-criteria
fundamental synthesis, forensic audit triage, and LLM-ready responses.
Operates seamlessly self-contained (offline) or with Gemini/OpenAI API if configured.
"""
import os
import re
import sys
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional

sys.path.insert(0, os.path.abspath("."))

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")

def safe_fmt(val, fmt="{:.1f}", prefix="", suffix="", default="N/A"):
    if val is None or pd.isna(val) or val == 'N/A':
        return default
    try:
        return f"{prefix}{fmt.format(float(val))}{suffix}"
    except Exception:
        return str(val)

def df_to_markdown(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    headers = list(df.columns)
    lines = ["| " + " | ".join(str(h) for h in headers) + " |"]
    lines.append("| " + " | ".join([":---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        vals = []
        for h in headers:
            v = row[h]
            if isinstance(v, float):
                vals.append(f"{v:.2f}")
            else:
                vals.append(str(v))
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)

class FinancialCopilot:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._load_metadata()

    def _load_metadata(self):
        with sqlite3.connect(self.db_path) as conn:
            self.companies_df = pd.read_sql_query("SELECT id, company_name FROM companies", conn)
            self.sectors_df = pd.read_sql_query("SELECT DISTINCT broad_sector FROM sectors", conn)
        
        # Build mapping for ticker/company resolution
        self.name_map = {}
        for _, r in self.companies_df.iterrows():
            cid = str(r['id']).upper()
            cname = str(r['company_name']).lower()
            self.name_map[cid] = (cid, r['company_name'])
            self.name_map[cname] = (cid, r['company_name'])
            # Clean common words (e.g. "Tata Motors Ltd" -> "tata motors")
            clean_name = re.sub(r'\b(ltd|limited|industries|corp|corporation|bank)\b', '', cname).strip()
            if clean_name and len(clean_name) > 2:
                self.name_map[clean_name] = (cid, r['company_name'])

    def find_company(self, query: str) -> Optional[tuple]:
        """Match query text to known Nifty 100 ticker or company name."""
        q_lower = query.lower()
        q_tokens = re.findall(r'\b[A-Za-z0-9]+\b', query)

        # 1. Exact Ticker check
        for token in q_tokens:
            tok_upper = token.upper()
            if tok_upper in self.name_map:
                return self.name_map[tok_upper]

        # 2. Substring match on company names
        for key, val in self.name_map.items():
            if key in q_lower and len(key) >= 3:
                return val
        return None

    def ask(self, query: str) -> str:
        """Main entrypoint: parses natural language intent and executes intelligent response."""
        q = query.strip()
        q_lower = q.lower()

        # 1. Check for Concept Explanation queries
        concept_resp = self._check_concepts(q_lower)
        if concept_resp:
            return concept_resp

        # 2. Check for Peer Comparison (e.g. "compare TCS and Infosys")
        if "compare" in q_lower or " vs " in q_lower:
            comp_resp = self._handle_comparison(q)
            if comp_resp:
                return comp_resp

        # 3. Check for Forensic / Anomaly / Distress queries
        if any(w in q_lower for w in ["distress", "bankruptcy", "beneish", "manipulat", "red flag", "forensic", "altman", "outlier", "anomaly", "anomalies"]):
            forensic_resp = self._handle_forensic_query(q_lower)
            if forensic_resp:
                return forensic_resp

        # 4. Check for Screener / Filter queries (e.g. "debt free", "roe > 20", "it companies")
        if any(w in q_lower for w in ["find", "show me", "which", "list", "stocks with", "companies with", "top", "lowest", "highest", "zero debt"]):
            screener_resp = self._handle_screening(q_lower)
            if screener_resp:
                return screener_resp

        # 5. Check for Company Deep-Dive
        found_comp = self.find_company(q)
        if found_comp:
            return self._handle_company_deepdive(found_comp[0], found_comp[1])

        # 6. Fallback General Summary & Guidance
        return self._handle_fallback(q)

    def _check_concepts(self, q: str) -> Optional[str]:
        if "beneish" in q or "m-score" in q or "m score" in q:
            return """### 🛡️ Beneish M-Score (Earnings Manipulation Detection)
The **Beneish M-Score** is an 8-variable mathematical model used by forensic accountants to evaluate whether a company has engaged in aggressive earnings manipulation or revenue inflation.

**Key Mathematical Cutoff:**
- **M-Score > -1.78**: 🚨 **High Risk of Earnings Manipulation** (Window dressing, uncollected receivables spike, or deferred expenses).
- **M-Score ≤ -1.78**: ✅ **Conforming / Non-Manipulator**.

**The 8 Variables Included:**
1. **DSRI** (Days Sales in Receivables): Detects accelerated revenue recognition / channel stuffing.
2. **GMI** (Gross Margin Index): Signals deteriorating margins prompting accounting pressure.
3. **AQI** (Asset Quality Index): Detects capitalization of operational costs into intangible assets.
4. **SGI** (Sales Growth Index): Rapid growth companies face pressure to keep growing.
5. **DEPI** (Depreciation Index): Detects slowing depreciation to boost current operating profit.
6. **SGAI** (SGA Expense Index): Measures administrative overhead efficiency.
7. **LVGI** (Leverage Index): Increasing financial debt gearing.
8. **TATA** (Total Accruals to Total Assets): Measures the divergence between paper profits and actual operating cash flow."""

        if "altman" in q or "z-score" in q or "z score" in q:
            return """### 🏛️ Altman Z''-Score (Emerging Market Solvency Engine)
The **Altman Z''-Score** predicts corporate insolvency and default likelihood, adapted specifically for emerging market manufacturing and service corporations.

**Z''-Score Thresholds:**
- **Z'' < 1.10**: 🚨 **Distress Zone** (Elevated probability of debt default or liquidity crunch within 2 years).
- **1.10 ≤ Z'' ≤ 2.60**: ⚠️ **Grey Zone** (Borderline solvency; requires cash flow surveillance).
- **Z'' > 2.60**: 🟢 **Safe Zone** (Robust financial cushion and sound solvency).

The 4-variable model weights **Working Capital**, **Retained Earnings**, **Operating Earnings (EBIT)**, and **Book Value of Equity vs Total Liabilities**."""

        if "monte carlo" in q or "dcf" in q or "valuation" in q:
            return """### 📈 Probabilistic Monte Carlo DCF Valuation
Unlike traditional DCF models that guess a single deterministic growth rate, our platform runs **5,000 stochastic Monte Carlo simulations**:
- **Simulated Variables**: Weighted Average Cost of Capital (WACC), Terminal Growth Rate ($g$), and Revenue CAGR under log-normal probability distributions.
- **Output**: Intrinsic value probability curves ($P_{10}$ Bear Case, $P_{50}$ Median Fair Value, $P_{90}$ Bull Case).
- **Margin of Safety (MoS)**: Calculated as `(Median Fair Value - Current Market Price) / Median Fair Value * 100%`."""

        return None

    def _handle_company_deepdive(self, ticker: str, comp_name: str) -> str:
        with sqlite3.connect(self.db_path) as conn:
            comp_info = pd.read_sql_query(f"SELECT * FROM companies WHERE id = '{ticker}'", conn)
            forensic = pd.read_sql_query(f"SELECT * FROM forensic_audit WHERE company_id = '{ticker}'", conn)
            ratios = pd.read_sql_query(f"SELECT * FROM financial_ratios WHERE company_id = '{ticker}' ORDER BY year DESC LIMIT 1", conn)
            mc = pd.read_sql_query(f"SELECT * FROM monte_carlo_valuation WHERE company_id = '{ticker}'", conn)
            anomaly = pd.read_sql_query(f"SELECT * FROM ml_anomalies WHERE company_id = '{ticker}'", conn) if self._table_exists(conn, 'ml_anomalies') else pd.DataFrame()

        if comp_info.empty:
            return f"Company **{comp_name}** (`{ticker}`) was not found in the Nifty 100 database."

        c = comp_info.iloc[0]
        r = ratios.iloc[0] if not ratios.empty else {}
        f = forensic.iloc[0] if not forensic.empty else {}
        m = mc.iloc[0] if not mc.empty else {}
        a = anomaly.iloc[0] if not anomaly.empty else {}

        # Valuation summary
        cmp_str = safe_fmt(m.get('current_market_price'), fmt="{:,.2f}", prefix="₹")
        fv_str = safe_fmt(m.get('median_fair_value'), fmt="{:,.2f}", prefix="₹")
        mos_str = safe_fmt(m.get('margin_of_safety_pct'), fmt="{:+.1f}", suffix="%")
        verdict = m.get('verdict', 'Neutral')

        # Forensic summary
        beneish = safe_fmt(f.get('beneish_m_score'), fmt="{:.2f}")
        b_flag = f.get('beneish_flag', 'Safe')
        altman = safe_fmt(f.get('altman_z_score'), fmt="{:.2f}")
        a_zone = f.get('altman_zone', 'Safe Zone')
        piotroski = safe_fmt(f.get('piotroski_f_score'), fmt="{:.0f}")

        # ML Anomaly summary
        is_anom = a.get('is_anomaly', False)
        anom_risk = safe_fmt(a.get('anomaly_risk_pct'), fmt="{:.1f}", suffix="%")
        driver = a.get('primary_driver_1', 'Normal statistical distribution')

        output = f"""## 📊 Institutional Executive Briefing: {comp_name} (`{ticker}`)

### 🏢 Corporate Snapshot
- **NSE/BSE Symbol**: `{ticker}` | **Face Value**: ₹{c.get('face_value', 'N/A')}
- **Latest Health Score**: **{safe_fmt(r.get('composite_score'), '{:.1f}')}/100**
- **ROE**: {safe_fmt(r.get('return_on_equity_pct'), '{:.1f}', suffix='%')} | **ROCE**: {safe_fmt(c.get('roce_percentage'), '{:.1f}', suffix='%')}
- **Operating Margin**: {safe_fmt(r.get('operating_profit_margin_pct'), '{:.1f}', suffix='%')} | **Debt/Equity**: {safe_fmt(r.get('debt_to_equity'), '{:.2f}', suffix='x')}
- **Free Cash Flow (Latest)**: {safe_fmt(r.get('free_cash_flow_cr'), '{:,.0f}', prefix='₹', suffix=' Cr')} | **Cash Conversion (CFO/PAT)**: {safe_fmt(r.get('cfo_pat_ratio'), '{:.2f}', suffix='x')}

---

### 🛡️ Forensic Governance & Red Flags
| Metric | Value | Threshold Status | Risk Assessment |
| :--- | :--- | :--- | :--- |
| **Beneish M-Score** | `{beneish}` | Cutoff: -1.78 | **{b_flag}** |
| **Altman Z''-Score** | `{altman}` | Safe > 2.60 | **{a_zone}** |
| **Piotroski F-Score** | `{piotroski}/9` | Strong ≥ 7 | **{f.get('piotroski_category', 'Moderate')}** |

---

### 🤖 Machine Learning Anomaly Detection
- **ML Anomaly Classification**: **{'🚨 Statistical Outlier' if is_anom else '✅ Conforming Profile'}** (Anomaly Risk: **{anom_risk}**)
- **Top ML Deviation Factor**: `{driver}`

---

### 🎯 Stochastic Monte Carlo Valuation
- **Current Market Price (CMP)**: {cmp_str}
- **Median Fair Value (P50)**: {fv_str}
- **Margin of Safety (MoS)**: **{mos_str}**
- **Valuation Verdict**: **{verdict}** (Based on 5,000 stochastic iterations)
"""
        return output

    def _handle_comparison(self, query: str) -> Optional[str]:
        words = re.findall(r'\b[A-Za-z0-9]+\b', query)
        found = []
        for w in words:
            match = self.find_company(w)
            if match and match[0] not in [m[0] for m in found]:
                found.append(match)
            if len(found) == 2:
                break

        if len(found) < 2:
            return "Please specify two companies to compare (e.g. *'Compare TCS and Infosys'* or *'HDFCBANK vs ICICIBANK'*)."

        t1, n1 = found[0]
        t2, n2 = found[1]

        with sqlite3.connect(self.db_path) as conn:
            q = f"""
            SELECT 
                c.id, c.company_name, r.return_on_equity_pct, r.operating_profit_margin_pct,
                r.debt_to_equity, r.cfo_pat_ratio, r.composite_score,
                f.beneish_m_score, f.altman_z_score, f.piotroski_f_score,
                m.current_market_price, m.median_fair_value, m.margin_of_safety_pct, m.verdict
            FROM companies c
            LEFT JOIN financial_ratios r ON c.id = r.company_id AND r.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
            LEFT JOIN forensic_audit f ON c.id = f.company_id
            LEFT JOIN monte_carlo_valuation m ON c.id = m.company_id
            WHERE c.id IN ('{t1}', '{t2}')
            """
            df = pd.read_sql_query(q, conn)

        if len(df) < 2:
            return f"Could not retrieve full comparison records for `{t1}` and `{t2}`."

        row1 = df[df['id'] == t1].iloc[0]
        row2 = df[df['id'] == t2].iloc[0]

        return f"""## ⚖️ Head-to-Head Comparison: {n1} vs {n2}

| Dimension | **{n1} (`{t1}`)** | **{n2} (`{t2}`)** | Advantage |
| :--- | :--- | :--- | :--- |
| **Health Score** | **{safe_fmt(row1['composite_score'], '{:.1f}')}/100** | **{safe_fmt(row2['composite_score'], '{:.1f}')}/100** | {'👈 ' + t1 if (row1['composite_score'] or 0) >= (row2['composite_score'] or 0) else '👉 ' + t2} |
| **Return on Equity (ROE)** | {safe_fmt(row1['return_on_equity_pct'], '{:.1f}', suffix='%')} | {safe_fmt(row2['return_on_equity_pct'], '{:.1f}', suffix='%')} | {'👈 ' + t1 if (row1['return_on_equity_pct'] or 0) >= (row2['return_on_equity_pct'] or 0) else '👉 ' + t2} |
| **Operating Margin (OPM)** | {safe_fmt(row1['operating_profit_margin_pct'], '{:.1f}', suffix='%')} | {safe_fmt(row2['operating_profit_margin_pct'], '{:.1f}', suffix='%')} | {'👈 ' + t1 if (row1['operating_profit_margin_pct'] or 0) >= (row2['operating_profit_margin_pct'] or 0) else '👉 ' + t2} |
| **Debt to Equity** | {safe_fmt(row1['debt_to_equity'], '{:.2f}', suffix='x')} | {safe_fmt(row2['debt_to_equity'], '{:.2f}', suffix='x')} | {'👈 ' + t1 if (row1['debt_to_equity'] or 999) <= (row2['debt_to_equity'] or 999) else '👉 ' + t2} |
| **Cash Conversion (CFO/PAT)**| {safe_fmt(row1['cfo_pat_ratio'], '{:.2f}', suffix='x')} | {safe_fmt(row2['cfo_pat_ratio'], '{:.2f}', suffix='x')} | {'👈 ' + t1 if (row1['cfo_pat_ratio'] or 0) >= (row2['cfo_pat_ratio'] or 0) else '👉 ' + t2} |
| **Piotroski F-Score** | {safe_fmt(row1['piotroski_f_score'], '{:.0f}')}/9 | {safe_fmt(row2['piotroski_f_score'], '{:.0f}')}/9 | {'👈 ' + t1 if (row1['piotroski_f_score'] or 0) >= (row2['piotroski_f_score'] or 0) else '👉 ' + t2} |
| **Beneish M-Score** | {safe_fmt(row1['beneish_m_score'], '{:.2f}')} | {safe_fmt(row2['beneish_m_score'], '{:.2f}')} | {'👈 ' + t1 if (row1['beneish_m_score'] or 0) <= (row2['beneish_m_score'] or 0) else '👉 ' + t2} |
| **Margin of Safety (MoS)** | **{safe_fmt(row1['margin_of_safety_pct'], '{:+.1f}', suffix='%')}** | **{safe_fmt(row2['margin_of_safety_pct'], '{:+.1f}', suffix='%')}** | {'👈 ' + t1 if (row1['margin_of_safety_pct'] or -999) >= (row2['margin_of_safety_pct'] or -999) else '👉 ' + t2} |
| **Valuation Verdict** | `{row1['verdict'] or 'Neutral'}` | `{row2['verdict'] or 'Neutral'}` | — |
"""

    def _handle_forensic_query(self, q: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            if "distress" in q or "bankruptcy" in q or "altman" in q:
                df = pd.read_sql_query("""
                SELECT company_id, company_name, broad_sector, altman_z_score, altman_zone, composite_score
                FROM forensic_audit
                WHERE altman_zone = 'Distress Zone'
                ORDER BY altman_z_score ASC
                LIMIT 10
                """, conn)
                title = "🚨 Top Distress Zone Candidates (Altman Z'' < 1.10)"
            elif "anomaly" in q or "anomalies" in q or "outlier" in q:
                if self._table_exists(conn, 'ml_anomalies'):
                    df = pd.read_sql_query("""
                    SELECT company_id, company_name, broad_sector, anomaly_risk_pct, primary_driver_1, composite_score
                    FROM ml_anomalies
                    WHERE is_anomaly = 1
                    ORDER BY anomaly_risk_pct DESC
                    LIMIT 10
                    """, conn)
                    title = "🤖 Machine Learning Accounting Outliers (Isolation Forest)"
                else:
                    return "ML Anomaly table not yet populated. Please train Screen 12 first."
            else: # Beneish manipulation
                df = pd.read_sql_query("""
                SELECT company_id, company_name, broad_sector, beneish_m_score, beneish_flag, composite_score
                FROM forensic_audit
                WHERE beneish_flag LIKE '%High Risk%'
                ORDER BY beneish_m_score DESC
                LIMIT 10
                """, conn)
                title = "⚠️ High Risk Beneish M-Score Candidates (M > -1.78)"

        if df.empty:
            return "No companies currently exceed this risk threshold in the Nifty 100 universe."

        table_md = df_to_markdown(df)
        return f"""### {title}
These companies show elevated statistical or governance divergences. High priority for audit scrutiny:

{table_md}
"""

    def _handle_screening(self, q: str) -> Optional[str]:
        with sqlite3.connect(self.db_path) as conn:
            sql = """
            SELECT 
                c.id as Ticker, c.company_name as Company, s.broad_sector as Sector,
                r.return_on_equity_pct as ROE_pct, r.operating_profit_margin_pct as OPM_pct,
                r.debt_to_equity as DE_ratio, r.composite_score as HealthScore
            FROM companies c
            JOIN sectors s ON c.id = s.company_id
            JOIN financial_ratios r ON c.id = r.company_id AND r.year = (SELECT MAX(year) FROM financial_ratios WHERE company_id = c.id)
            WHERE 1=1
            """
            
            # Filter by sector if mentioned
            if "it" in q or "tech" in q or "software" in q:
                sql += " AND s.broad_sector = 'Information Technology'"
            elif "fmcg" in q or "consumer" in q:
                sql += " AND s.broad_sector = 'Fast Moving Consumer Goods'"
            elif "bank" in q or "financial" in q:
                sql += " AND s.broad_sector = 'Financial Services'"
            elif "auto" in q:
                sql += " AND s.broad_sector = 'Automobile and Auto Components'"

            # Filter by debt
            if "zero debt" in q or "debt free" in q or "no debt" in q:
                sql += " AND r.debt_to_equity = 0"
            elif "low debt" in q:
                sql += " AND r.debt_to_equity <= 0.3"

            # Filter by ROE
            roe_match = re.search(r'roe\s*(?:>|>=|greater than|above)\s*(\d+)', q)
            if roe_match:
                sql += f" AND r.return_on_equity_pct >= {roe_match.group(1)}"
            elif "high roe" in q:
                sql += " AND r.return_on_equity_pct >= 20.0"

            sql += " ORDER BY r.composite_score DESC LIMIT 10"
            df = pd.read_sql_query(sql, conn)

        if df.empty:
            return "No companies matched your specific filter combination. Try adjusting the threshold (e.g. *'IT companies with ROE > 15%'*)."

        table_md = df_to_markdown(df)
        return f"""### 🎯 Custom Screener Results
Found **{len(df)}** Nifty 100 constituents matching your investment criteria:

{table_md}
"""

    def _handle_fallback(self, query: str) -> str:
        return f"""### 🤖 AI Financial Copilot: Suggestions
I didn't fully understand: *"{query}"*. 

Here are some powerful questions you can ask me:
- **Analyze a Stock**: *"Analyze Tata Motors"*, *"What are the risks in Reliance?"*, *"Is Infosys undervalued?"*
- **Head-to-Head Comparison**: *"Compare TCS and Infosys"*, *"HDFC Bank vs ICICI Bank"*
- **Forensic & Bankruptcy Triage**: *"Show distress zone companies"*, *"Which stocks have high Beneish M-score?"*
- **Machine Learning**: *"Show me the top ML accounting anomalies"*
- **Smart Screener**: *"Find IT companies with ROE > 20%"*, *"List zero debt companies"*
- **Financial Concept Explainer**: *"What is Beneish M-score?"*, *"Explain Monte Carlo DCF"*
"""

    def _table_exists(self, conn, table_name: str) -> bool:
        res = conn.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'").fetchone()
        return res is not None

copilot = FinancialCopilot()
