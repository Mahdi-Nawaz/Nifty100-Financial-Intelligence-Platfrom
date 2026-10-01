"""Unit tests for the Monte Carlo DCF Valuation Engine."""
import pytest
from src.analytics.monte_carlo_dcf import run_monte_carlo_dcf

def test_single_company_monte_carlo():
    """Verify stochastic Monte Carlo returns valid distributions and bounds."""
    res = run_monte_carlo_dcf("TCS", n_simulations=1000)
    assert res["company_id"] == "TCS"
    assert res["median_fair_value"] > 0
    assert res["bear_case_p10"] <= res["base_case_p50"] <= res["bull_case_p90"]
    assert 0.0 <= res["prob_undervalued_pct"] <= 100.0
    assert "verdict" in res
