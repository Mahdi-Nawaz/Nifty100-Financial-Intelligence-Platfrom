"""API endpoint integration test suite (10 test cases)."""
import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_200():
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "db_row_counts" in data
    assert data["db_row_counts"]["companies"] == 92

def test_companies_count():
    resp = client.get("/api/v1/companies")
    assert resp.status_code == 200
    cos = resp.json()
    assert len(cos) == 92

def test_companies_search():
    resp = client.get("/api/v1/companies?search=TCS")
    assert resp.status_code == 200
    cos = resp.json()
    assert any(c["id"] == "TCS" for c in cos)

def test_company_profile():
    resp = client.get("/api/v1/companies/TCS")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "TCS"
    assert "Tata Consultancy Services" in data["company_name"]
    assert "broad_sector" in data

def test_invalid_ticker():
    resp = client.get("/api/v1/companies/INVALID_XYZ_999")
    assert resp.status_code == 404

def test_company_ratios_ten_years():
    resp = client.get("/api/v1/companies/TCS/ratios")
    assert resp.status_code == 200
    ratios = resp.json()
    assert len(ratios) >= 10

def test_company_pl_history():
    resp = client.get("/api/v1/companies/TCS/pl")
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) >= 10
    assert "sales" in rows[0]

def test_screener_filter_roe():
    resp = client.get("/api/v1/screener?min_roe=15")
    assert resp.status_code == 200
    matches = resp.json()
    assert len(matches) > 0
    assert all(m["return_on_equity_pct"] >= 15.0 for m in matches if m["return_on_equity_pct"] is not None)

def test_sectors_list():
    resp = client.get("/api/v1/sectors")
    assert resp.status_code == 200
    sectors = resp.json()
    assert len(sectors) >= 10
    assert any(s["broad_sector"] == "Financials" for s in sectors)

def test_portfolio_stats():
    resp = client.get("/api/v1/portfolio/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert len(stats) >= 5
    assert "Metric" in stats[0]
