"""Screen 12: Machine Learning Accounting Anomaly & Forensic Outlier Detector."""
import os
import sys
import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.insert(0, os.path.abspath("."))
from src.analytics.ml_anomaly import run_ml_anomaly_detection, FEATURE_LABELS

st.set_page_config(page_title="ML Anomaly Detector - Nifty 100", page_icon="🤖", layout="wide")

st.title("🤖 Machine Learning Accounting Anomaly Detector")
st.markdown("""
**Unsupervised Multivariate Anomaly Detection**: Employs **Isolation Forest** (250 estimators) combined with **Principal Component Analysis (PCA)** across **14 forensic and fundamental indicators** to detect statistical outliers, creative accounting anomalies, and hidden balance sheet stress across the 92 Nifty 100 companies.
""")

# Sidebar Controls
st.sidebar.header("⚙️ ML Model Hyperparameters")
contamination = st.sidebar.slider(
    "Contamination Rate (Target Outlier Ratio)",
    min_value=0.05,
    max_value=0.25,
    value=0.12,
    step=0.01,
    help="Expected proportion of anomalies in the dataset. Default 12% aligns with typical forensic stress rate."
)

sector_filter = st.sidebar.selectbox(
    "Filter by Broad Sector",
    options=["All Sectors", "Financial Services", "Information Technology", "Automobile and Auto Components", "Fast Moving Consumer Goods", "Oil, Gas and Consumable Fuels", "Healthcare", "Metals and Mining", "Capital Goods"]
)

# Run or load ML results
@st.cache_data(show_spinner="Training Isolation Forest & Fitting PCA...")
def get_ml_results(contam_rate: float):
    return run_ml_anomaly_detection(contamination=contam_rate)

ml_data = get_ml_results(contamination)
df_all = ml_data['df']

# Apply sector filter if selected
if sector_filter != "All Sectors":
    df_display = df_all[df_all['broad_sector'] == sector_filter].copy()
else:
    df_display = df_all.copy()

outliers_detected = int((df_display['is_anomaly'] == True).sum())
total_shown = len(df_display)
avg_anomaly_risk = df_display['anomaly_risk_pct'].mean()
highest_risk = df_display.iloc[0]['company_name'] if not df_display.empty else "N/A"

# KPI Metrics Banner
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.metric("Companies Evaluated", f"{total_shown}", help="Total constituents in selected universe")
with kpi2:
    st.metric(
        "ML Outliers Flagged", 
        f"{outliers_detected}", 
        delta=f"{round(outliers_detected / max(1, total_shown) * 100, 1)}% of universe",
        delta_color="inverse"
    )
with kpi3:
    st.metric(
        "PCA Variance Explained", 
        f"{sum(ml_data['var_explained']):.1f}%", 
        help=f"PC1: {ml_data['var_explained'][0]}% | PC2: {ml_data['var_explained'][1]}% | PC3: {ml_data['var_explained'][2]}%"
    )
with kpi4:
    st.metric("Highest Anomaly Risk", highest_risk, delta=f"{df_display.iloc[0]['anomaly_risk_pct']}% Risk" if not df_display.empty else "")

st.markdown("---")

# Main Visualizations: 2D vs 3D PCA Space
col_view, col_opt = st.columns([3, 1])
with col_opt:
    viz_mode = st.radio("Dimensionality View", ["2D PCA Projection", "3D PCA Projection"], horizontal=True)

# Scatter Chart
if viz_mode == "2D PCA Projection":
    fig = px.scatter(
        df_display,
        x='pc1',
        y='pc2',
        color='anomaly_status',
        color_discrete_map={
            'Outlier / Anomaly': '#EF4444',
            'Conforming Profile': '#0EA5E9'
        },
        size='anomaly_risk_pct',
        hover_name='company_name',
        hover_data={
            'company_id': True,
            'broad_sector': True,
            'anomaly_risk_pct': ':.1f%',
            'primary_driver_1': True,
            'pc1': False,
            'pc2': False,
            'anomaly_status': False
        },
        title=f"2D Multivariate PCA Feature Space (PC1: {ml_data['var_explained'][0]}% vs PC2: {ml_data['var_explained'][1]}% Variance)",
        labels={'pc1': 'Principal Component 1 (Solvency & Quality Dimension)', 'pc2': 'Principal Component 2 (Accruals & Margin Dimension)'},
        template="plotly_dark",
        height=540
    )
    fig.update_traces(marker=dict(line=dict(width=1.5, color='#FFFFFF'), opacity=0.85))
    st.plotly_chart(fig, use_container_width=True)
else:
    fig_3d = px.scatter_3d(
        df_display,
        x='pc1',
        y='pc2',
        z='pc3',
        color='anomaly_status',
        color_discrete_map={
            'Outlier / Anomaly': '#EF4444',
            'Conforming Profile': '#0EA5E9'
        },
        size='anomaly_risk_pct',
        hover_name='company_name',
        hover_data={
            'company_id': True,
            'broad_sector': True,
            'anomaly_risk_pct': ':.1f%',
            'primary_driver_1': True
        },
        title=f"3D PCA Manifold ({sum(ml_data['var_explained']):.1f}% Total Variance Captured)",
        labels={'pc1': 'PC1', 'pc2': 'PC2', 'pc3': 'PC3'},
        template="plotly_dark",
        height=620
    )
    fig_3d.update_traces(marker=dict(line=dict(width=1, color='#FFFFFF'), opacity=0.85))
    st.plotly_chart(fig_3d, use_container_width=True)

st.markdown("---")

# Section: Explainable AI & Deep-Dive Inspector
st.subheader("🔍 Explainable AI (XAI): Forensic Anomaly Inspector")
st.markdown("Select any company below to inspect the **exact statistical deviations** and mathematical reasons the Isolation Forest classified it as an anomaly or normal profile.")

selected_company = st.selectbox(
    "Choose Company to Inspect",
    options=df_display['company_name'].tolist(),
    index=0 if not df_display.empty else 0
)

if selected_company:
    comp_row = df_display[df_display['company_name'] == selected_company].iloc[0]
    
    col_stat1, col_stat2, col_stat3 = st.columns([1, 1, 2])
    with col_stat1:
        if comp_row['is_anomaly']:
            st.error(f"🚨 **STATUS: STATISTICAL OUTLIER**\n\nAnomaly Risk: **{comp_row['anomaly_risk_pct']}%**")
        else:
            st.success(f"✅ **STATUS: CONFORMING PROFILE**\n\nAnomaly Risk: **{comp_row['anomaly_risk_pct']}%**")
        st.markdown(f"**Sector**: {comp_row['broad_sector']}")
        st.markdown(f"**Ticker**: `{comp_row['company_id']}`")
    
    with col_stat2:
        st.metric("Composite Health Score", f"{comp_row['composite_score']:.1f}/100")
        st.metric("Beneish M-Score", f"{comp_row['beneish_m_score']:.2f}", delta=comp_row['beneish_flag'], delta_color="inverse" if "High Risk" in str(comp_row['beneish_flag']) else "normal")
        st.metric("Altman Z-Score", f"{comp_row['altman_z_score']:.2f}", delta=comp_row['altman_zone'], delta_color="inverse" if "Distress" in str(comp_row['altman_zone']) else "normal")

    with col_stat3:
        st.markdown("### 📌 Top ML Attribution Drivers")
        st.markdown(f"1. **Primary Deviation**: `{comp_row['primary_driver_1']}`")
        st.markdown(f"2. **Secondary Deviation**: `{comp_row['primary_driver_2']}`")
        if comp_row['primary_driver_3']:
            st.markdown(f"3. **Tertiary Deviation**: `{comp_row['primary_driver_3']}`")
        st.caption("Deviations are measured in standard deviations (σ) relative to the universe median across all 92 companies.")

st.markdown("---")

# Comprehensive Data Table
st.subheader("📋 Complete Nifty 100 ML Anomaly Ranking")
table_cols = [
    'company_id', 'company_name', 'broad_sector', 'anomaly_status', 
    'anomaly_risk_pct', 'primary_driver_1', 'beneish_m_score', 
    'altman_z_score', 'piotroski_f_score', 'composite_score'
]
st.dataframe(
    df_display[table_cols].rename(columns={
        'company_id': 'Ticker',
        'company_name': 'Company',
        'broad_sector': 'Sector',
        'anomaly_status': 'ML Classification',
        'anomaly_risk_pct': 'Anomaly Risk %',
        'primary_driver_1': 'Top Anomaly Driver',
        'beneish_m_score': 'Beneish M',
        'altman_z_score': 'Altman Z',
        'piotroski_f_score': 'Piotroski F',
        'composite_score': 'Health Score'
    }),
    use_container_width=True,
    height=400
)
