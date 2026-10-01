"""Screen 09: Forensic Accounting & Corporate Governance Red Flag Triage."""
import os
import sys
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath("."))
from src.dashboard.utils.db import get_all_tickers
from src.analytics.forensics import compute_forensic_scores

st.set_page_config(page_title="Forensic Audit - Nifty 100", page_icon="🛡️", layout="wide")

st.title("🛡️ Forensic Accounting & Red Flag Triage")
st.markdown("""
**Institutional Forensic Governance Suite**: Detects financial statement anomalies, window-dressing risks, 
and insolvency signals using **Beneish M-Score** (8 factors), **Altman Z''-Score** (Emerging Markets), and **Piotroski F-Score** (9 signals).
""")

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")

@st.cache_data
def load_forensic_data():
    with sqlite3.connect(DB_PATH) as conn:
        try:
            df = pd.read_sql_query("SELECT * FROM forensic_audit", conn)
        except Exception:
            df = compute_forensic_scores(DB_PATH)
    return df

df_forensic = load_forensic_data()

# KPI Banner
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    distress_count = len(df_forensic[df_forensic['altman_zone'] == 'Distress Zone'])
    st.metric("Distress Zone Candidates", f"{distress_count}", delta=f"-{distress_count} Watchlist", delta_color="inverse")
with kpi2:
    high_risk_m = len(df_forensic[df_forensic['beneish_flag'].str.contains('High Risk')])
    st.metric("Potential M-Score Flags", f"{high_risk_m}", help="Beneish M-Score > -1.78")
with kpi3:
    strong_f = len(df_forensic[df_forensic['piotroski_f_score'] >= 7])
    st.metric("High Quality Compounders (F >= 7)", f"{strong_f}", delta="Fundamental Momentum")
with kpi4:
    avg_f = df_forensic['piotroski_f_score'].mean()
    st.metric("Universe Mean F-Score", f"{avg_f:.2f}/9")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["🔍 Triage Quadrant Analysis", "📋 Full Universe Forensic Audit", "🏢 Company Deep-Dive Audit"])

with tab1:
    st.subheader("Earnings Quality vs. Solvency Quadrant")
    st.caption("X-axis: Altman Z''-Score (Solvency/Bankruptcy Risk). Y-axis: Beneish M-Score (Earnings Manipulation Risk). Lower-Right is Safest.")

    # Scatter plot
    clean_scatter_df = df_forensic[df_forensic['broad_sector'] != 'Financials'].copy()
    fig_scatter = px.scatter(
        clean_scatter_df,
        x="altman_z_score",
        y="beneish_m_score",
        color="piotroski_category",
        hover_name="company_name",
        hover_data=["company_id", "broad_sector", "beneish_flag", "altman_zone"],
        size="piotroski_f_score",
        color_discrete_map={
            "Very Strong (7-9)": "#10B981",
            "Moderate (5-6)": "#38BDF8",
            "Weak (0-4)": "#EF4444"
        },
        title="Nifty 100 Non-Financials: Beneish M vs Altman Z Quadrants"
    )
    # Threshold lines
    fig_scatter.add_hline(y=-1.78, line_dash="dash", line_color="red", annotation_text="Beneish Manipulation Threshold (-1.78)")
    fig_scatter.add_vline(x=2.60, line_dash="dash", line_color="green", annotation_text="Altman Safe Zone (2.60)")
    fig_scatter.add_vline(x=1.10, line_dash="dash", line_color="orange", annotation_text="Altman Distress Zone (1.10)")
    fig_scatter.update_layout(template="plotly_dark", height=550)
    st.plotly_chart(fig_scatter, use_container_width=True)

with tab2:
    st.subheader("Constituent Forensic Audit Table")
    c1, c2, c3 = st.columns(3)
    with c1:
        sec_filter = st.multiselect("Filter Sector", sorted(df_forensic['broad_sector'].dropna().unique()), default=[])
    with c2:
        alt_filter = st.multiselect("Filter Altman Zone", sorted(df_forensic['altman_zone'].dropna().unique()), default=[])
    with c3:
        ben_filter = st.multiselect("Filter Beneish Flag", sorted(df_forensic['beneish_flag'].dropna().unique()), default=[])

    filtered_df = df_forensic.copy()
    if sec_filter:
        filtered_df = filtered_df[filtered_df['broad_sector'].isin(sec_filter)]
    if alt_filter:
        filtered_df = filtered_df[filtered_df['altman_zone'].isin(alt_filter)]
    if ben_filter:
        filtered_df = filtered_df[filtered_df['beneish_flag'].isin(ben_filter)]

    disp_cols = [
        'company_id', 'company_name', 'broad_sector', 'beneish_m_score',
        'beneish_flag', 'altman_z_score', 'altman_zone', 'piotroski_f_score', 'piotroski_category'
    ]
    st.dataframe(filtered_df[disp_cols].reset_index(drop=True), use_container_width=True)

with tab3:
    st.subheader("Individual Company Forensic Breakdown")
    selected_ticker = st.selectbox("Select Constituent:", sorted(df_forensic['company_id'].unique()))
    row = df_forensic[df_forensic['company_id'] == selected_ticker].iloc[0]

    st.markdown(f"### {row['company_name']} ({row['company_id']}) - Sector: *{row['broad_sector']}*")

    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"""
        <div style="background:#1E293B; border-radius:8px; padding:16px; border:1px solid #334155;">
            <h4 style="margin:0; color:#94A3B8;">Beneish M-Score</h4>
            <h2 style="margin:8px 0; color:{'#EF4444' if 'High Risk' in row['beneish_flag'] else '#10B981'};">{row['beneish_m_score']}</h2>
            <p style="margin:0; font-size:13px;">Status: <b>{row['beneish_flag']}</b></p>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div style="background:#1E293B; border-radius:8px; padding:16px; border:1px solid #334155;">
            <h4 style="margin:0; color:#94A3B8;">Altman Z''-Score</h4>
            <h2 style="margin:8px 0; color:{'#10B981' if row['altman_zone']=='Safe Zone' else '#F59E0B' if row['altman_zone']=='Grey Zone' else '#EF4444'};">{row['altman_z_score']}</h2>
            <p style="margin:0; font-size:13px;">Classification: <b>{row['altman_zone']}</b></p>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div style="background:#1E293B; border-radius:8px; padding:16px; border:1px solid #334155;">
            <h4 style="margin:0; color:#94A3B8;">Piotroski F-Score</h4>
            <h2 style="margin:8px 0; color:#38BDF8;">{row['piotroski_f_score']} / 9</h2>
            <p style="margin:0; font-size:13px;">Category: <b>{row['piotroski_category']}</b></p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.write("**Beneish 8-Factor Sub-Indices:**")
    b_factors = {
        "DSRI (Days Sales in Receivables)": row.get('dsri'),
        "GMI (Gross Margin Index)": row.get('gmi'),
        "AQI (Asset Quality Index)": row.get('aqi'),
        "SGI (Sales Growth Index)": row.get('sgi'),
        "DEPI (Depreciation Rate Index)": row.get('depi'),
        "SGAI (Sales, General & Admin Index)": row.get('sgai'),
        "LVGI (Leverage Index)": row.get('lvgi'),
        "TATA (Total Accruals to Total Assets)": row.get('tata')
    }
    b_df = pd.DataFrame(list(b_factors.items()), columns=["Forensic Sub-Index", "Observed Factor Value"])
    st.table(b_df)
