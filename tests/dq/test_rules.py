"""Tests for Data Quality (DQ) validation rules (14 test cases)."""
import pytest
import pandas as pd
from src.etl.validator import DQValidator

def test_dq01_company_pk_uniqueness():
    v = DQValidator()
    df = pd.DataFrame([
        {'id': 'TCS', 'company_name': 'TCS Ltd'},
        {'id': 'TCS', 'company_name': 'TCS Ltd'}
    ])
    res = v.validate_companies(df)
    assert len(res) == 1
    assert any(f['issue'].startswith("Duplicate company ticker") for f in v.failures)

def test_dq02_annual_pk_uniqueness():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'sales': 100},
        {'company_id': 'TCS', 'year': '2023-03', 'sales': 110}
    ])
    res = v.validate_pl(df, {'TCS'})
    assert len(res) == 1
    assert any("Duplicate annual record in P&L" in f['issue'] for f in v.failures)

def test_dq03_fk_integrity():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'UNKNOWN_CO', 'year': '2023-03', 'sales': 100}
    ])
    res = v.validate_pl(df, {'TCS'})
    assert len(res) == 0
    assert any("Foreign key constraint failure" in f['issue'] for f in v.failures)

def test_dq04_bs_balance():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'total_assets': 1000, 'total_liabilities': 1050}
    ])
    v.validate_bs(df, {'TCS'})
    assert any("Balance sheet discrepancy" in f['issue'] for f in v.failures)

def test_dq05_opm_cross_check():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'sales': 100, 'operating_profit': 20, 'opm_percentage': 25.0}
    ])
    v.validate_pl(df, {'TCS'})
    assert any("OPM divergence" in f['issue'] for f in v.failures)

def test_dq06_positive_sales():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'sales': -50}
    ])
    v.validate_pl(df, {'TCS'})
    assert any("Sales non-positive" in f['issue'] for f in v.failures)

def test_dq07_year_format():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023/March', 'sales': 100}
    ])
    res = v.validate_pl(df, {'TCS'})
    assert len(res) == 0
    assert any("Invalid year format" in f['issue'] for f in v.failures)

def test_dq08_ticker_format():
    v = DQValidator()
    df = pd.DataFrame([
        {'id': 'TOOLONGTICKERNAMEFORNSE', 'company_name': 'Test Corp'}
    ])
    res = v.validate_companies(df)
    assert len(res) == 0
    assert any("Invalid ticker format/length" in f['issue'] for f in v.failures)

def test_dq09_net_cash_check():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'operating_activity': 100, 'investing_activity': -50, 'financing_activity': -30, 'net_cash_flow': 50}
    ])
    v.validate_cf(df, {'TCS'})
    assert any("Net cash divergence" in f['issue'] for f in v.failures)

def test_dq10_non_negative_fixed_assets():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'fixed_assets': -10}
    ])
    res = v.validate_bs(df, {'TCS'})
    assert res.iloc[0]['fixed_assets'] == 0
    assert any("Negative fixed assets" in f['issue'] for f in v.failures)

def test_dq11_tax_rate_range():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'tax_percentage': 75.0}
    ])
    v.validate_pl(df, {'TCS'})
    assert any("Tax percentage outside 0-60%" in f['issue'] for f in v.failures)

def test_dq12_dividend_payout_cap():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'dividend_payout': 250.0}
    ])
    v.validate_pl(df, {'TCS'})
    assert any("Dividend payout > 200%" in f['issue'] for f in v.failures)

def test_dq14_eps_sign_consistency():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'TCS', 'year': '2023-03', 'net_profit': 1000, 'eps': -5.0}
    ])
    v.validate_pl(df, {'TCS'})
    assert any("EPS negative or zero while Net Profit is positive" in f['issue'] for f in v.failures)

def test_dq16_coverage_check():
    v = DQValidator()
    df = pd.DataFrame([
        {'company_id': 'NEWCO', 'year': '2023-03', 'sales': 100}
    ])
    v.check_coverage(df, {'NEWCO'})
    assert any("Company has only 1 years of records" in f['issue'] for f in v.failures)
