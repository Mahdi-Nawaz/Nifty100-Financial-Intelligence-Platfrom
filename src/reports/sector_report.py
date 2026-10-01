"""Sector Report Generator creating 11 broad sector intelligence PDFs via ReportLab."""
import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

sys.path.insert(0, os.path.abspath("."))
from src.analytics.screener.engine import get_latest_screener_universe

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "reports/sector"

def generate_sector_pdf(sector_name: str, sector_df: pd.DataFrame) -> str:
    """Generate a formatted PDF report for a given broad sector."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_sec = sector_name.replace("/", "_").replace(" ", "_")
    out_pdf = os.path.join(OUTPUT_DIR, f"{safe_sec}_report.pdf")

    doc = SimpleDocTemplate(
        out_pdf,
        pagesize=landscape(letter),
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('SecTitle', parent=styles['Heading1'], fontSize=16, leading=18, textColor=colors.HexColor('#0F172A'))
    sub_style = ParagraphStyle('SecSub', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#475569'))
    h2_style = ParagraphStyle('SecH2', parent=styles['Heading2'], fontSize=11, leading=14, textColor=colors.HexColor('#1E293B'), spaceBefore=8, spaceAfter=4)
    cell_style = ParagraphStyle('SecCell', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#1E293B'))

    elements = []

    # Header
    n_cos = len(sector_df)
    med_roe = sector_df['return_on_equity_pct'].median()
    med_pe = sector_df['pe_ratio'].median()
    med_de = sector_df['debt_to_equity'].median()
    tot_mktcap = sector_df['market_cap_crore'].sum()

    elements.append(Paragraph(f"<b>Nifty 100 Sector Intelligence: {sector_name}</b>", title_style))
    elements.append(Paragraph(f"Constituents: <b>{n_cos} companies</b> | Total Sector Mkt Cap: <b>₹{tot_mktcap:,.0f} Cr</b> | Median ROE: <b>{med_roe:.1f}%</b> | Median P/E: <b>{med_pe:.1f}x</b> | Median D/E: <b>{med_de:.2f}x</b>", sub_style))
    elements.append(Spacer(1, 12))

    # Benchmark Table of all companies in this sector
    headers = ['Ticker', 'Company Name', 'Sub-Sector', 'Mkt Cap (₹ Cr)', 'P/E', 'ROE %', 'D/E', 'FCF (₹ Cr)', '5Y Rev CAGR', 'Health Score']
    table_data = [[Paragraph(f"<b>{h}</b>", cell_style) for h in headers]]

    sorted_df = sector_df.sort_values(by='composite_score', ascending=False)
    for _, row in sorted_df.iterrows():
        tck = row.get('ticker', '')
        name = row.get('company_name', '')[:22]
        sub = row.get('sub_sector', '')[:18]
        mkt = f"₹{row.get('market_cap_crore', 0):,.0f}" if pd.notnull(row.get('market_cap_crore')) else '-'
        pe = f"{row.get('pe_ratio', 0):.1f}x" if pd.notnull(row.get('pe_ratio')) else '-'
        roe = f"{row.get('return_on_equity_pct', 0):.1f}%" if pd.notnull(row.get('return_on_equity_pct')) else '-'
        de = f"{row.get('debt_to_equity', 0):.2f}" if pd.notnull(row.get('debt_to_equity')) else '-'
        fcf = f"₹{row.get('free_cash_flow_cr', 0):,.0f}" if pd.notnull(row.get('free_cash_flow_cr')) else '-'
        cagr = f"{row.get('revenue_cagr_5yr', 0):.1f}%" if pd.notnull(row.get('revenue_cagr_5yr')) else '-'
        score = f"{row.get('composite_score', 0):.1f}" if pd.notnull(row.get('composite_score')) else '-'

        table_data.append([
            Paragraph(f"<b>{tck}</b>", cell_style),
            Paragraph(name, cell_style),
            Paragraph(sub, cell_style),
            Paragraph(mkt, cell_style),
            Paragraph(pe, cell_style),
            Paragraph(roe, cell_style),
            Paragraph(de, cell_style),
            Paragraph(fcf, cell_style),
            Paragraph(cagr, cell_style),
            Paragraph(f"<b>{score}</b>", cell_style)
        ])

    col_widths = [55, 130, 110, 85, 45, 50, 45, 75, 65, 60]
    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8FAFC')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 14))
    elements.append(Paragraph("<font size=7 color='#64748B'>Generated automatically by Nifty 100 Financial Intelligence Platform.</font>", cell_style))

    doc.build(elements)
    return out_pdf

def generate_all_sector_reports(db_path: str = DB_PATH):
    """Generate sector reports for all 11 sectors (including Conglomerates)."""
    universe = get_latest_screener_universe(db_path)
    sectors = universe['broad_sector'].dropna().unique().tolist()
    print(f"Generating sector reports for {len(sectors)} sectors...")
    for sec in sectors:
        sec_df = universe[universe['broad_sector'] == sec]
        generate_sector_pdf(sec, sec_df)

    # Generate 11th sector report: Conglomerates (from sub_sector mapping)
    conglom_df = universe[universe['sub_sector'].str.contains('Conglomerate|Diversified', case=False, na=False)]
    if not conglom_df.empty:
        generate_sector_pdf("Conglomerates", conglom_df)
    
    gen_files = [f for f in os.listdir(OUTPUT_DIR) if f.endswith('.pdf')]
    print(f"All {len(gen_files)} sector reports generated in {OUTPUT_DIR}")

if __name__ == "__main__":
    generate_all_sector_reports()
