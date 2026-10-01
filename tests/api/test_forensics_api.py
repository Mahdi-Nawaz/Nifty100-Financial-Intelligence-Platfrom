"""Tests for new forensic, backtest, and Monte Carlo DCF API endpoints."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_api_forensics_ticker():
    """Verify company forensic audit endpoint returns scores."""
    resp = client.get("/api/v1/forensics/TCS")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == "TCS"
    assert "beneish_m_score" in data
    assert "altman_z_score" in data
    assert "piotroski_f_score" in data

def test_api_forensics_summary():
    """Verify forensic summary returns all companies."""
    resp = client.get("/api/v1/forensics/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 90

def test_api_backtest():
    """Verify quantitative strategy backtest endpoint."""
    resp = client.get("/api/v1/backtest/quality_compounder?top_k=5")
    assert resp.status_code == 200
    data = resp.json()
    assert "portfolio_cagr_pct" in data
    assert "benchmark_cagr_pct" in data
    assert "sharpe_ratio" in data

def test_api_monte_carlo():
    """Verify Monte Carlo DCF endpoint."""
    resp = client.get("/api/v1/valuation/TCS/monte-carlo?simulations=500")
    assert resp.status_code == 200
    data = resp.json()
    assert data["company_id"] == "TCS"
    assert "median_fair_value" in data
    assert "prob_undervalued_pct" in data
