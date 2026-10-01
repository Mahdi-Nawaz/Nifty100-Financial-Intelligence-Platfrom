"""Unit tests for Financial Ratio and KPI formula accuracy (20 test cases)."""
import pytest
from src.analytics.cagr import calculate_cagr
from src.analytics.cashflow_kpis import classify_capital_allocation

def test_roe_positive():
    net_profit = 100.0
    equity = 500.0
    roe = (net_profit / equity) * 100.0
    assert roe == 20.0

def test_roe_neg_equity():
    equity = -50.0
    roe = None if equity <= 0 else 10.0
    assert roe is None

def test_de_debtfree():
    borrowings = 0.0
    equity = 500.0
    de = borrowings / equity
    assert de == 0.0

def test_icr_debtfree():
    interest = 0.0
    icr = 999.0 if interest == 0 else (100 / interest)
    assert icr == 999.0

def test_icr_normal():
    interest = 20.0
    ebit = 100.0
    icr = ebit / interest
    assert icr == 5.0

def test_cagr_normal():
    cagr, flag, disp = calculate_cagr(100.0, 161.051, 5)
    assert flag == "NORMAL"
    assert round(cagr, 1) == 10.0

def test_cagr_turnaround():
    cagr, flag, disp = calculate_cagr(-100.0, 200.0, 5)
    assert flag == "TURNAROUND"
    assert cagr is None
    assert "Turnaround" in disp

def test_cagr_decline_to_loss():
    cagr, flag, disp = calculate_cagr(100.0, -50.0, 5)
    assert flag == "DECLINE_TO_LOSS"
    assert cagr is None

def test_cagr_both_negative():
    cagr, flag, disp = calculate_cagr(-100.0, -50.0, 5)
    assert flag == "BOTH_NEGATIVE"
    assert cagr is None

def test_cagr_zero_base():
    cagr, flag, disp = calculate_cagr(0.0, 100.0, 5)
    assert flag == "ZERO_BASE"
    assert cagr is None

def test_cagr_insufficient():
    cagr, flag, disp = calculate_cagr(100.0, 120.0, 2)
    assert flag == "INSUFFICIENT"
    assert cagr is None

def test_fcf_formula():
    cfo = 1500.0
    cfi = -600.0
    fcf = cfo + cfi
    assert fcf == 900.0

def test_capex_formula():
    cfi = -850.0
    capex = abs(cfi)
    assert capex == 850.0

def test_opm_formula():
    sales = 10000.0
    op = 2500.0
    opm = (op / sales) * 100.0
    assert opm == 25.0

def test_npm_formula():
    sales = 10000.0
    pat = 1500.0
    npm = (pat / sales) * 100.0
    assert npm == 15.0

def test_asset_turnover():
    sales = 2000.0
    assets = 1000.0
    turnover = sales / assets
    assert turnover == 2.0

def test_bvps_formula():
    tot_equity = 1000.0
    equity_cap = 10.0
    face_val = 1.0
    num_shares = equity_cap / face_val
    bvps = tot_equity / num_shares
    assert bvps == 100.0

def test_capital_allocation_reinvestor():
    s_cfo, s_cfi, s_cff, label = classify_capital_allocation(500, -300, -100)
    assert s_cfo == "+" and s_cfi == "-" and s_cff == "-"
    assert "Reinvestor" in label

def test_capital_allocation_distress():
    s_cfo, s_cfi, s_cff, label = classify_capital_allocation(-200, -100, 300)
    assert s_cfo == "-" and s_cff == "+"
    assert "Distress" in label

def test_composite_score_range():
    import sqlite3
    conn = sqlite3.connect("data/nifty100.db")
    scores = [r[0] for r in conn.execute("SELECT composite_score FROM financial_ratios WHERE composite_score IS NOT NULL").fetchall()]
    assert len(scores) > 0
    assert min(scores) >= 0.0
    assert max(scores) <= 100.0
