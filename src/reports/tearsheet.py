"""Automated Company Tearsheet Generator producing 2-page PDF reports via ReportLab."""
import os
import sys
import io
import datetime
import sqlite3
from typing import Tuple, List, Any, Dict
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

sys.path.insert(0, os.path.abspath("."))
from src.analytics.screener.engine import get_latest_screener_universe

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "reports/tearsheets"
SCRATCH_IMG_DIR = "reports/scratch_charts"

def create_company_charts(ticker: str, pl_df: pd.DataFrame, bs_df: pd.DataFrame, cf_df: pd.DataFrame, ratios_df: pd.DataFrame) -> Tuple[str, str]:
    """Generate financial charts and return filepaths for embedding in PDF."""
    os.makedirs(SCRATCH_IMG_DIR, exist_ok=True)
    p1_path = os.path.join(SCRATCH_IMG_DIR, f"{ticker}_p1.png")
    p2_path = os.path.join(SCRATCH_IMG_DIR, f"{ticker}_p2.png")

    # Chart 1: Revenue & Profit Trend
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.5, 3.2))
    
    # Revenue & Net Profit
    yrs = [y[-5:] for y in pl_df['year'].tolist()[-8:]]
    revs = pl_df['sales'].tolist()[-8:]
    pats = pl_df['net_profit'].tolist()[-8:]
    
    x = np.arange(len(yrs))
    width = 0.35
    ax1.bar(x - width/2, revs, width, label='Revenue', color='#1E88E5')
    ax1.bar(x + width/2, pats, width, label='Net Profit', color='#43A047')
    ax1.set_xticks(x)
    ax1.set_xticklabels(yrs, rotation=45, fontsize=8)
    ax1.set_title('Revenue & PAT (₹ Cr)', fontsize=10, fontweight='bold')
    ax1.legend(fontsize=7)
    ax1.grid(True, linestyle=':', alpha=0.6)

    # ROE Trend
    r_yrs = [y[-5:] for y in ratios_df['year'].tolist()[-8:]]
    roes = ratios_df['return_on_equity_pct'].tolist()[-8:]
    ax2.plot(r_yrs, roes, marker='o', color='#E53935', linewidth=2, label='ROE %')
    ax2.set_xticks(range(len(r_yrs)))
    ax2.set_xticklabels(r_yrs, rotation=45, fontsize=8)
    ax2.set_title('Return on Equity (%)', fontsize=10, fontweight='bold')
    ax2.axhline(15, color='gray', linestyle='--', label='15% Hurdle')
    ax2.legend(fontsize=7)
    ax2.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig(p1_path, dpi=160)
    plt.close(fig)

    # Chart 2: Cash Flow & Balance Sheet Assets
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(8.5, 3.2))
    
    cf_yrs = [y[-5:] for y in cf_df['year'].tolist()[-7:]]
    cfos = cf_df['operating_activity'].tolist()[-7:]
    cfis = cf_df['investing_activity'].tolist()[-7:]
    cffs = cf_df['financing_activity'].tolist()[-7:]

    cx = np.arange(len(cf_yrs))
    c_w = 0.25
    ax3.bar(cx - c_w, cfos, c_w, label='CFO', color='#2E7D32')
    ax3.bar(cx, cfis, c_w, label='CFI', color='#D81B60')
    ax3.bar(cx + c_w, cffs, c_w, label='CFF', color='#FB8C00')
    ax3.set_xticks(cx)
    ax3.set_xticklabels(cf_yrs, rotation=45, fontsize=8)
    ax3.set_title('Cash Flow Profile (₹ Cr)', fontsize=10, fontweight='bold')
    ax3.legend(fontsize=7)
    ax3.grid(True, linestyle=':', alpha=0.6)

    # Balance Sheet Assets
    bs_yrs = [y[-5:] for y in bs_df['year'].tolist()[-7:]]
    tot_a = bs_df['total_assets'].tolist()[-7:]
    borr = bs_df['borrowings'].tolist()[-7:]
    ax4.plot(bs_yrs, tot_a, marker='s', color='#1565C0', linewidth=2, label='Total Assets')
    ax4.plot(bs_yrs, borr, marker='^', color='#C62828', linewidth=1.5, linestyle='--', label='Borrowings')
    ax4.set_xticks(range(len(bs_yrs)))
    ax4.set_xticklabels(bs_yrs, rotation=45, fontsize=8)
    ax4.set_title('Asset Base & Debt (₹ Cr)', fontsize=10, fontweight='bold')
    ax4.legend(fontsize=7)
    ax4.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.savefig(p2_path, dpi=160)
    plt.close(fig2)

    return p1_path, p2_path

def generate_tearsheet(ticker: str, conn: sqlite3.Connection, universe_row: pd.Series, pros: List[str], cons: List[str]) -> str:
    """Generate a single 2-page company tearsheet PDF."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_pdf = os.path.join(OUTPUT_DIR, f"{ticker}_tearsheet.pdf")

    # Fetch data
    pl_df = pd.read_sql_query(f"SELECT * FROM profitandloss WHERE company_id = '{ticker}' ORDER BY year", conn)
    bs_df = pd.read_sql_query(f"SELECT * FROM balancesheet WHERE company_id = '{ticker}' ORDER BY year", conn)
    cf_df = pd.read_sql_query(f"SELECT * FROM cashflow WHERE company_id = '{ticker}' ORDER BY year", conn)
    r_df = pd.read_sql_query(f"SELECT * FROM financial_ratios WHERE company_id = '{ticker}' ORDER BY year", conn)

    p1_img, p2_img = create_company_charts(ticker, pl_df, bs_df, cf_df, r_df)

    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=16, leading=18, textColor=colors.HexColor('#0F172A'))
    sub_style = ParagraphStyle('DocSub', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#475569'))
    h2_style = ParagraphStyle('SectionH2', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#334155'))
    bullet_style = ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#1E293B'), bulletIndent=6, leftIndent=16)

    elements = []

    # === PAGE 1 ===
    # Header Banner
    c_name = universe_row.get('company_name', ticker)
    sector = universe_row.get('broad_sector', 'N/A')
    sub_sec = universe_row.get('sub_sector', 'N/A')
    score = universe_row.get('composite_score', 50.0)

    header_table_data = [
        [
            Paragraph(f"<b>{c_name} ({ticker})</b><br/><font color='#64748B'>{sector} | {sub_sec}</font>", title_style),
            Paragraph(f"<para align='right'><font size=14 color='#1E88E5'><b>Health Score: {score}/100</b></font><br/><font size=7 color='#64748B'>Nifty 100 Fundamental Intelligence</font></para>", sub_style)
        ]
    ]
    t_head = Table(header_table_data, colWidths=[380, 160])
    t_head.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(t_head)
    elements.append(Spacer(1, 6))

    # Business Overview
    about_text = conn.execute(f"SELECT about_company FROM companies WHERE id = '{ticker}'").fetchone()[0]
    if about_text and len(str(about_text)) > 300:
        about_text = str(about_text)[:300] + "..."
    elements.append(Paragraph(f"<b>Business Profile:</b> {about_text or 'Leading constituent in Nifty 100.'}", body_style))
    elements.append(Spacer(1, 6))

    # KPI Tiles Table
    kpis = [
        ('Market Cap', f"₹{universe_row.get('market_cap_crore', 0):,.0f} Cr", 'P/E Ratio', f"{universe_row.get('pe_ratio', 0):.1f}x"),
        ('Return on Equity', f"{universe_row.get('return_on_equity_pct', 0):.1f}%", 'Debt / Equity', f"{universe_row.get('debt_to_equity', 0):.2f}x"),
        ('Free Cash Flow', f"₹{universe_row.get('free_cash_flow_cr', 0):,.0f} Cr", '5Y Rev CAGR', f"{universe_row.get('revenue_cagr_5yr', 0):.1f}%")
    ]
    kpi_table_data = [
        [
            Paragraph(f"<font color='#64748B'>{k1}:</font> <b>{v1}</b>", body_style),
            Paragraph(f"<font color='#64748B'>{k2}:</font> <b>{v2}</b>", body_style)
        ]
        for k1, v1, k2, v2 in kpis
    ]
    kpi_tbl = Table(kpi_table_data, colWidths=[270, 270])
    kpi_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F8FAFC')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(kpi_tbl)
    elements.append(Spacer(1, 10))

    # Page 1 Chart: Revenue & Profit, ROE
    elements.append(Paragraph("<b>Historical Performance & Return Ratios</b>", h2_style))
    elements.append(Image(p1_img, width=540, height=200))
    elements.append(Spacer(1, 6))

    # Financial Statement Summary Table (Last 4 Years)
    pl_recent = pl_df.tail(4)
    stmt_headers = ['Metric'] + [y[-5:] for y in pl_recent['year'].tolist()]
    stmt_data = [
        stmt_headers,
        ['Revenue (₹ Cr)'] + [f"{x:,.0f}" if pd.notnull(x) else '-' for x in pl_recent['sales']],
        ['Operating Profit (₹ Cr)'] + [f"{x:,.0f}" if pd.notnull(x) else '-' for x in pl_recent['operating_profit']],
        ['Net Profit (₹ Cr)'] + [f"{x:,.0f}" if pd.notnull(x) else '-' for x in pl_recent['net_profit']],
        ['EPS (₹)'] + [f"{x:.1f}" if pd.notnull(x) else '-' for x in pl_recent['eps']]
    ]
    pl_tbl = Table(stmt_data, colWidths=[140] + [100] * (len(stmt_headers) - 1))
    pl_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7.5),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
    ]))
    elements.append(pl_tbl)

    # === PAGE BREAK ===
    elements.append(PageBreak())

    # === PAGE 2 ===
    elements.append(Paragraph(f"<b>Financial Quality & Risk Intelligence — {ticker}</b>", title_style))
    elements.append(Spacer(1, 8))

    # Capital Allocation & Balance Sheet Overview
    cap_pat = universe_row.get('capital_allocation_pattern', 'Reinvestor')
    cfo_pat = universe_row.get('cfo_pat_ratio', 1.0)
    elements.append(Paragraph(f"<b>Capital Allocation Pattern:</b> <font color='#1E88E5'><b>{cap_pat}</b></font> | <b>CFO-to-PAT Quality:</b> {cfo_pat:.2f}x", body_style))
    elements.append(Spacer(1, 6))

    # Page 2 Chart: Cash Flow & Assets
    elements.append(Paragraph("<b>Cash Flow Dynamics & Solvency</b>", h2_style))
    elements.append(Image(p2_img, width=540, height=200))
    elements.append(Spacer(1, 10))

    # Qualitative Pros & Cons Section
    elements.append(Paragraph("<b>Investment Strengths (Pros)</b>", h2_style))
    for p in pros[:4]:
        elements.append(Paragraph(f"• <font color='#2E7D32'><b>Strengths:</b></font> {p}", bullet_style))
    elements.append(Spacer(1, 6))

    elements.append(Paragraph("<b>Key Risks & Considerations (Cons)</b>", h2_style))
    for c in cons[:4]:
        elements.append(Paragraph(f"• <font color='#C62828'><b>Risk Factor:</b></font> {c}", bullet_style))
    elements.append(Spacer(1, 14))

    # Disclaimer footer
    elements.append(Paragraph("<font size=6 color='#94A3B8'>Confidential. Produced for Nifty 100 Financial Intelligence Platform. Data sourced from audited annual filings and verified models.</font>", body_style))

    doc.build(elements)
    return out_pdf

def generate_all_tearsheets(db_path: str = DB_PATH):
    """Generate all 92 company tearsheet PDFs."""
    universe = get_latest_screener_universe(db_path)
    pc_df = pd.read_csv("output/pros_cons_generated.csv")

    with sqlite3.connect(db_path) as conn:
        for idx, row in universe.iterrows():
            ticker = row['ticker']
            p_list = pc_df[(pc_df['company_id'] == ticker) & (pc_df['type'] == 'pro')]['text'].tolist()
            c_list = pc_df[(pc_df['company_id'] == ticker) & (pc_df['type'] == 'con')]['text'].tolist()
            pdf_path = generate_tearsheet(ticker, conn, row, p_list, c_list)
            sz_kb = os.path.getsize(pdf_path) / 1024
            if idx % 15 == 0 or idx == len(universe) - 1:
                print(f"Generated ({idx+1}/92): {ticker}_tearsheet.pdf ({sz_kb:.1f} KB)")

if __name__ == "__main__":
    generate_all_tearsheets()
