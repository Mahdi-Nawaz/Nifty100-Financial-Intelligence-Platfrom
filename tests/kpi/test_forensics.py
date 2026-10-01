"""Unit and verification tests for Forensic Accounting Suite (Beneish M, Altman Z, Piotroski F)."""
import os
import sqlite3
import pytest
import pandas as pd
from src.analytics.forensics import compute_forensic_scores

DB_PATH = "data/nifty100.db"

@pytest.fixture(scope="module")
def forensic_df():
    """Load or compute forensic scores once for testing."""
    return compute_forensic_scores(DB_PATH)

def test_forensic_universe_coverage(forensic_df):
    """Ensure all 92 companies have forensic ratings."""
    assert len(forensic_df) == 92
    assert "beneish_m_score" in forensic_df.columns
    assert "altman_z_score" in forensic_df.columns
    assert "piotroski_f_score" in forensic_df.columns

def test_piotroski_score_bounds(forensic_df):
    """Piotroski F-score must be an integer between 0 and 9."""
    assert forensic_df["piotroski_f_score"].min() >= 0
    assert forensic_df["piotroski_f_score"].max() <= 9
    assert all(forensic_df["piotroski_f_score"].apply(lambda x: isinstance(x, (int, float))))

def test_altman_zones(forensic_df):
    """Verify Altman Z zones are properly classified."""
    valid_zones = {"Safe Zone", "Grey Zone", "Distress Zone", "Financial (Z-Score N/A)"}
    unique_zones = set(forensic_df["altman_zone"].unique())
    assert unique_zones.issubset(valid_zones)

def test_beneish_flags(forensic_df):
    """Verify Beneish M flags contain Low Risk or High Risk."""
    valid_flags = {"Low Risk (Unlikely Manipulation)", "High Risk (Potential Manipulation)"}
    unique_flags = set(forensic_df["beneish_flag"].unique())
    assert unique_flags.issubset(valid_flags)

def test_sqlite_forensic_table_persisted():
    """Verify the forensic_audit table exists and can be queried directly from SQLite."""
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query("SELECT COUNT(*) as cnt FROM forensic_audit", conn)
        assert df["cnt"].iloc[0] == 92
