"""Unit tests for the Quantitative Portfolio Backtesting Engine."""
import os
import pytest
import pandas as pd
from src.analytics.backtester import run_strategy_backtest, run_all_presets_backtest

def test_single_preset_backtest():
    """Verify single preset backtest returns complete risk-adjusted KPI suite."""
    res = run_strategy_backtest("quality_compounder", top_k=5)
    assert "portfolio_cagr_pct" in res
    assert "benchmark_cagr_pct" in res
    assert "alpha_pct" in res
    assert "sharpe_ratio" in res
    assert "sortino_ratio" in res
    assert "max_drawdown_pct" in res
    assert len(res["yearly_breakdown"]) > 0

def test_backtest_leaderboard():
    """Verify comparative leaderboard generation across all presets."""
    df = run_all_presets_backtest()
    assert isinstance(df, pd.DataFrame)
    assert len(df) >= 5
    assert "Alpha (%)" in df.columns
    assert "Sharpe Ratio" in df.columns
    assert os.path.exists("output/backtest_leaderboard.csv")
