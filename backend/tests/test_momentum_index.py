import pandas as pd
import pytest

from app.features.momentum_index import (
    NEUTRAL_SCORE,
    compute_momentum_index,
    compute_momentum_series,
    normalize_min_max,
)


def test_normalize_min_max_scales_to_zero_hundred():
    series = pd.Series([1500, 1520, 1550, 1500])
    normalized = normalize_min_max(series)
    assert normalized.min() == pytest.approx(0.0)
    assert normalized.max() == pytest.approx(100.0)


def test_normalize_min_max_degenerate_series_returns_neutral():
    series = pd.Series([1500.0, 1500.0, 1500.0])
    normalized = normalize_min_max(series)
    assert (normalized == NEUTRAL_SCORE).all()


def test_compute_momentum_index_weighted_formula():
    elo_norm = pd.Series([100.0])
    points_norm = pd.Series([0.0])
    goal_diff_norm = pd.Series([0.0])
    result = compute_momentum_index(elo_norm, points_norm, goal_diff_norm)
    # 0.5*100 + 0.25*0 + 0.25*0 = 50
    assert result.iloc[0] == pytest.approx(50.0)


def test_compute_momentum_index_all_components_max():
    elo_norm = pd.Series([100.0])
    points_norm = pd.Series([100.0])
    goal_diff_norm = pd.Series([100.0])
    result = compute_momentum_index(elo_norm, points_norm, goal_diff_norm)
    assert result.iloc[0] == pytest.approx(100.0)


def test_compute_momentum_series_first_match_is_not_null():
    df = pd.DataFrame(
        {
            "match_date": pd.to_datetime(["2024-08-01"]),
            "elo_after": [1510.0],
            "result": ["W"],
            "goals_for": [2],
            "goals_against": [0],
        }
    )
    out = compute_momentum_series(df)
    assert pd.notna(out["momentum_index"].iloc[0])
    assert pd.isna(out["points_rolling5"].iloc[0])  # raw rolling stays null, no history yet


def test_compute_momentum_series_full_sequence():
    df = pd.DataFrame(
        {
            "match_date": pd.to_datetime(
                ["2024-08-01", "2024-08-08", "2024-08-15", "2024-08-22", "2024-08-29"]
            ),
            "elo_after": [1510.0, 1525.0, 1520.0, 1500.0, 1515.0],
            "result": ["W", "W", "D", "L", "W"],
            "goals_for": [2, 3, 1, 0, 2],
            "goals_against": [0, 1, 1, 2, 1],
        }
    )
    out = compute_momentum_series(df)
    assert len(out) == 5
    assert out["momentum_index"].between(0, 100).all()
    assert out["elo_normalized"].iloc[out["elo_after"].idxmax()] == pytest.approx(100.0)
    assert out["elo_normalized"].iloc[out["elo_after"].idxmin()] == pytest.approx(0.0)
