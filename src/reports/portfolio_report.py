"""Portfolio Summary Report Generator compiling all 92 companies into a unified PDF document."""
import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

sys.path.insert(0, os.path.abspath("."))
from src.analytics.screener.engine import get_latest_screener_universe

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "reports/portfolio"

def generate_portfolio_summary_pdf(db_path: str = DB_PATH) -> str:
    """Generate portfolio_summary.pdf with all 92 companies (1 page per company)."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_pdf = os.path.join(OUTPUT_DIR, "portfolio_summary.pdf")

    universe = get_latest_screener_universe(db_path)
    pc_df = pd.read_csv("output/pros_cons_generated.csv")

    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('PortTitle', parent=styles['Heading1'], fontSize=16, leading=18, textColor=colors.HexColor('#0F172A'))
    sub_style = ParagraphStyle('PortSub', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#475569'))
    h2_style = ParagraphStyle('PortH2', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#1E293B'), spaceBefore=10, spaceAfter=4)
    body_style = ParagraphStyle('PortBody', parent=styles['Normal'], fontSize=8.5, leading=12, textColor=colors.HexColor('#334155'))
    cell_style = ParagraphStyle('PortCell', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.HexColor('#1E293B'))

    elements = []

    # Title Page / Executive Summary
    elements.append(Paragraph("<b>NIFTY 100 PORTFOLIO INTELLIGENCE SUMMARY</b>", title_style))
    elements.append(Paragraph(f"Universe: <b>{len(universe)} Companies</b> | Master Investment & Fundamental Reference", sub_style))
    elements.append(Spacer(1, 14))

    # Portfolio overview stats
    avg_roe = universe['return_on_equity_pct'].mean()
    med_pe = universe['pe_ratio'].median()
    tot_mktcap = universe['market_cap_crore'].sum()
    avg_score = universe['composite_score'].mean()

    elements.append(Paragraph(f"<b>Platform Metrics:</b> Aggregate Market Capitalisation: <b>₹{tot_mktcap:,.0f} Cr</b> | Average ROE: <b>{avg_roe:.1f}%</b> | Median P/E: <b>{med_pe:.1f}x</b> | Average Health Score: <b>{avg_score:.1f}/100</b>", body_style))
    elements.append(Spacer(1, 14))

    elements.append(Paragraph("<b>Constituent Navigation Index (Ranked by Composite Health Score)</b>", h2_style))
    index_headers = ['Rank', 'Ticker', 'Company Name', 'Sector', 'ROE %', 'P/E', 'FCF (₹ Cr)', 'Health Score']
    index_data = [[Paragraph(f"<b>{h}</b>", cell_style) for h in index_headers]]

    ranked_univ = universe.sort_values(by='composite_score', ascending=False).reset_index(drop=True)
    for rank_idx, r in ranked_univ.head(25).iterrows():
        index_data.append([
            Paragraph(str(rank_idx + 1), cell_style),
            Paragraph(f"<b>{r['ticker']}</b>", cell_style),
            Paragraph(str(r['company_name'])[:20], cell_style),
            Paragraph(str(r['broad_sector'])[:18], cell_style),
            Paragraph(f"{r['return_on_equity_pct']:.1f}%" if pd.notnull(r['return_on_equity_pct']) else '-', cell_style),
            Paragraph(f"{r['pe_ratio']:.1f}x" if pd.notnull(r['pe_ratio']) else '-', cell_style),
            Paragraph(f"₹{r['free_cash_flow_cr']:,.0f}" if pd.notnull(r['free_cash_flow_cr']) else '-', cell_style),
            Paragraph(f"<b>{r['composite_score']:.1f}</b>" if pd.notnull(r['composite_score']) else '-', cell_style)
        ])

    t_idx = Table(index_data, colWidths=[30, 60, 140, 110, 50, 45, 60, 55])
    t_idx.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (2, 0), (3, -1), 'LEFT'),
    ]))
    elements.append(t_idx)

    # Individual 1-page summaries for each company
    for _, row in universe.iterrows():
        elements.append(PageBreak())
        tck = row['ticker']
        c_name = row['company_name']
        sec = row.get('broad_sector', 'N/A')
        score = row.get('composite_score', 50.0)

        elements.append(Paragraph(f"<b>{c_name} ({tck})</b> — {sec}", title_style))
        elements.append(Paragraph(f"Composite Health Score: <b><font color='#1E88E5'>{score}/100</font></b> | Capital Pattern: <b>{row.get('capital_allocation_pattern', 'Reinvestor')}</b>", sub_style))
        elements.append(Spacer(1, 10))

        # KPI Matrix
        kpi_matrix = [
            [Paragraph("<b>Metric</b>", cell_style), Paragraph("<b>Value</b>", cell_style), Paragraph("<b>Metric</b>", cell_style), Paragraph("<b>Value</b>", cell_style)],
            [Paragraph("Market Capitalisation", cell_style), Paragraph(f"₹{row.get('market_cap_crore', 0):,.0f} Cr", cell_style), Paragraph("P/E Ratio", cell_style), Paragraph(f"{row.get('pe_ratio', 0):.1f}x", cell_style)],
            [Paragraph("Return on Equity (ROE)", cell_style), Paragraph(f"{row.get('return_on_equity_pct', 0):.1f}%", cell_style), Paragraph("Debt to Equity", cell_style), Paragraph(f"{row.get('debt_to_equity', 0):.2f}x", cell_style)],
            [Paragraph("Operating Margin (OPM)", cell_style), Paragraph(f"{row.get('operating_profit_margin_pct', 0):.1f}%", cell_style), Paragraph("Interest Coverage", cell_style), Paragraph(f"{row.get('interest_coverage', 0):.1f}x", cell_style)],
            [Paragraph("Free Cash Flow (FCF)", cell_style), Paragraph(f"₹{row.get('free_cash_flow_cr', 0):,.0f} Cr", cell_style), Paragraph("5-Yr Revenue CAGR", cell_style), Paragraph(f"{row.get('revenue_cagr_5yr', 0):.1f}%", cell_style)],
            [Paragraph("CFO to PAT Quality", cell_style), Paragraph(f"{row.get('cfo_pat_ratio', 0):.2f}x", cell_style), Paragraph("5-Yr PAT CAGR", cell_style), Paragraph(f"{row.get('pat_cagr_5yr', 0):.1f}%", cell_style)]
        ]
        kpi_table = Table(kpi_matrix, colWidths=[150, 120, 150, 120])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(kpi_table)
        elements.append(Spacer(1, 14))

        # Pros and Cons
        p_list = pc_df[(pc_df['company_id'] == tck) & (pc_df['type'] == 'pro')]['text'].tolist()
        c_list = pc_df[(pc_df['company_id'] == tck) & (pc_df['type'] == 'con')]['text'].tolist()

        elements.append(Paragraph("<b>Investment Strengths:</b>", h2_style))
        for p in p_list[:3]:
            elements.append(Paragraph(f"• <font color='#2E7D32'>{p}</font>", body_style))
        elements.append(Spacer(1, 6))

        elements.append(Paragraph("<b>Investment Risks:</b>", h2_style))
        for c in c_list[:3]:
            elements.append(Paragraph(f"• <font color='#C62828'>{c}</font>", body_style))

    doc.build(elements)
    print(f"Generated portfolio summary PDF at {out_pdf} ({len(universe)} companies).")
    return out_pdf

if __name__ == "__main__":
    generate_portfolio_summary_pdf()
