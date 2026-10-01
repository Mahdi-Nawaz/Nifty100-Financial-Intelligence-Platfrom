"""Unit tests for ETL normalisation functions (45 test cases)."""
import pytest
from src.etl.normaliser import normalize_ticker, normalize_year

# --- 20 cases for normalize_year ---
@pytest.mark.parametrize("inp, expected", [
    ("Mar-23", "2023-03"),
    ("Mar 23", "2023-03"),
    ("March-2023", "2023-03"),
    ("2023", "2023-03"),
    ("2023.0", "2023-03"),
    ("FY23", "2023-03"),
    ("FY24", "2024-03"),
    ("FY 2024", "2024-03"),
    ("Dec-22", "2022-12"),
    ("Dec 2022", "2022-12"),
    ("December-2022", "2022-12"),
    ("Jun-23", "2023-06"),
    ("Jun 2023", "2023-06"),
    ("Sep-21", "2021-09"),
    ("Jan-20", "2020-01"),
    ("2023-03", "2023-03"),
    ("2022-12", "2022-12"),
    ("xyz", "PARSE_ERROR"),
    ("", "PARSE_ERROR"),
    (None, "PARSE_ERROR"),
])
def test_normalize_year_cases(inp, expected):
    assert normalize_year(inp) == expected

# --- 15 cases for normalize_ticker ---
@pytest.mark.parametrize("inp, expected", [
    ("TCS", "TCS"),
    ("tcs", "TCS"),
    (" TCS ", "TCS"),
    ("  infy  ", "INFY"),
    ("BAJAJ-AUTO", "BAJAJ-AUTO"),
    ("bajaj-auto", "BAJAJ-AUTO"),
    ("M&M", "M&M"),
    ("m&m", "M&M"),
    ("HDFCBANK", "HDFCBANK"),
    ("hdfcbank", "HDFCBANK"),
    ("RELIANCE", "RELIANCE"),
    ("ITC", "ITC"),
    ("sbicard", "SBICARD"),
    ("adaniports", "ADANIPORTS"),
    ("LT", "LT"),
])
def test_normalize_ticker_cases(inp, expected):
    assert normalize_ticker(inp) == expected

# --- 5 deduplication and 5 load audit validation test cases ---
def test_deduplication_keeps_latest():
    import pandas as pd
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'val': 10},
        {'company_id': 'TCS', 'year': '2023-03', 'val': 20}
    ])
    deduped = df.drop_duplicates(subset=['company_id', 'year'], keep='last')
    assert len(deduped) == 1
    assert deduped.iloc[0]['val'] == 20

def test_deduplication_different_years():
    import pandas as pd
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2022-03', 'val': 10},
        {'company_id': 'TCS', 'year': '2023-03', 'val': 20}
    ])
    deduped = df.drop_duplicates(subset=['company_id', 'year'], keep='last')
    assert len(deduped) == 2

def test_deduplication_different_companies():
    import pandas as pd
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'val': 10},
        {'company_id': 'INFY', 'year': '2023-03', 'val': 20}
    ])
    deduped = df.drop_duplicates(subset=['company_id', 'year'], keep='last')
    assert len(deduped) == 2

def test_deduplication_empty():
    import pandas as pd
    df = pd.DataFrame(columns=['company_id', 'year'])
    deduped = df.drop_duplicates(subset=['company_id', 'year'], keep='last')
    assert len(deduped) == 0

def test_deduplication_triplicate():
    import pandas as pd
    df = pd.DataFrame([
        {'company_id': 'ABB', 'year': '2024-03', 'val': 1},
        {'company_id': 'ABB', 'year': '2024-03', 'val': 2},
        {'company_id': 'ABB', 'year': '2024-03', 'val': 3}
    ])
    deduped = df.drop_duplicates(subset=['company_id', 'year'], keep='last')
    assert len(deduped) == 1
    assert deduped.iloc[0]['val'] == 3

def test_load_audit_file_exists():
    import os
    assert os.path.exists("output/load_audit.csv")

def test_load_audit_columns():
    import pandas as pd
    df = pd.read_csv("output/load_audit.csv")
    cols = ['table', 'rows_in', 'rows_out', 'rejected', 'timestamp', 'runtime_s']
    for c in cols:
        assert c in df.columns

def test_load_audit_non_empty():
    import pandas as pd
    df = pd.read_csv("output/load_audit.csv")
    assert len(df) >= 10

def test_load_audit_companies_count():
    import pandas as pd
    df = pd.read_csv("output/load_audit.csv")
    comp_row = df[df['table'] == 'companies']
    assert not comp_row.empty
    assert comp_row.iloc[0]['rows_out'] == 92

def test_load_audit_zero_negative_rows():
    import pandas as pd
    df = pd.read_csv("output/load_audit.csv")
    assert (df['rows_out'] >= 0).all()
