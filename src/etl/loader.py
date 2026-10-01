"""ETL Loader for Nifty 100 Financial Intelligence Platform."""
import os
import sys
import time
import sqlite3
import datetime
import logging
import pandas as pd
from typing import Dict, Tuple

sys.path.insert(0, os.path.abspath("."))
from src.etl.normaliser import normalize_ticker, normalize_year
from src.etl.validator import DQValidator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("etl_loader")

DB_PATH = os.environ.get("DB_PATH", "data/nifty100.db")
SCHEMA_PATH = "src/etl/schema.sql"
OUTPUT_DIR = "output"

CORE_DATASETS = {
    'companies': 'data/raw/companies.xlsx',
    'profitandloss': 'data/raw/profitandloss.xlsx',
    'balancesheet': 'data/raw/balancesheet.xlsx',
    'cashflow': 'data/raw/cashflow.xlsx',
    'analysis': 'data/raw/analysis.xlsx',
    'documents': 'data/raw/documents.xlsx',
    'prosandcons': 'data/raw/prosandcons.xlsx',
}

SUPPLEMENTARY_DATASETS = {
    'sectors': 'data/supporting/sectors.xlsx',
    'market_cap': 'data/supporting/market_cap.xlsx',
    'peer_groups': 'data/supporting/peer_groups.xlsx',
    'stock_prices': 'data/supporting/stock_prices.xlsx',
    'financial_ratios': 'data/supporting/financial_ratios.xlsx',
}

def init_database(db_path: str = DB_PATH, schema_path: str = SCHEMA_PATH):
    """Initialise SQLite database with tables, indexes, and foreign keys."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception as e:
            logger.warning(f"Could not remove old DB: {e}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(schema_sql)
        conn.commit()
    logger.info(f"Database schema initialized at {db_path}")

def load_all_data(db_path: str = DB_PATH) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Execute full ETL load: extract, transform, validate, and load to SQLite."""
    start_time = time.time()
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    init_database(db_path)

    validator = DQValidator()
    audit_records = []

    # 1. Load companies master table
    c_start = time.time()
    comp_path = CORE_DATASETS['companies']
    df_comp_raw = pd.read_excel(comp_path, header=1)
    rows_in = len(df_comp_raw)

    df_comp = df_comp_raw.copy()
    df_comp['id'] = df_comp['id'].apply(normalize_ticker)
    if 'company_name' in df_comp.columns:
        df_comp['company_name'] = df_comp['company_name'].astype(str).str.replace('\n', ' ').str.strip()

    df_comp = validator.validate_companies(df_comp)
    valid_companies = set(df_comp['id'].dropna().unique())

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_comp.to_sql('companies', conn, if_exists='append', index=False)
        conn.commit()

    rows_out = len(df_comp)
    audit_records.append({
        'table': 'companies',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - c_start, 3)
    })
    logger.info(f"Loaded companies: {rows_out} records (rejected {rows_in - rows_out})")

    # 2. Load core financial statements: P&L, BS, CF
    # P&L
    p_start = time.time()
    df_pl_raw = pd.read_excel(CORE_DATASETS['profitandloss'], header=1)
    rows_in = len(df_pl_raw)
    df_pl = df_pl_raw.copy()
    df_pl['company_id'] = df_pl['company_id'].apply(normalize_ticker)
    df_pl['year'] = df_pl['year'].apply(normalize_year)
    df_pl = validator.validate_pl(df_pl, valid_companies)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_pl.to_sql('profitandloss', conn, if_exists='append', index=False)
        conn.commit()

    rows_out = len(df_pl)
    audit_records.append({
        'table': 'profitandloss',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - p_start, 3)
    })
    logger.info(f"Loaded profitandloss: {rows_out} records")

    # Balance Sheet
    b_start = time.time()
    df_bs_raw = pd.read_excel(CORE_DATASETS['balancesheet'], header=1)
    rows_in = len(df_bs_raw)
    df_bs = df_bs_raw.copy()
    df_bs['company_id'] = df_bs['company_id'].apply(normalize_ticker)
    df_bs['year'] = df_bs['year'].apply(normalize_year)
    df_bs = validator.validate_bs(df_bs, valid_companies)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_bs.to_sql('balancesheet', conn, if_exists='append', index=False)
        conn.commit()

    rows_out = len(df_bs)
    audit_records.append({
        'table': 'balancesheet',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - b_start, 3)
    })
    logger.info(f"Loaded balancesheet: {rows_out} records")

    # Cash Flow
    cf_start = time.time()
    df_cf_raw = pd.read_excel(CORE_DATASETS['cashflow'], header=1)
    rows_in = len(df_cf_raw)
    df_cf = df_cf_raw.copy()
    df_cf['company_id'] = df_cf['company_id'].apply(normalize_ticker)
    df_cf['year'] = df_cf['year'].apply(normalize_year)
    df_cf = validator.validate_cf(df_cf, valid_companies)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_cf.to_sql('cashflow', conn, if_exists='append', index=False)
        conn.commit()

    rows_out = len(df_cf)
    audit_records.append({
        'table': 'cashflow',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - cf_start, 3)
    })
    logger.info(f"Loaded cashflow: {rows_out} records")

    # Check coverage across time-series
    validator.check_coverage(df_pl, valid_companies)

    # 3. Load remaining core datasets: analysis, documents, prosandcons
    # Analysis
    a_start = time.time()
    df_ana_raw = pd.read_excel(CORE_DATASETS['analysis'], header=1)
    rows_in = len(df_ana_raw)
    df_ana = df_ana_raw.copy()
    df_ana['company_id'] = df_ana['company_id'].apply(normalize_ticker)
    df_ana = df_ana[df_ana['company_id'].isin(valid_companies)].copy()
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_ana.to_sql('analysis', conn, if_exists='append', index=False)
        conn.commit()
    rows_out = len(df_ana)
    audit_records.append({
        'table': 'analysis',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - a_start, 3)
    })

    # Documents
    d_start = time.time()
    df_doc_raw = pd.read_excel(CORE_DATASETS['documents'], header=1)
    rows_in = len(df_doc_raw)
    df_doc = df_doc_raw.copy()
    df_doc['company_id'] = df_doc['company_id'].apply(normalize_ticker)
    df_doc['Year'] = pd.to_numeric(df_doc['Year'], errors='coerce').fillna(2020).astype(int)
    df_doc = df_doc[df_doc['company_id'].isin(valid_companies)].copy()
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_doc.to_sql('documents', conn, if_exists='append', index=False)
        conn.commit()
    rows_out = len(df_doc)
    audit_records.append({
        'table': 'documents',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - d_start, 3)
    })

    # Pros and Cons
    pc_start = time.time()
    df_pc_raw = pd.read_excel(CORE_DATASETS['prosandcons'], header=1)
    rows_in = len(df_pc_raw)
    df_pc = df_pc_raw.copy()
    df_pc['company_id'] = df_pc['company_id'].apply(normalize_ticker)
    df_pc = df_pc[df_pc['company_id'].isin(valid_companies)].copy()
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_pc.to_sql('prosandcons', conn, if_exists='append', index=False)
        conn.commit()
    rows_out = len(df_pc)
    audit_records.append({
        'table': 'prosandcons',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - pc_start, 3)
    })

    # 4. Load Supplementary datasets: sectors, market_cap, peer_groups, stock_prices
    # Sectors
    sec_start = time.time()
    df_sec_raw = pd.read_excel(SUPPLEMENTARY_DATASETS['sectors'], header=0)
    rows_in = len(df_sec_raw)
    df_sec = df_sec_raw.copy()
    df_sec['company_id'] = df_sec['company_id'].apply(normalize_ticker)
    df_sec = df_sec[df_sec['company_id'].isin(valid_companies)].copy()
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_sec.to_sql('sectors', conn, if_exists='append', index=False)
        conn.commit()
    rows_out = len(df_sec)
    audit_records.append({
        'table': 'sectors',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - sec_start, 3)
    })

    # Market Cap
    mc_start = time.time()
    df_mc_raw = pd.read_excel(SUPPLEMENTARY_DATASETS['market_cap'], header=0)
    rows_in = len(df_mc_raw)
    df_mc = df_mc_raw.copy()
    df_mc['company_id'] = df_mc['company_id'].apply(normalize_ticker)
    df_mc['year'] = pd.to_numeric(df_mc['year'], errors='coerce').fillna(2020).astype(int)
    df_mc = df_mc[df_mc['company_id'].isin(valid_companies)].copy()
    df_mc = df_mc.drop_duplicates(subset=['company_id', 'year'], keep='last')
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_mc.to_sql('market_cap', conn, if_exists='append', index=False)
        conn.commit()
    rows_out = len(df_mc)
    audit_records.append({
        'table': 'market_cap',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - mc_start, 3)
    })

    # Peer Groups
    pg_start = time.time()
    df_pg_raw = pd.read_excel(SUPPLEMENTARY_DATASETS['peer_groups'], header=0)
    rows_in = len(df_pg_raw)
    df_pg = df_pg_raw.copy()
    df_pg['company_id'] = df_pg['company_id'].apply(normalize_ticker)
    df_pg = df_pg[df_pg['company_id'].isin(valid_companies)].copy()
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_pg.to_sql('peer_groups', conn, if_exists='append', index=False)
        conn.commit()
    rows_out = len(df_pg)
    audit_records.append({
        'table': 'peer_groups',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - pg_start, 3)
    })

    # Stock Prices
    sp_start = time.time()
    df_sp_raw = pd.read_excel(SUPPLEMENTARY_DATASETS['stock_prices'], header=0)
    rows_in = len(df_sp_raw)
    df_sp = df_sp_raw.copy()
    df_sp['company_id'] = df_sp['company_id'].apply(normalize_ticker)
    df_sp = df_sp[df_sp['company_id'].isin(valid_companies)].copy()
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_sp.to_sql('stock_prices', conn, if_exists='append', index=False)
        conn.commit()
    rows_out = len(df_sp)
    audit_records.append({
        'table': 'stock_prices',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - sp_start, 3)
    })

    # Financial Ratios (from supporting file)
    fr_start = time.time()
    df_fr_raw = pd.read_excel(SUPPLEMENTARY_DATASETS['financial_ratios'], header=0)
    rows_in = len(df_fr_raw)
    df_fr = df_fr_raw.copy()
    df_fr['company_id'] = df_fr['company_id'].apply(normalize_ticker)
    df_fr['year'] = df_fr['year'].apply(normalize_year)
    df_fr = df_fr[df_fr['company_id'].isin(valid_companies)].copy()
    df_fr = df_fr[df_fr['year'] != 'PARSE_ERROR'].copy()
    df_fr = df_fr.drop_duplicates(subset=['company_id', 'year'], keep='last')
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON;")
        df_fr.to_sql('financial_ratios', conn, if_exists='append', index=False)
        conn.commit()
    rows_out = len(df_fr)
    audit_records.append({
        'table': 'financial_ratios',
        'rows_in': rows_in,
        'rows_out': rows_out,
        'rejected': rows_in - rows_out,
        'timestamp': datetime.datetime.now().isoformat(),
        'runtime_s': round(time.time() - fr_start, 3)
    })
    logger.info(f"Loaded financial_ratios: {rows_out} records")

    # Write audit log & validation failures
    df_audit = pd.DataFrame(audit_records)
    df_audit.to_csv(os.path.join(OUTPUT_DIR, "load_audit.csv"), index=False)

    df_val = validator.get_failures_df()
    df_val.to_csv(os.path.join(OUTPUT_DIR, "validation_failures.csv"), index=False)

    # Write parse_failures.csv for unparseable raw values
    parse_fails = df_val[df_val['issue'].str.contains("Invalid year format", na=False)]
    if not parse_fails.empty:
        df_pf = parse_fails[['company_id', 'year', 'field', 'issue']].copy()
        df_pf.to_csv(os.path.join(OUTPUT_DIR, "parse_failures.csv"), index=False)
    else:
        pd.DataFrame(columns=['company_id', 'year', 'field', 'issue']).to_csv(
            os.path.join(OUTPUT_DIR, "parse_failures.csv"), index=False
        )

    # Verify foreign key integrity
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_check;")
        fk_errors = cursor.fetchall()
        if fk_errors:
            logger.error(f"Foreign key violations found: {fk_errors}")
        else:
            logger.info("PRAGMA foreign_key_check passed with 0 errors!")

    logger.info(f"ETL completed in {round(time.time() - start_time, 2)} seconds.")
    return df_audit, df_val

if __name__ == "__main__":
    load_all_data()
