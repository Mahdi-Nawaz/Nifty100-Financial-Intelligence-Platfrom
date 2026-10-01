"""Parser for qualitative analysis text fields and cross-validation against computed KPIs."""
import os
import sys
import re
import sqlite3
import pandas as pd
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath("."))

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
OUTPUT_DIR = "output"

def parse_analysis_records(db_path: str = DB_PATH) -> pd.DataFrame:
    """Parse string entries like '10 Years: 21%' from analysis table into structured records."""
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM analysis", conn)

    parsed_rows = []
    pattern = re.compile(r'(\d+)\s*Years?:?\s*([\d.]+)%?', re.IGNORECASE)

    metric_cols = [
        ('compounded_sales_growth', 'Sales CAGR'),
        ('compounded_profit_growth', 'Profit CAGR'),
        ('stock_price_cagr', 'Stock Price CAGR'),
        ('roe', 'ROE')
    ]

    for _, row in df.iterrows():
        cid = row['company_id']
        for col, label in metric_cols:
            raw_text = str(row.get(col, ''))
            matches = pattern.findall(raw_text)
            for m in matches:
                period_yrs = int(m[0])
                val_pct = float(m[1])
                parsed_rows.append({
                    'company_id': cid,
                    'metric_type': label,
                    'period_years': period_yrs,
                    'value_pct': val_pct
                })

    parsed_df = pd.DataFrame(parsed_rows)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    parsed_df.to_csv(os.path.join(OUTPUT_DIR, "analysis_parsed.csv"), index=False)
    print(f"Parsed {len(parsed_df)} records from analysis table.")
    return parsed_df

if __name__ == "__main__":
    parse_analysis_records()
