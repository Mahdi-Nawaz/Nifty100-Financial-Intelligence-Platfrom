# Nifty 100 Financial Intelligence Platform 📈

[![CI Test Suite & Quality Gates](https://github.com/Mahdi-Nawaz/Nifty100-Financial-Intelligence-Platfrom/actions/workflows/ci.yml/badge.svg)](https://github.com/Mahdi-Nawaz/Nifty100-Financial-Intelligence-Platfrom/actions)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An institutional-grade quantitative fundamental analytics, forensic accounting triage, and investment intelligence platform covering **92 constituent companies** of the National Stock Exchange (NSE) Nifty 100 Index across 10 historical fiscal years (FY14–FY24).

---

## 🌟 Key Platform Capabilities

1. **Automated ETL & Data Quality Pipeline**:
   - Ingests audited Profit & Loss, Balance Sheet, Cash Flow, and Valuation datasets from Excel sources.
   - Enforces **14 Data Quality (DQ) integrity rules** (OPM cross-check, balance sheet balancing, EPS sign consistency, foreign key validation).
   - Generates SQLite database with foreign keys, indexes, and Write-Ahead Logging (WAL) concurrency.

2. **Institutional Financial Ratio Engine (50+ KPIs)**:
   - **Profitability**: ROE, ROCE, ROA, Net Profit Margin (NPM), Operating Profit Margin (OPM).
   - **Solvency & Liquidity**: Debt-to-Equity (D/E), Interest Coverage Ratio (ICR), Net Debt / EBITDA.
   - **Cash Quality**: Free Cash Flow (FCF), CFO/PAT ratio, Capex Intensity, Capital Allocation Trajectory classification.
   - **Growth & Momentum**: 3-Year, 5-Year, and 10-Year CAGRs with turnaround/loss handling.
   - **Composite Score**: 0–100 percentile-ranked financial health score.

3. **Forensic Accounting & Corporate Governance Suite**:
   - **Beneish M-Score**: 8-variable model detecting potential earnings manipulation with non-financial sector filtering.
   - **Altman Z''-Score**: Emerging-market variant classifying companies into Safe, Grey, and Distress insolvency zones.
   - **Piotroski F-Score**: 9-signal fundamental momentum scoring (0 to 9).

4. **Probabilistic Monte Carlo DCF Valuation Engine**:
   - Vectorized NumPy stochastic simulation executing **5,000 runs per company**.
   - Evaluates stochastic revenue growth, operating profit margins, triangular WACC, and terminal growth distributions.
   - Generates P10 Bear, P50 Base, and P90 Bull intrinsic values alongside Margin of Safety and Undervaluation Probability.

5. **Quantitative Strategy Backtester**:
   - Historical multi-factor simulation (2020–2024) across 5 investment presets (*Quality Compounder*, *Value Pick*, *Growth Accelerator*, *Dividend Champion*, *Debt-Free Blue Chip*).
   - Calculates Annual Strategy CAGR, Benchmark CAGR, Alpha ($\alpha$), Beta ($\beta$), Sharpe Ratio, Sortino Ratio, and Max Drawdown (MDD).

6. **Unsupervised ML Anomaly Detection**:
   - Multivariate **Isolation Forest** and **3D Principal Component Analysis (PCA)** to uncover statistical accounting outliers.

7. **AI Financial Research Copilot**:
   - Natural language query assistant for financial ratio triage, peer comparisons, and forensic health lookups.

8. **Multi-Channel Delivery Surface**:
   - **Streamlit Interactive Dashboard**: 13 rich analytical screens with Plotly visualisations and dark-themed KPI cards.
   - **FastAPI REST Service**: 20 production endpoints with interactive Swagger UI and OpenAPI 3.0 export.
   - **ReportLab PDF Generator**: Automated generation of 104+ company tearsheets and analyst guides.

---

## 📂 Project Architecture & Directory Layout

```
Nifty100_Financial_Intelligence/
├── .github/workflows/ci.yml       # GitHub Actions CI workflow (101 automated tests)
├── .dockerignore                  # Build context exclusion rules
├── .gitignore                     # Git tracking exclusions
├── Dockerfile                     # Multi-stage production container build
├── docker-compose.yml             # Dual-service orchestrator (FastAPI :8000 + Streamlit :8501)
├── Makefile                       # Developer shortcuts (load, test, dashboard, api)
├── requirements.txt               # Pinned Python package dependencies
├── streamlit_app.py               # Root deployment entrypoint for Streamlit Community Cloud
│
├── config/
│   ├── .env.template              # Environment variable template
│   ├── logging_config.yaml        # Structured logging configuration
│   └── screener_config.yaml       # Screener filter presets & weightings
│
├── data/
│   ├── nifty100.db                # SQLite database with WAL mode and indexes
│   ├── raw/                       # Clean source Excel statements (P&L, BS, CF, etc.)
│   └── supporting/                # Supporting datasets (sectors, market cap, stock prices)
│
├── docs/
│   ├── openapi.json               # Auto-generated OpenAPI 3.0 specification
│   ├── analyst_guide.pdf          # Analyst User Guide
│   └── acceptance_checklist.pdf   # Platform Acceptance Verification Checklist
│
├── src/
│   ├── analytics/                 # Quantitative models & analytics engines
│   │   ├── backtester.py          # Strategy backtester & risk engine
│   │   ├── cagr.py                # CAGR calculation with edge-case handling
│   │   ├── cashflow_kpis.py       # Capital allocation pattern classifier
│   │   ├── forensics.py           # Beneish M, Altman Z, Piotroski F scores
│   │   ├── ml_anomaly.py          # Isolation Forest & PCA anomaly detector
│   │   ├── monte_carlo_dcf.py     # 5,000-iteration stochastic DCF model
│   │   ├── peer.py                # Peer percentile ranking engine
│   │   ├── ratios.py              # 50+ KPI computation & composite scoring
│   │   ├── valuation.py           # Historical valuation multiples
│   │   └── screener/engine.py     # Multi-parameter screener filter engine
│   │
│   ├── api/
│   │   └── main.py                # FastAPI REST server (20 endpoints)
│   │
│   ├── dashboard/                 # Streamlit Web Application
│   │   ├── app.py                 # Main dashboard landing page & KPI summary
│   │   ├── pages/                 # 12 specialized analytical screens
│   │   │   ├── 02_Company_Profile.py
│   │   │   ├── 03_Financial_Screener.py
│   │   │   ├── 04_Peer_Comparison.py
│   │   │   ├── 05_Trend_Analysis.py
│   │   │   ├── 06_Sector_Analytics.py
│   │   │   ├── 07_Capital_Allocation.py
│   │   │   ├── 08_Annual_Reports.py
│   │   │   ├── 09_Forensic_Audit.py
│   │   │   ├── 10_Strategy_Backtester.py
│   │   │   ├── 11_Monte_Carlo_Valuation.py
│   │   │   ├── 12_ML_Anomaly_Detection.py
│   │   │   └── 13_AI_Financial_Copilot.py
│   │   └── utils/
│   │       ├── charts.py          # Reusable Plotly chart generators
│   │       └── db.py              # Cached SQLite database accessors
│   │
│   ├── etl/                       # Data pipeline & quality assurance
│   │   ├── loader.py              # ETL orchestrator
│   │   ├── normaliser.py          # Ticker & year standardization
│   │   ├── schema.sql             # Relational schema DDL & indexes
│   │   └── validator.py           # 14-rule Data Quality validator
│   │
│   ├── nlp/                       # NLP & Copilot engines
│   │   ├── copilot_engine.py      # Natural language financial search
│   │   └── pros_cons_generator.py # Rule-based strengths/weaknesses synthesis
│   │
│   └── reports/                   # Automated PDF reporting engine (ReportLab)
│       ├── tearsheet.py           # 2-page institutional company tearsheets
│       ├── sector_report.py       # Sector overview reports
│       └── portfolio_report.py    # Portfolio summary report
│
└── tests/                         # Complete 101-test validation suite
    ├── api/                       # API integration test suite
    ├── dq/                        # Data Quality rule tests
    ├── etl/                       # Normalization & deduplication tests
    └── kpi/                       # Financial formula & model unit tests
```

---

## 🚀 Deployment Guide

### Option 1: Deploy to Streamlit Community Cloud (Recommended)

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Deploy Nifty 100 Financial Intelligence Platform"
   git push origin master
   ```

2. **Connect Streamlit Community Cloud**:
   - Navigate to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
   - Click **New app**.
   - Select your repository: `Mahdi-Nawaz/Nifty100-Financial-Intelligence-Platfrom`
   - Select Branch: `master`
   - Set **Main file path** to:
     ```text
     src/dashboard/app.py
     ```
     *(Alternatively, `streamlit_app.py` in the root also points directly to the dashboard).*
   - Expand **Advanced settings** (optional): select Python `3.10`.
   - Click **Deploy!**

---

### Option 2: Run Locally (Windows / macOS / Linux)

#### 1. Clone the repository & set up environment
```bash
git clone https://github.com/Mahdi-Nawaz/Nifty100-Financial-Intelligence-Platfrom.git
cd Nifty100-Financial-Intelligence-Platfrom

python -m venv .venv
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS / Linux:
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Launch the Streamlit Dashboard
```bash
streamlit run src/dashboard/app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

#### 3. Launch the FastAPI REST Server
```bash
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger API documentation: [http://localhost:8000/docs](http://localhost:8000/docs)  
Alternative ReDoc documentation: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

### Option 3: Run with Docker & Docker Compose

Run both the REST API and Streamlit Dashboard simultaneously in isolated containers:
```bash
docker-compose up --build
```
- Streamlit Dashboard: [http://localhost:8501](http://localhost:8501)
- FastAPI Service: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing & Verification

The platform includes a test suite of **101 tests** covering Data Quality rules, normalization, ratio computations, forensic algorithms, Monte Carlo DCF simulations, backtesting, and API endpoints.

Run the test suite:
```bash
pytest tests/ -v
```

Generate a self-contained HTML test report:
```bash
pytest tests/ --html=reports/pytest_report.html --self-contained-html
```

---

## 📡 REST API Summary (20 Endpoints)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/health` | System health, uptime, and database row counts |
| `GET` | `/api/v1/companies` | List all 92 companies with sector filter and text search |
| `GET` | `/api/v1/companies/{ticker}` | Comprehensive company profile and latest fundamentals |
| `GET` | `/api/v1/companies/{ticker}/pl` | 10-year Profit & Loss historical statements |
| `GET` | `/api/v1/companies/{ticker}/bs` | 10-year Balance Sheet historical statements |
| `GET` | `/api/v1/companies/{ticker}/cashflow` | 10-year Cash Flow historical statements |
| `GET` | `/api/v1/companies/{ticker}/ratios` | 50+ computed KPIs and financial ratios per year |
| `GET` | `/api/v1/companies/{ticker}/tearsheet` | Download pre-generated 2-page company tearsheet PDF |
| `GET` | `/api/v1/screener` | Multi-parameter fundamental screener (ROE, D/E, FCF, etc.) |
| `GET` | `/api/v1/sectors` | Sector aggregates (median ROE, median P/E, total market cap) |
| `GET` | `/api/v1/sectors/{sector}/companies` | All companies within a given sector |
| `GET` | `/api/v1/peers/{group_name}` | Peer group constituents and percentile ranks |
| `GET` | `/api/v1/companies/{ticker}/peers/compare` | Radar comparison data vs sector medians |
| `GET` | `/api/v1/market-cap/{ticker}` | Historical valuation multiples (P/E, P/B, EV/EBITDA) |
| `GET` | `/api/v1/portfolio/stats` | Portfolio-level distributions (P10 to P90) |
| `GET` | `/api/v1/companies/{ticker}/documents` | Company annual report links |
| `GET` | `/api/v1/forensics/summary` | Universe-wide forensic audit triage leaderboard |
| `GET` | `/api/v1/forensics/{ticker}` | Beneish M, Altman Z'', and Piotroski F scores |
| `GET` | `/api/v1/backtest/{preset_name}` | 5-year quantitative strategy backtest simulation |
| `GET` | `/api/v1/valuation/{ticker}/monte-carlo` | Stochastic Monte Carlo DCF intrinsic value distribution |

---

## ⚖️ License & Attribution

This project is licensed under the MIT License. Developed for quantitative financial analysis and academic research on the NSE Nifty 100 universe.
