"""Unsupervised Machine Learning Accounting Anomaly Detection Engine.

Uses Isolation Forest and Principal Component Analysis (PCA) to detect multivariate
forensic and fundamental accounting anomalies across 92 Nifty 100 companies.
"""
import os
import sys
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.decomposition import PCA
from sklearn.preprocessing import RobustScaler

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"

# Key forensic & fundamental features for multivariate anomaly detection
ANOMALY_FEATURES = [
    'beneish_m_score',
    'dsri',
    'aqi',
    'sgi',
    'depi',
    'sgai',
    'lvgi',
    'tata',
    'altman_z_score',
    'piotroski_f_score',
    'cfo_pat_ratio',
    'debt_to_equity',
    'operating_profit_margin_pct',
    'composite_score'
]

FEATURE_LABELS = {
    'beneish_m_score': 'Beneish M-Score (Earnings Manipulation)',
    'dsri': 'DSRI (Days Sales in Receivables)',
    'aqi': 'AQI (Asset Quality Index)',
    'sgi': 'SGI (Sales Growth Index)',
    'depi': 'DEPI (Depreciation Rate Index)',
    'sgai': 'SGAI (Sales General & Admin Index)',
    'lvgi': 'LVGI (Leverage Index)',
    'tata': 'TATA (Total Accruals to Total Assets)',
    'altman_z_score': 'Altman Z-Score (Solvency/Insolvency)',
    'piotroski_f_score': 'Piotroski F-Score (Operational Quality)',
    'cfo_pat_ratio': 'CFO/PAT Ratio (Cash Conversion)',
    'debt_to_equity': 'Debt-to-Equity (Gearing)',
    'operating_profit_margin_pct': 'Operating Profit Margin %',
    'composite_score': 'Composite Health Score'
}

def load_ml_dataset(db_path: str = DB_PATH) -> pd.DataFrame:
    """Join forensic_audit, latest financial_ratios, and companies into a unified feature set."""
    with sqlite3.connect(db_path) as conn:
        query = """
        SELECT 
            f.company_id,
            f.company_name,
            f.broad_sector,
            f.latest_year,
            f.beneish_m_score,
            f.beneish_flag,
            f.dsri,
            f.aqi,
            f.sgi,
            f.depi,
            f.sgai,
            f.lvgi,
            f.tata,
            f.altman_z_score,
            f.altman_zone,
            f.piotroski_f_score,
            f.piotroski_category,
            r.cfo_pat_ratio,
            r.debt_to_equity,
            r.operating_profit_margin_pct,
            r.composite_score,
            r.free_cash_flow_cr,
            r.return_on_equity_pct
        FROM forensic_audit f
        LEFT JOIN financial_ratios r ON f.company_id = r.company_id AND f.latest_year = r.year
        """
        df = pd.read_sql_query(query, conn)
    return df

def run_ml_anomaly_detection(contamination: float = 0.12, db_path: str = DB_PATH) -> Dict[str, Any]:
    """Train Isolation Forest and PCA to classify and explain accounting anomalies."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df_raw = load_ml_dataset(db_path)

    # 1. Clean & Impute Missing Features
    X = df_raw[ANOMALY_FEATURES].copy()
    
    # Impute missing values with median
    medians = X.median()
    stds = X.std().replace(0, 1e-6)
    X_imputed = X.fillna(medians)

    # 2. Scale features using RobustScaler (handles heavy financial tails)
    scaler = RobustScaler()
    X_scaled = scaler.fit_transform(X_imputed)

    # 3. Fit Isolation Forest
    iso_forest = IsolationForest(
        n_estimators=250,
        contamination=contamination,
        random_state=42,
        bootstrap=True,
        n_jobs=1
    )
    raw_preds = iso_forest.fit_predict(X_scaled) # -1 = Outlier/Anomaly, 1 = Inlier/Normal
    raw_scores = iso_forest.decision_function(X_scaled) # Lower score = higher anomaly

    # Normalize anomaly risk to 0 - 100%
    min_s, max_s = raw_scores.min(), raw_scores.max()
    anomaly_risk_pct = 100 * (1 - (raw_scores - min_s) / (max_s - min_s + 1e-6))

    # 4. Dimensionality Reduction with PCA (2D & 3D projection)
    pca_3d = PCA(n_components=3, random_state=42)
    pca_coords = pca_3d.fit_transform(X_scaled)
    var_explained = pca_3d.explained_variance_ratio_

    # 5. Feature Deviation & Explanation Engine
    # Compute standardized deviations from universe median to explain why flagged
    z_scores = (X_imputed - medians) / stds

    anomalies_summary = []
    for i in range(len(df_raw)):
        is_anomaly = (raw_preds[i] == -1)
        comp_row = df_raw.iloc[i]
        comp_z = z_scores.iloc[i]

        # Find top 3 features with highest absolute deviation
        top_deviations = comp_z.abs().sort_values(ascending=False).head(3)
        driver_explanations = []
        for feat_name, abs_dev in top_deviations.items():
            actual_val = X_imputed.iloc[i][feat_name]
            med_val = medians[feat_name]
            direction = "elevated" if actual_val > med_val else "depressed"
            label = FEATURE_LABELS.get(feat_name, feat_name)
            driver_explanations.append(
                f"{label}: {actual_val:.2f} (Median: {med_val:.2f}, {abs_dev:.1f}σ {direction})"
            )

        anomalies_summary.append({
            'company_id': comp_row['company_id'],
            'company_name': comp_row['company_name'],
            'broad_sector': comp_row['broad_sector'],
            'is_anomaly': is_anomaly,
            'anomaly_status': 'Outlier / Anomaly' if is_anomaly else 'Conforming Profile',
            'anomaly_risk_pct': round(float(anomaly_risk_pct[i]), 1),
            'raw_decision_score': round(float(raw_scores[i]), 4),
            'pc1': round(float(pca_coords[i, 0]), 3),
            'pc2': round(float(pca_coords[i, 1]), 3),
            'pc3': round(float(pca_coords[i, 2]), 3),
            'primary_driver_1': driver_explanations[0] if len(driver_explanations) > 0 else '',
            'primary_driver_2': driver_explanations[1] if len(driver_explanations) > 1 else '',
            'primary_driver_3': driver_explanations[2] if len(driver_explanations) > 2 else '',
            'beneish_m_score': comp_row['beneish_m_score'],
            'beneish_flag': comp_row['beneish_flag'],
            'altman_z_score': comp_row['altman_z_score'],
            'altman_zone': comp_row['altman_zone'],
            'piotroski_f_score': comp_row['piotroski_f_score'],
            'cfo_pat_ratio': comp_row['cfo_pat_ratio'],
            'debt_to_equity': comp_row['debt_to_equity'],
            'composite_score': comp_row['composite_score']
        })

    results_df = pd.DataFrame(anomalies_summary)
    # Sort with highest anomaly risk first
    results_df = results_df.sort_values(by='anomaly_risk_pct', ascending=False).reset_index(drop=True)

    # Save to SQLite table
    with sqlite3.connect(db_path) as conn:
        results_df.to_sql('ml_anomalies', conn, if_exists='replace', index=False)

    results_df.to_csv(os.path.join(OUTPUT_DIR, "ml_accounting_anomalies.csv"), index=False)

    return {
        'df': results_df,
        'total_companies': len(results_df),
        'anomalies_count': int((results_df['is_anomaly'] == True).sum()),
        'var_explained': [round(float(v) * 100, 1) for v in var_explained],
        'feature_medians': medians.to_dict(),
        'feature_stds': stds.to_dict()
    }

if __name__ == "__main__":
    out = run_ml_anomaly_detection()
    print(f"ML Anomaly Detection Run Complete:")
    print(f"Total Companies: {out['total_companies']}")
    print(f"Outliers Detected: {out['anomalies_count']}")
    print(f"Explained Variance (PC1, PC2, PC3): {out['var_explained']}%")
    print("\nTop 5 Detected Accounting Outliers:")
    print(out['df'][out['df']['is_anomaly'] == True][['company_id', 'company_name', 'anomaly_risk_pct', 'primary_driver_1']].head(5))
