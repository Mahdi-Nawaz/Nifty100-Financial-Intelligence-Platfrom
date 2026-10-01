"""FastAPI REST API Server for Nifty 100 Financial Intelligence Platform."""
import os
import sys
import time
import json
import sqlite3
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
from src.analytics.screener.engine import get_latest_screener_universe

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
SERVER_START_TIME = time.time()

app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    description="REST API service providing quantitative fundamentals, screening, and scoring for 92 Nifty 100 constituents.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 1. Health Endpoint (11.16)
@app.get("/api/v1/health", tags=["System"])
def get_health():
    """Server health check returning DB row counts and uptime."""
    counts = {}
    tables = [
        'companies', 'profitandloss', 'balancesheet', 'cashflow', 'analysis',
        'documents', 'prosandcons', 'sectors', 'market_cap', 'stock_prices',
        'financial_ratios', 'peer_groups'
    ]
    with get_db() as conn:
        for t in tables:
            try:
                c = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                counts[t] = c
            except Exception:
                counts[t] = 0

    return {
        "status": "ok",
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - SERVER_START_TIME, 1),
        "db_row_counts": counts
    }

# 2. Companies List (11.1)
@app.get("/api/v1/companies", tags=["Companies"])
def list_companies(sector: Optional[str] = None, search: Optional[str] = None):
    """List all companies with id, name, sector."""
    query = """
        SELECT c.id, c.company_name, s.broad_sector, s.sub_sector, c.roe_percentage, c.roce_percentage
        FROM companies c
        LEFT JOIN sectors s ON c.id = s.company_id
        WHERE 1=1
    """
    params = []
    if sector:
        query += " AND s.broad_sector = ?"
        params.append(sector)
    if search:
        query += " AND (c.id LIKE ? OR c.company_name LIKE ?)"
        params.extend([f"%{search}%", f"%{search}%"])

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

# 3. Company Profile (11.2)
@app.get("/api/v1/companies/{ticker}", tags=["Companies"])
def get_company_profile(ticker: str):
    """Full company profile including latest KPIs, sector, and pros/cons."""
    ticker = ticker.strip().upper()
    with get_db() as conn:
        c = conn.execute("SELECT * FROM companies WHERE id = ?", (ticker,)).fetchone()
        if not c:
            raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")
        
        comp_dict = dict(c)
        sec = conn.execute("SELECT broad_sector, sub_sector FROM sectors WHERE company_id = ?", (ticker,)).fetchone()
        if sec:
            comp_dict.update(dict(sec))

        # Latest ratios
        r = conn.execute("SELECT * FROM financial_ratios WHERE company_id = ? ORDER BY year DESC LIMIT 1", (ticker,)).fetchone()
        if r:
            comp_dict['latest_ratios'] = dict(r)

        # Pros and Cons
        pc_rows = conn.execute("SELECT pros, cons FROM prosandcons WHERE company_id = ?", (ticker,)).fetchall()
        comp_dict['pros_and_cons'] = [dict(row) for row in pc_rows]

        # Also attach rule-generated pros/cons if available
        if os.path.exists("output/pros_cons_generated.csv"):
            try:
                gen_df = pd.read_csv("output/pros_cons_generated.csv")
                match_gen = gen_df[gen_df['company_id'] == ticker]
                comp_dict['generated_pros_cons'] = match_gen.to_dict(orient='records')
            except Exception:
                comp_dict['generated_pros_cons'] = []

        return comp_dict

# 4. Profit & Loss History (11.3)
@app.get("/api/v1/companies/{ticker}/pl", tags=["Financial Statements"])
def get_company_pl(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """P&L statement history for a company."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM profitandloss WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No P&L records found.")
        return [dict(r) for r in rows]

# 5. Balance Sheet History (11.4)
@app.get("/api/v1/companies/{ticker}/bs", tags=["Financial Statements"])
def get_company_bs(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Balance sheet statement history for a company."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM balancesheet WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No Balance Sheet records found.")
        return [dict(r) for r in rows]

# 6. Cash Flow History (11.5)
@app.get("/api/v1/companies/{ticker}/cashflow", tags=["Financial Statements"])
def get_company_cashflow(ticker: str, from_year: Optional[str] = None, to_year: Optional[str] = None):
    """Cash flow statement history for a company."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM cashflow WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No Cash Flow records found.")
        return [dict(r) for r in rows]

# 7. Ratios History (11.6 & AC-12)
@app.get("/api/v1/companies/{ticker}/ratios", tags=["Financial Ratios"])
def get_company_ratios(ticker: str, year: Optional[str] = None):
    """Pre-computed KPIs and ratios per year for a company."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM financial_ratios WHERE company_id = ?"
    params = [ticker]
    if year:
        query += " AND year = ?"
        params.append(year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No ratio records found for '{ticker}'.")
        return [dict(r) for r in rows]

# 8. Download Tearsheet PDF (11.7)
@app.get("/api/v1/companies/{ticker}/tearsheet", tags=["Reports"])
def download_tearsheet(ticker: str):
    """Download pre-generated 2-page company tearsheet PDF."""
    ticker = ticker.strip().upper()
    pdf_path = os.path.join("reports/tearsheets", f"{ticker}_tearsheet.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail=f"Tearsheet PDF for '{ticker}' not found.")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{ticker}_tearsheet.pdf")

# 9. Investment Screener (11.8 & AC-13)
@app.get("/api/v1/screener", tags=["Screener"])
def run_screener_api(
    min_roe: Optional[float] = None,
    max_de: Optional[float] = None,
    min_fcf: Optional[float] = None,
    sector: Optional[str] = None,
    min_rev_cagr_5yr: Optional[float] = None,
    min_pat_cagr_5yr: Optional[float] = None,
    max_pe: Optional[float] = None
):
    """Multi-parameter screener returning ranked list of companies."""
    df = get_latest_screener_universe(DB_PATH)
    is_fin = df['broad_sector'].isin(['Financials', 'Financial Services'])

    if min_roe is not None:
        df = df[df['return_on_equity_pct'].fillna(-999) >= min_roe]
    if max_de is not None:
        if max_de == 0:
            df = df[df['debt_to_equity'].fillna(999) == 0]
        else:
            df = df[(df['debt_to_equity'].fillna(999) <= max_de) | is_fin]
    if min_fcf is not None:
        df = df[df['free_cash_flow_cr'].fillna(-999999) > min_fcf]
    if sector:
        df = df[df['broad_sector'] == sector]
    if min_rev_cagr_5yr is not None:
        df = df[df['revenue_cagr_5yr'].fillna(-999) >= min_rev_cagr_5yr]
    if min_pat_cagr_5yr is not None:
        df = df[df['pat_cagr_5yr'].fillna(-999) >= min_pat_cagr_5yr]
    if max_pe is not None:
        df = df[(df['pe_ratio'].fillna(999) <= max_pe) & (df['pe_ratio'] > 0)]

    df = df.sort_values(by='composite_score', ascending=False)
    # Convert numpy nan to None for JSON
    res_dict = json.loads(df.to_json(orient='records'))
    return res_dict

# 10. Sectors Overview (11.9)
@app.get("/api/v1/sectors", tags=["Sectors"])
def list_sectors():
    """List all broad sectors with company count and median KPIs."""
    df = get_latest_screener_universe(DB_PATH)
    res = df.groupby('broad_sector').agg({
        'ticker': 'count',
        'return_on_equity_pct': 'median',
        'pe_ratio': 'median',
        'debt_to_equity': 'median',
        'market_cap_crore': 'sum'
    }).reset_index().rename(columns={
        'ticker': 'company_count',
        'return_on_equity_pct': 'median_roe',
        'pe_ratio': 'median_pe',
        'debt_to_equity': 'median_de',
        'market_cap_crore': 'total_mkt_cap_cr'
    })
    return json.loads(res.to_json(orient='records'))

# 11. Companies in Sector (11.10)
@app.get("/api/v1/sectors/{sector}/companies", tags=["Sectors"])
def get_sector_companies(sector: str):
    """All companies in a sector with KPI summary."""
    df = get_latest_screener_universe(DB_PATH)
    filtered = df[df['broad_sector'].str.lower() == sector.lower()]
    if filtered.empty:
        raise HTTPException(status_code=404, detail=f"No companies found for sector '{sector}'.")
    return json.loads(filtered.to_json(orient='records'))

# 12. Peer Group Members & Percentiles (11.11)
@app.get("/api/v1/peers/{group_name}", tags=["Peers"])
def get_peer_group(group_name: str):
    """All companies in a peer group with percentile ranks."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT p.peer_group, p.company_id, c.company_name, p.metric, p.value, p.percentile_rank
            FROM peer_percentiles p
            JOIN companies c ON p.company_id = c.id
            WHERE LOWER(p.peer_group) = LOWER(?)
        """, (group_name,)).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail=f"Peer group '{group_name}' not found.")
        return [dict(r) for r in rows]

# 13. Radar Comparison Data (11.12)
@app.get("/api/v1/companies/{ticker}/peers/compare", tags=["Peers"])
def get_peer_compare(ticker: str):
    """Radar data: company metrics vs peer group average."""
    ticker = ticker.strip().upper()
    df = get_latest_screener_universe(DB_PATH)
    target = df[df['ticker'] == ticker]
    if target.empty:
        raise HTTPException(status_code=404, detail=f"Company '{ticker}' not found.")
    
    sec = target.iloc[0].get('broad_sector')
    sector_peers = df[df['broad_sector'] == sec]

    radar_metrics = ['return_on_equity_pct', 'operating_profit_margin_pct', 'net_profit_margin_pct', 'revenue_cagr_5yr', 'pat_cagr_5yr', 'cfo_pat_ratio', 'composite_score']
    
    comp_metrics = {m: float(target.iloc[0].get(m) or 0.0) for m in radar_metrics}
    avg_metrics = {m: float(sector_peers[m].median() or 0.0) for m in radar_metrics}

    return {
        "ticker": ticker,
        "sector": sec,
        "company_metrics": comp_metrics,
        "peer_median_metrics": avg_metrics
    }

# 14. Historical Valuation Multiples (11.13)
@app.get("/api/v1/market-cap/{ticker}", tags=["Valuation"])
def get_market_cap_history(ticker: str, from_year: Optional[int] = None, to_year: Optional[int] = None):
    """Historical valuation multiples (P/E, P/B, EV/EBITDA, Dividend Yield)."""
    ticker = ticker.strip().upper()
    query = "SELECT * FROM market_cap WHERE company_id = ?"
    params = [ticker]
    if from_year:
        query += " AND year >= ?"
        params.append(from_year)
    if to_year:
        query += " AND year <= ?"
        params.append(to_year)
    query += " ORDER BY year ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail="No market cap records found.")
        return [dict(r) for r in rows]

# 15. Portfolio Statistics (11.14)
@app.get("/api/v1/portfolio/stats", tags=["Analytics"])
def get_portfolio_statistics():
    """Portfolio-level statistics: P10 to P90 for core KPIs."""
    stats_path = "output/portfolio_stats.csv"
    if not os.path.exists(stats_path):
        raise HTTPException(status_code=404, detail="Portfolio statistics not generated.")
    df = pd.read_csv(stats_path)
    return json.loads(df.to_json(orient='records'))

# 16. Annual Reports / Documents (11.15)
@app.get("/api/v1/companies/{ticker}/documents", tags=["Documents"])
def get_company_documents(ticker: str):
    """Annual report links for a company."""
    ticker = ticker.strip().upper()
    with get_db() as conn:
        rows = conn.execute("SELECT Year, Annual_Report FROM documents WHERE company_id = ? ORDER BY Year DESC", (ticker,)).fetchall()
        if not rows:
            raise HTTPException(status_code=404, detail=f"No annual reports found for '{ticker}'.")
        return [dict(r) for r in rows]

# 17. Forensic Summary Leaderboard
@app.get("/api/v1/forensics/summary", tags=["Forensics"])
def get_forensics_summary():
    """Universe-wide forensic audit summary across safe and distress candidates."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM forensic_audit ORDER BY piotroski_f_score DESC, altman_z_score DESC").fetchall()
        if not rows:
            from src.analytics.forensics import compute_forensic_scores
            compute_forensic_scores(DB_PATH)
            rows = conn.execute("SELECT * FROM forensic_audit ORDER BY piotroski_f_score DESC, altman_z_score DESC").fetchall()
        return [dict(r) for r in rows]

# 18. Forensic Accounting Triage (Beneish M, Altman Z, Piotroski F)
@app.get("/api/v1/forensics/{ticker}", tags=["Forensics"])
def get_company_forensic_audit(ticker: str):
    """Forensic red flag analysis including Beneish M-Score, Altman Z''-Score, and Piotroski F-Score."""
    ticker = ticker.strip().upper()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM forensic_audit WHERE company_id = ?", (ticker,)).fetchone()
        if not row:
            from src.analytics.forensics import compute_forensic_scores
            compute_forensic_scores(DB_PATH)
            row = conn.execute("SELECT * FROM forensic_audit WHERE company_id = ?", (ticker,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"Forensic audit not available for '{ticker}'.")
        return dict(row)

# 19. Quantitative Strategy Backtest
@app.get("/api/v1/backtest/{preset_name}", tags=["Quantitative Backtest"])
def get_strategy_backtest(preset_name: str, top_k: int = 10):
    """Run historical backtest (2020-2024) returning CAGR, Alpha, Sharpe, and Drawdown."""
    from src.analytics.backtester import run_strategy_backtest
    try:
        res = run_strategy_backtest(preset_name=preset_name.lower().strip(), top_k=top_k, db_path=DB_PATH)
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# 20. Monte Carlo Probabilistic DCF Valuation
@app.get("/api/v1/valuation/{ticker}/monte-carlo", tags=["Valuation"])
def get_monte_carlo_valuation(ticker: str, simulations: int = 2000):
    """Run 2000+ stochastic Monte Carlo DCF simulations to compute intrinsic value distributions."""
    from src.analytics.monte_carlo_dcf import run_monte_carlo_dcf
    try:
        return run_monte_carlo_dcf(ticker=ticker.strip().upper(), n_simulations=simulations, db_path=DB_PATH)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def export_openapi_json(out_path: str = "docs/openapi.json"):
    """Export auto-generated OpenAPI 3.0 specification."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(app.openapi(), f, indent=2)
    print(f"Exported OpenAPI spec to {out_path}")

if __name__ == "__main__":
    export_openapi_json()
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
