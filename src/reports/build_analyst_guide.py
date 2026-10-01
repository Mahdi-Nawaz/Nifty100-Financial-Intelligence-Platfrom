"""Generate comprehensive 10+ page Analyst Guide PDF (Deliverable D-22 & AC-20)."""
import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

OUTPUT_PDF = "docs/analyst_guide.pdf"

def build_analyst_guide():
    os.makedirs(os.path.dirname(OUTPUT_PDF), exist_ok=True)
    doc = SimpleDocTemplate(
        OUTPUT_PDF,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor('#0F172A'), alignment=1)
    sub_title = ParagraphStyle('DocSubTitle', parent=styles['Normal'], fontSize=11, leading=15, textColor=colors.HexColor('#475569'), alignment=1)
    h1_style = ParagraphStyle('SecH1', parent=styles['Heading1'], fontSize=14, leading=18, textColor=colors.HexColor('#0F172A'), spaceBefore=12, spaceAfter=8)
    h2_style = ParagraphStyle('SecH2', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('BodyText', parent=styles['Normal'], fontSize=9, leading=13, textColor=colors.HexColor('#334155'), spaceAfter=6)
    bullet_style = ParagraphStyle('BulletText', parent=styles['Normal'], fontSize=8.5, leading=12, textColor=colors.HexColor('#1E293B'), leftIndent=15, bulletIndent=5, spaceAfter=3)
    table_cell = ParagraphStyle('TCell', parent=styles['Normal'], fontSize=8, leading=10.5, textColor=colors.HexColor('#1E293B'))

    elements = []

    # ==================== PAGE 1: COVER PAGE ====================
    elements.append(Spacer(1, 120))
    elements.append(Paragraph("<b>NIFTY 100 FINANCIAL INTELLIGENCE PLATFORM</b>", title_style))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph("<b>COMPREHENSIVE ANALYST & SYSTEM USER GUIDE</b>", sub_title))
    elements.append(Paragraph("Production Architecture, Quantitative Engines, Screener Presets & Dashboard Navigation", sub_title))
    elements.append(Spacer(1, 40))
    
    meta_info = [
        [Paragraph("<b>Document Version:</b>", table_cell), Paragraph("1.0 Production Ready", table_cell)],
        [Paragraph("<b>Target Universe:</b>", table_cell), Paragraph("92 Nifty 100 Index Constituents (10-13 Years History)", table_cell)],
        [Paragraph("<b>Computed KPIs:</b>", table_cell), Paragraph("50+ Fundamental, Growth, Cash Flow & Valuation Ratios", table_cell)],
        [Paragraph("<b>Primary Modules:</b>", table_cell), Paragraph("12 Interconnected Modules (ETL, Screener, Scoring, Reports, API, Dashboard)", table_cell)],
        [Paragraph("<b>Data Classification:</b>", table_cell), Paragraph("Confidential — Internal Use Only | Data Analytics Division", table_cell)],
        [Paragraph("<b>Publication Date:</b>", table_cell), Paragraph("June 2026", table_cell)]
    ]
    t_meta = Table(meta_info, colWidths=[150, 350])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    elements.append(t_meta)
    elements.append(Spacer(1, 30))
    if os.path.exists("reports/correlation_heatmap.png"):
        from reportlab.platypus import Image
        elements.append(Image("reports/correlation_heatmap.png", width=360, height=240))
    elements.append(Spacer(1, 30))
    elements.append(Paragraph("<para align='center'><font size=8 color='#64748B'>Bluestock Fintech · Data Analytics Platform Initiative</font></para>", body_style))

    # ==================== PAGE 2: PLATFORM OVERVIEW & ARCHITECTURE ====================
    elements.append(PageBreak())
    elements.append(Paragraph("<b>1. Platform Overview & 7-Layer Architecture</b>", h1_style))
    elements.append(Paragraph("The Nifty 100 Financial Intelligence Platform transforms raw, disparate annual filings and financial statements into high-conviction quantitative signals, institutional tearsheets, and interactive screener workflows. The platform operates on a robust 7-layer data platform architecture designed for determinism, auditability, and speed.", body_style))
    elements.append(Spacer(1, 6))

    arch_rows = [
        [Paragraph("<b>Layer</b>", table_cell), Paragraph("<b>Components</b>", table_cell), Paragraph("<b>Primary Technologies</b>", table_cell)],
        [Paragraph("L1: Ingestion", table_cell), Paragraph("Excel loaders with header=1 detection, ticker validation", table_cell), Paragraph("Python, openpyxl, pandas", table_cell)],
        [Paragraph("L2: Normalisation", table_cell), Paragraph("Fiscal year normaliser (YYYY-MM), deduplication engine", table_cell), Paragraph("src/etl/normaliser.py", table_cell)],
        [Paragraph("L3: Persistent Store", table_cell), Paragraph("SQLite database with 10 tables, relational FKs, index trees", table_cell), Paragraph("SQLite 3.x, data/nifty100.db", table_cell)],
        [Paragraph("L4: Analytics Engine", table_cell), Paragraph("50+ KPIs, CAGR engine, cashflow intelligence, capital patterns", table_cell), Paragraph("NumPy, pandas, scipy.stats", table_cell)],
        [Paragraph("L5: Intelligence Layer", table_cell), Paragraph("0-100 Composite score, 11 peer percentiles, KMeans clusters", table_cell), Paragraph("scikit-learn, rule engine", table_cell)],
        [Paragraph("L6: Reporting Layer", table_cell), Paragraph("92 tearsheets, 11 sector PDFs, portfolio master PDF", table_cell), Paragraph("ReportLab, Matplotlib", table_cell)],
        [Paragraph("L7: Interface & API", table_cell), Paragraph("Interactive 8-screen dashboard, 16 REST endpoints", table_cell), Paragraph("Streamlit, FastAPI, Uvicorn", table_cell)],
    ]
    t_arch = Table(arch_rows, colWidths=[90, 240, 180])
    t_arch.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_arch)
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<b>Core Operating Principles:</b>", h2_style))
    elements.append(Paragraph("• <b>Full Traceability:</b> Every calculated KPI is traceable to a specific mathematical formula and underlying statement row.", bullet_style))
    elements.append(Paragraph("• <b>Graceful Edge-Case Handling:</b> Division by zero, negative shareholder equity, debt-free flags, and turnaround sign inversions are safely handled without data distortion.", bullet_style))
    elements.append(Paragraph("• <b>Zero Data Leakage:</b> Annual metrics are strictly indexed by standardized fiscal year labels (YYYY-MM).", bullet_style))

    # ==================== PAGE 3: DATA WAREHOUSE & SCHEMA ====================
    elements.append(PageBreak())
    elements.append(Paragraph("<b>2. Data Warehouse & Schema Dictionary</b>", h1_style))
    elements.append(Paragraph("The platform aggregates 7 core and 5 supplementary datasets spanning over a decade of audited corporate disclosures. All datasets are unified around the master NSE ticker primary key.", body_style))
    elements.append(Spacer(1, 6))

    ds_rows = [
        [Paragraph("<b>Dataset / Table</b>", table_cell), Paragraph("<b>Type</b>", table_cell), Paragraph("<b>Coverage</b>", table_cell), Paragraph("<b>Key Columns & Purpose</b>", table_cell)],
        [Paragraph("companies", table_cell), Paragraph("Core Master", table_cell), Paragraph("92 constituents", table_cell), Paragraph("Ticker id, legal name, logo URL, business profile, face value", table_cell)],
        [Paragraph("profitandloss", table_cell), Paragraph("Core Time-Series", table_cell), Paragraph("FY 2010–2024", table_cell), Paragraph("Sales, expenses, operating profit, OPM, net profit, EPS", table_cell)],
        [Paragraph("balancesheet", table_cell), Paragraph("Core Time-Series", table_cell), Paragraph("FY 2010–2024", table_cell), Paragraph("Equity capital, reserves, borrowings, total assets/liabilities", table_cell)],
        [Paragraph("cashflow", table_cell), Paragraph("Core Time-Series", table_cell), Paragraph("FY 2010–2024", table_cell), Paragraph("Operating activity (CFO), investing (CFI), financing (CFF)", table_cell)],
        [Paragraph("sectors", table_cell), Paragraph("Supplementary", table_cell), Paragraph("92 companies", table_cell), Paragraph("Broad sector (11 sectors), sub-sector, market cap category", table_cell)],
        [Paragraph("market_cap", table_cell), Paragraph("Supplementary", table_cell), Paragraph("2019–2024", table_cell), Paragraph("Market cap, enterprise value, P/E, P/B, EV/EBITDA, dividend yield", table_cell)],
        [Paragraph("stock_prices", table_cell), Paragraph("Supplementary", table_cell), Paragraph("60 monthly rows", table_cell), Paragraph("Monthly OHLCV price series (Jan 2020–Dec 2024)", table_cell)],
        [Paragraph("peer_groups", table_cell), Paragraph("Supplementary", table_cell), Paragraph("11 peer clusters", table_cell), Paragraph("Peer group name, company ID, benchmark constituent flag", table_cell)],
        [Paragraph("financial_ratios", table_cell), Paragraph("Computed Warehouse", table_cell), Paragraph("1,155 records", table_cell), Paragraph("50+ computed KPIs, 3Y/5Y/10Y CAGRs, composite quality score", table_cell)],
    ]
    t_ds = Table(ds_rows, colWidths=[95, 75, 80, 260])
    t_ds.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_ds)

    # ==================== PAGE 4: FINANCIAL RATIO ENGINE ====================
    elements.append(PageBreak())
    elements.append(Paragraph("<b>3. Financial KPI & Ratio Calculation Reference</b>", h1_style))
    elements.append(Paragraph("The ratio engine evaluates over 50 indicators across 4 key dimensions: Profitability, Solvency, Efficiency, and Cash Flow Quality.", body_style))
    elements.append(Spacer(1, 6))

    kpi_spec = [
        [Paragraph("<b>KPI Category</b>", table_cell), Paragraph("<b>Metric & Formula</b>", table_cell), Paragraph("<b>Institutional Benchmark</b>", table_cell), Paragraph("<b>Edge-Case Handling</b>", table_cell)],
        [Paragraph("Profitability", table_cell), Paragraph("<b>ROE:</b> Net Profit / (Equity + Reserves) × 100", table_cell), Paragraph(">15% Good, >20% Exceptional", table_cell), Paragraph("Returns None if total equity <= 0", table_cell)],
        [Paragraph("Profitability", table_cell), Paragraph("<b>OPM:</b> Operating Profit / Sales × 100", table_cell), Paragraph(">15% Stable, >25% Strong Moat", table_cell), Paragraph("Cross-checked against reported OPM ±1%", table_cell)],
        [Paragraph("Profitability", table_cell), Paragraph("<b>ROCE:</b> EBIT / Capital Employed × 100", table_cell), Paragraph(">15% Preferred", table_cell), Paragraph("Sector-relative treatment for Banks/NBFCs", table_cell)],
        [Paragraph("Solvency", table_cell), Paragraph("<b>D/E:</b> Borrowings / Equity", table_cell), Paragraph("<1.0 Safe, <0.5 Conservative", table_cell), Paragraph("Zero debt yields exactly 0.0x", table_cell)],
        [Paragraph("Solvency", table_cell), Paragraph("<b>ICR:</b> (OP + Other Income) / Interest", table_cell), Paragraph(">3.0x Safe, >5.0x Outstanding", table_cell), Paragraph("Interest=0 flags 999.0 ('Debt Free')", table_cell)],
        [Paragraph("Cash Flow", table_cell), Paragraph("<b>FCF:</b> CFO + CFI", table_cell), Paragraph(">0 Cash Generation", table_cell), Paragraph("Negative allowed; 3-yr run flags risk", table_cell)],
        [Paragraph("Cash Quality", table_cell), Paragraph("<b>CFO/PAT:</b> Operating Cash / Net Profit", table_cell), Paragraph(">1.0 High Quality, <0.5 Accrual Risk", table_cell), Paragraph("Identifies aggressive revenue recognition", table_cell)],
        [Paragraph("Efficiency", table_cell), Paragraph("<b>Asset Turnover:</b> Sales / Total Assets", table_cell), Paragraph(">1.0x Normal, >2.0x Asset Light", table_cell), Paragraph("None if total assets = 0", table_cell)],
    ]
    t_kpi = Table(kpi_spec, colWidths=[80, 180, 110, 140])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_kpi)

    # ==================== PAGE 5: INVESTMENT SCREENER ====================
    elements.append(PageBreak())
    elements.append(Paragraph("<b>4. Multi-Parameter Screener & 6 Preset Screens</b>", h1_style))
    elements.append(Paragraph("The screener engine combines 18 configurable criteria to isolate investment candidates. Presets are loaded from <code>config/screener_config.yaml</code>.", body_style))
    elements.append(Spacer(1, 6))

    sc_rows = [
        [Paragraph("<b>Preset Name</b>", table_cell), Paragraph("<b>Filter Logic</b>", table_cell), Paragraph("<b>Primary Rank Metric</b>", table_cell), Paragraph("<b>Target Universe</b>", table_cell)],
        [Paragraph("<b>Quality Compounder</b>", table_cell), Paragraph("ROE > 15%, D/E < 1.0, FCF > 0, 5Y Rev CAGR > 10%", table_cell), Paragraph("Composite Health Score", table_cell), Paragraph("Elite franchise compounders (15–35 cos)", table_cell)],
        [Paragraph("<b>Value Pick</b>", table_cell), Paragraph("P/E < 20, P/B < 3.0, D/E < 2.0, Div Yield > 1%", table_cell), Paragraph("FCF Yield", table_cell), Paragraph("Undervalued cash generators (10–25 cos)", table_cell)],
        [Paragraph("<b>Growth Accelerator</b>", table_cell), Paragraph("5Y PAT CAGR > 20%, 5Y Rev CAGR > 15%, D/E < 2.0", table_cell), Paragraph("5Y PAT CAGR", table_cell), Paragraph("High velocity growth businesses (8–20 cos)", table_cell)],
        [Paragraph("<b>Dividend Champion</b>", table_cell), Paragraph("Div Yield > 2%, Payout < 80%, FCF > 0", table_cell), Paragraph("Dividend Yield", table_cell), Paragraph("Sustainable high-yield income (10–20 cos)", table_cell)],
        [Paragraph("<b>Debt-Free Blue Chip</b>", table_cell), Paragraph("D/E = 0, ROE > 12%, Revenue > ₹5,000 Cr", table_cell), Paragraph("ROE %", table_cell), Paragraph("Pristine zero-debt balance sheets (15–30 cos)", table_cell)],
        [Paragraph("<b>Turnaround Watch</b>", table_cell), Paragraph("3Y Rev CAGR > 10%, FCF positive, D/E improving", table_cell), Paragraph("3Y Revenue CAGR", table_cell), Paragraph("Operational turnaround candidates (5–15 cos)", table_cell)],
    ]
    t_sc = Table(sc_rows, colWidths=[110, 190, 110, 100])
    t_sc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_sc)
    elements.append(Spacer(1, 8))
    elements.append(Paragraph("<b>Financial Sector Carve-Out Rule:</b>", h2_style))
    elements.append(Paragraph("Per Risk Mitigation Rule R-04, companies classified under 'Financials' (Commercial Banks, NBFCs) are exempt from non-financial D/E screening ceilings. Their leverage is evaluated through sector-normalized return on assets and regulatory tier equity.", body_style))

    # ==================== PAGE 6: FINANCIAL HEALTH SCORING MODEL ====================
    elements.append(PageBreak())
    elements.append(Paragraph("<b>5. Financial Health Scoring Model (0–100)</b>", h1_style))
    elements.append(Paragraph("The platform uses an institutional composite scoring framework that weights fundamental quality across 4 balanced dimensions.", body_style))
    elements.append(Spacer(1, 6))

    score_rows = [
        [Paragraph("<b>Dimension</b>", table_cell), Paragraph("<b>Weight</b>", table_cell), Paragraph("<b>Sub-Metrics</b>", table_cell), Paragraph("<b>Normalisation & Scoring Logic</b>", table_cell)],
        [Paragraph("Profitability", table_cell), Paragraph("35%", table_cell), Paragraph("ROE (15%), OPM (10%), NPM (10%)", table_cell), Paragraph("Winsorised P10–P90, scaled 0–100 percentile rank", table_cell)],
        [Paragraph("Cash Quality", table_cell), Paragraph("30%", table_cell), Paragraph("5Y FCF CAGR (15%), CFO/PAT (10%), FCF > 0 (5%)", table_cell), Paragraph("Scaled cash generation; FCF > 0 awards 100 pts", table_cell)],
        [Paragraph("Growth", table_cell), Paragraph("20%", table_cell), Paragraph("5Y Revenue CAGR (10%), 5Y PAT CAGR (10%)", table_cell), Paragraph("Penalises negative base turnaround anomalies", table_cell)],
        [Paragraph("Leverage", table_cell), Paragraph("15%", table_cell), Paragraph("D/E Score (10%), ICR Score (5%)", table_cell), Paragraph("D/E: 0=100, 0.5=85, 1.0=70, 2.0=50. ICR: >10=100, >5=75", table_cell)],
    ]
    t_sc_mod = Table(score_rows, colWidths=[90, 50, 160, 210])
    t_sc_mod.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_sc_mod)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Composite Score Rating Tiers:</b>", h2_style))
    tier_rows = [
        [Paragraph("<b>Score Range</b>", table_cell), Paragraph("<b>Tier Label</b>", table_cell), Paragraph("<b>Colour Theme</b>", table_cell), Paragraph("<b>Investment Interpretation</b>", table_cell)],
        [Paragraph("80 – 100", table_cell), Paragraph("Excellent", table_cell), Paragraph("Green (#2E7D32)", table_cell), Paragraph("Market leading balance sheet, elite cash flows, low default risk", table_cell)],
        [Paragraph("65 – 79", table_cell), Paragraph("Good", table_cell), Paragraph("Teal (#0288D1)", table_cell), Paragraph("Solid fundamentals with sustainable growth and manageable leverage", table_cell)],
        [Paragraph("50 – 64", table_cell), Paragraph("Average", table_cell), Paragraph("Yellow (#FBC02D)", table_cell), Paragraph("Benchmark performance; mixed capital efficiency or moderate debt", table_cell)],
        [Paragraph("35 – 49", table_cell), Paragraph("Weak", table_cell), Paragraph("Orange (#FB8C00)", table_cell), Paragraph("Stressed cash generation or high leverage requiring active monitoring", table_cell)],
        [Paragraph("0 – 34", table_cell), Paragraph("Poor", table_cell), Paragraph("Red (#D32F2F)", table_cell), Paragraph("Severe operational deficits or structural financial impairment", table_cell)],
    ]
    t_tier = Table(tier_rows, colWidths=[80, 80, 110, 240])
    t_tier.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_tier)

    # ==================== PAGE 7: PEER COMPARISON & RADAR CHARTS ====================
    elements.append(PageBreak())
    elements.append(Paragraph("<b>6. Peer Comparison & Radar Analytics</b>", h1_style))
    elements.append(Paragraph("The peer engine categorizes companies into 11 distinct industry peer clusters. It computes within-group percentile rankings for 20 metrics and generates individual radar chart profiles.", body_style))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("<b>11 Dedicated Peer Groups:</b>", h2_style))
    elements.append(Paragraph("1. <b>Private Banks:</b> HDFCBANK, ICICIBANK, AXISBANK, KOTAKBANK, INDUSINDBK", bullet_style))
    elements.append(Paragraph("2. <b>Public Sector Banks:</b> SBIN, BANKBARODA, CANBK, PNB", bullet_style))
    elements.append(Paragraph("3. <b>IT Services:</b> TCS, INFY, HCLTECH, TECHM, LTIM", bullet_style))
    elements.append(Paragraph("4. <b>Pharmaceuticals:</b> SUNPHARMA, CIPLA, DRREDDY, DIVISLAB, TORNTPHARM", bullet_style))
    elements.append(Paragraph("5. <b>Automobiles:</b> MARUTI, TATAMOTORS, M&M, BAJAJ-AUTO, EICHERMOT, HEROMOTOCO, TVSMOTOR", bullet_style))
    elements.append(Paragraph("6. <b>Life Insurance:</b> LICI, HDFCLIFE, SBILIFE, ICICIPRULI", bullet_style))
    elements.append(Paragraph("7. <b>Oil & Gas:</b> RELIANCE, ONGC, BPCL, IOC, GAIL", bullet_style))
    elements.append(Paragraph("8. <b>Power & Utilities:</b> NTPC, POWERGRID, TATAPOWER, ADANIPOWER, NHPC, JSWENERGY, ADANIGREEN", bullet_style))
    elements.append(Paragraph("9. <b>Steel & Metals:</b> TATASTEEL, JSWSTEEL, JINDALSTEL, HINDALCO", bullet_style))
    elements.append(Paragraph("10. <b>FMCG:</b> HINDUNILVR, ITC, BRITANNIA, DABUR, NESTLEIND, GODREJCP, TATACONSUM", bullet_style))
    elements.append(Paragraph("11. <b>Consumer Finance:</b> BAJFINANCE, CHOLAFIN, SHRIRAMFIN", bullet_style))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Radar Chart Interpretation:</b>", h2_style))
    elements.append(Paragraph("Each radar chart visualizes a constituent's profile across 8 axes: ROE, OPM, NPM, 5Y Revenue CAGR, 5Y PAT CAGR, CFO/PAT Quality, FCF, and Composite Quality. The blue shaded polygon reflects company performance, while the orange dashed line shows the peer group average.", body_style))

    # ==================== PAGE 8: CAPITAL ALLOCATION MATRIX ====================
    elements.append(PageBreak())
    elements.append(Paragraph("<b>7. Cash Flow Intelligence & Capital Allocation Archetypes</b>", h1_style))
    elements.append(Paragraph("Every company-year cash flow profile is classified into one of 8 capital allocation archetypes based on the mathematical sign of Operating Cash (CFO), Investing Cash (CFI), and Financing Cash (CFF).", body_style))
    elements.append(Spacer(1, 6))

    cap_table = [
        [Paragraph("<b>Archetype Label</b>", table_cell), Paragraph("<b>CFO</b>", table_cell), Paragraph("<b>CFI</b>", table_cell), Paragraph("<b>CFF</b>", table_cell), Paragraph("<b>Strategic Interpretation & Health Implication</b>", table_cell)],
        [Paragraph("Reinvestor & Shareholder Returns", table_cell), Paragraph("+", table_cell), Paragraph("−", table_cell), Paragraph("−", table_cell), Paragraph("Ideal profile: Strong operating cash funding CapEx and paying dividends/debt", table_cell)],
        [Paragraph("Growth via External Capital", table_cell), Paragraph("+", table_cell), Paragraph("−", table_cell), Paragraph("+", table_cell), Paragraph("Aggressive capacity expansion funded by both internal cash and external debt/equity", table_cell)],
        [Paragraph("Divestment & Debt Repayment", table_cell), Paragraph("+", table_cell), Paragraph("+", table_cell), Paragraph("−", table_cell), Paragraph("Core operations positive; asset sales used to de-lever the balance sheet", table_cell)],
        [Paragraph("Cash Hoarding", table_cell), Paragraph("+", table_cell), Paragraph("+", table_cell), Paragraph("+", table_cell), Paragraph("Accumulating liquid reserves across all channels; potential M&A war-chest", table_cell)],
        [Paragraph("Distress / External Funding", table_cell), Paragraph("−", table_cell), Paragraph("−", table_cell), Paragraph("+", table_cell), Paragraph("Red flag: Operations burning cash while CapEx and deficits are funded by debt raises", table_cell)],
        [Paragraph("Rapid Cash Burn", table_cell), Paragraph("−", table_cell), Paragraph("−", table_cell), Paragraph("−", table_cell), Paragraph("Severe liquidity depletion: operating deficit, CapEx outlays, and net cash outflow", table_cell)],
        [Paragraph("Asset Sale & Debt Funding", table_cell), Paragraph("−", table_cell), Paragraph("+", table_cell), Paragraph("+", table_cell), Paragraph("Emergency liquidity triage: selling fixed assets and raising loans to support operations", table_cell)],
        [Paragraph("Restructuring & Contraction", table_cell), Paragraph("−", table_cell), Paragraph("+", table_cell), Paragraph("−", table_cell), Paragraph("Downsizing operations and liquidating investments while repaying senior lenders", table_cell)],
    ]
    t_cap = Table(cap_table, colWidths=[140, 30, 30, 30, 280])
    t_cap.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('ALIGN', (1, 0), (3, -1), 'CENTER'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_cap)

    # ==================== PAGE 9: STREAMLIT DASHBOARD GUIDE ====================
    elements.append(PageBreak())
    elements.append(Paragraph("<b>8. Streamlit Dashboard Navigation Guide</b>", h1_style))
    elements.append(Paragraph("The platform features an analyst dashboard accessible locally via <code>streamlit run src/dashboard/app.py</code>. The application is organized across 8 dedicated modules.", body_style))
    elements.append(Spacer(1, 6))

    dash_screens = [
        [Paragraph("<b>Screen / Page</b>", table_cell), Paragraph("<b>Key Visualizations & Analytics</b>", table_cell), Paragraph("<b>User Controls & Export Options</b>", table_cell)],
        [Paragraph("01 Home / Overview", table_cell), Paragraph("Nifty 100 index summary KPIs, sector market cap donut, health band distributions", table_cell), Paragraph("Sector filter chips, year selection dropdown", table_cell)],
        [Paragraph("02 Company Profile", table_cell), Paragraph("Company header card, 6 KPI tiles, 10Y Revenue/PAT bar charts, Balance Sheet breakdown, CF waterfall", table_cell), Paragraph("Ticker search autocomplete, year range slider, PDF tearsheet download", table_cell)],
        [Paragraph("03 Screener", table_cell), Paragraph("Interactive table with 18 filterable metrics, live match counter, composite score ranking", table_cell), Paragraph("Preset selector (6 screens), sidebar numeric sliders, CSV & Excel export buttons", table_cell)],
        [Paragraph("04 Peer Comparison", table_cell), Paragraph("Interactive Plotly radar chart, side-by-side comparison table, benchmark delta heatmap", table_cell), Paragraph("Peer group dropdown, metric axis toggle, PNG chart save", table_cell)],
        [Paragraph("05 Trend Analysis", table_cell), Paragraph("10-year historical sparklines, YoY percentage change annotations, multi-metric overlay", table_cell), Paragraph("Company search, multi-metric selector, CSV series export", table_cell)],
        [Paragraph("06 Sector Analysis", table_cell), Paragraph("Sector bubble chart (Sales vs ROE, bubble size = Mkt Cap), sector median KPI comparison", table_cell), Paragraph("Sector selector, bubble axis parameters, PNG export", table_cell)],
        [Paragraph("07 Capital Map", table_cell), Paragraph("Treemap of 92 companies partitioned into the 8 capital allocation archetypes", table_cell), Paragraph("Year slider, click-to-drill company list", table_cell)],
        [Paragraph("08 Annual Reports", table_cell), Paragraph("BSE India primary filing repository table with status flags and download links", table_cell), Paragraph("Ticker search, filing year filter, direct BSE URL links", table_cell)],
    ]
    t_dash = Table(dash_screens, colWidths=[110, 240, 160])
    t_dash.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_dash)

    # ==================== PAGE 10: REST API & TESTING ====================
    elements.append(PageBreak())
    elements.append(Paragraph("<b>9. REST API Integration & Data Quality Rules</b>", h1_style))
    elements.append(Paragraph("A FastAPI server exposes 16 production endpoints for programmatic integration. Start the API using <code>uvicorn src.api.main:app --port 8000</code>. Interactive OpenAPI documentation is available at <code>http://localhost:8000/docs</code>.", body_style))
    elements.append(Spacer(1, 6))

    api_endpoints = [
        [Paragraph("<b>Endpoint Route</b>", table_cell), Paragraph("<b>Method</b>", table_cell), Paragraph("<b>Parameters</b>", table_cell), Paragraph("<b>Description & Response Payload</b>", table_cell)],
        [Paragraph("/api/v1/health", table_cell), Paragraph("GET", table_cell), Paragraph("None", table_cell), Paragraph("Health check returning SQLite row counts and uptime", table_cell)],
        [Paragraph("/api/v1/companies", table_cell), Paragraph("GET", table_cell), Paragraph("sector, search", table_cell), Paragraph("Constituent company list with base metadata", table_cell)],
        [Paragraph("/api/v1/companies/{ticker}", table_cell), Paragraph("GET", table_cell), Paragraph("ticker", table_cell), Paragraph("Comprehensive company profile with latest KPIs and pros/cons", table_cell)],
        [Paragraph("/api/v1/companies/{ticker}/ratios", table_cell), Paragraph("GET", table_cell), Paragraph("ticker, year", table_cell), Paragraph("Full time series of 50+ computed financial ratios", table_cell)],
        [Paragraph("/api/v1/companies/{ticker}/tearsheet", table_cell), Paragraph("GET", table_cell), Paragraph("ticker", table_cell), Paragraph("Streams pre-generated 2-page institutional tearsheet PDF", table_cell)],
        [Paragraph("/api/v1/screener", table_cell), Paragraph("GET", table_cell), Paragraph("min_roe, max_de, sector", table_cell), Paragraph("Returns ranked list of matching companies with composite score", table_cell)],
        [Paragraph("/api/v1/sectors", table_cell), Paragraph("GET", table_cell), Paragraph("None", table_cell), Paragraph("Sector medians for ROE, P/E, D/E and total market cap", table_cell)],
        [Paragraph("/api/v1/portfolio/stats", table_cell), Paragraph("GET", table_cell), Paragraph("None", table_cell), Paragraph("P10 to P90 portfolio distribution benchmarks across all KPIs", table_cell)],
    ]
    t_api = Table(api_endpoints, colWidths=[140, 45, 120, 205])
    t_api.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_api)
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Data Quality (DQ) Enforcement:</b>", h2_style))
    elements.append(Paragraph("16 programmatic validation rules ensure data warehouse integrity on every ETL run. Zero critical violations are permitted for production sign-off. All anomalies are permanently logged to <code>output/validation_failures.csv</code>.", body_style))

    doc.build(elements)
    print(f"Generated 10-page Analyst Guide PDF at {OUTPUT_PDF}")
    return OUTPUT_PDF

if __name__ == "__main__":
    build_analyst_guide()
