"""Statistical Analysis & KMeans Clustering Module for Nifty 100 Financial Intelligence."""
import os
import sys
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))
from src.analytics.screener.engine import get_latest_screener_universe

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"
REPORTS_DIR = "reports"

CLUSTER_FEATURES = ['return_on_equity_pct', 'debt_to_equity', 'revenue_cagr_5yr', 'free_cash_flow_cr', 'operating_profit_margin_pct']
STATS_METRICS = ['return_on_equity_pct', 'operating_profit_margin_pct', 'net_profit_margin_pct', 'debt_to_equity', 'pe_ratio', 'pb_ratio', 'dividend_yield_pct', 'free_cash_flow_cr', 'revenue_cagr_5yr', 'pat_cagr_5yr']

CLUSTER_NAMES = [
    "High-Quality Growth",
    "Defensive Dividend & Cash Rich",
    "Value & Capital Intensive",
    "High Leverage Turnaround",
    "Emerging Compounders"
]

def run_clustering_and_stats(db_path: str = DB_PATH) -> Dict[str, Any]:
    """Run KMeans clustering, correlation heatmap, outlier detection, and portfolio statistics."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)
    universe = get_latest_screener_universe(db_path)

    # 1. KMeans Clustering (n=5)
    X_raw = universe[CLUSTER_FEATURES].copy()
    # Impute missing values with median for clustering stability
    X_imputed = X_raw.fillna(X_raw.median())
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)

    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Distance from centroid
    centroids = kmeans.cluster_centers_
    distances = [
        np.linalg.norm(X_scaled[i] - centroids[clusters[i]]) 
        for i in range(len(clusters))
    ]

    cluster_df = pd.DataFrame({
        'company_id': universe['ticker'],
        'cluster_id': clusters,
        'cluster_name': [CLUSTER_NAMES[c] for c in clusters],
        'distance_from_centroid': np.round(distances, 3)
    })
    cluster_df.to_csv(os.path.join(OUTPUT_DIR, "cluster_labels.csv"), index=False)

    # 2. Portfolio Statistics (P10, P25, P50, P75, P90, Mean, Std)
    stats_rows = []
    for m in STATS_METRICS:
        if m in universe.columns:
            vals = universe[m].dropna()
            if not vals.empty:
                stats_rows.append({
                    'Metric': m,
                    'P10': round(float(np.percentile(vals, 10)), 2),
                    'P25': round(float(np.percentile(vals, 25)), 2),
                    'P50': round(float(np.percentile(vals, 50)), 2),
                    'P75': round(float(np.percentile(vals, 75)), 2),
                    'P90': round(float(np.percentile(vals, 90)), 2),
                    'Mean': round(float(vals.mean()), 2),
                    'Std': round(float(vals.std()), 2)
                })
    p_stats_df = pd.DataFrame(stats_rows)
    p_stats_df.to_csv(os.path.join(OUTPUT_DIR, "portfolio_stats.csv"), index=False)

    # 3. Correlation Matrix & Heatmap
    corr_metrics = [m for m in STATS_METRICS if m in universe.columns]
    corr_matrix = universe[corr_metrics].corr()

    fig, ax = plt.subplots(figsize=(10, 8))
    cax = ax.matshow(corr_matrix, cmap='coolwarm', vmin=-1, vmax=1)
    fig.colorbar(cax)
    ax.set_xticks(range(len(corr_metrics)))
    ax.set_yticks(range(len(corr_metrics)))
    ax.set_xticklabels(corr_metrics, rotation=45, ha='left', fontsize=8)
    ax.set_yticklabels(corr_metrics, fontsize=8)
    plt.title('Nifty 100 Financial Metrics Correlation Heatmap', pad=20, fontweight='bold')
    plt.tight_layout()
    plt.savefig(os.path.join(REPORTS_DIR, "correlation_heatmap.png"), dpi=150)
    plt.close(fig)

    # 4. Outlier Detection: Z-score > 3 within Sector
    outlier_records = []
    for sector, s_grp in universe.groupby('broad_sector'):
        if len(s_grp) < 3:
            continue
        for m in STATS_METRICS:
            if m not in s_grp.columns:
                continue
            s_vals = s_grp[m].dropna()
            if len(s_vals) < 3:
                continue
            s_mean = s_vals.mean()
            s_std = s_vals.std()
            if s_std == 0 or np.isnan(s_std):
                continue
            for _, r in s_grp.iterrows():
                val = r.get(m)
                if pd.notnull(val):
                    z = (val - s_mean) / s_std
                    if abs(z) > 2.5: # Outlier threshold
                        outlier_records.append({
                            'company_id': r['ticker'],
                            'metric': m,
                            'value': round(float(val), 2),
                            'z_score': round(float(z), 2),
                            'sector': sector,
                            'sector_mean': round(float(s_mean), 2),
                            'sector_std': round(float(s_std), 2)
                        })

    outlier_df = pd.DataFrame(outlier_records)
    outlier_df.to_csv(os.path.join(OUTPUT_DIR, "outlier_report.csv"), index=False)

    print(f"Clustering & statistical analysis completed: 5 clusters assigned to {len(cluster_df)} companies.")
    return {
        'clusters': cluster_df,
        'stats': p_stats_df,
        'outliers': outlier_df
    }

if __name__ == "__main__":
    run_clustering_and_stats()
