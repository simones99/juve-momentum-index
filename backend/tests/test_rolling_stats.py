import math

import pandas as pd
import pytest

from app.features.rolling_stats import match_points, rolling_goal_diff, rolling_points


def make_df():
    # Chronological Juve results: W, W, D, L, W
    return pd.DataFrame(
        {
            "result": ["W", "W", "D", "L", "W"],
            "goals_for": [2, 3, 1, 0, 2],
            "goals_against": [0, 1, 1, 2, 1],
        }
    )


def test_match_points_mapping():
    assert match_points("W") == 3
    assert match_points("D") == 1
    assert match_points("L") == 0


def test_rolling_points_first_match_has_no_history():
    df = make_df()
    result = rolling_points(df, window=5)
    assert math.isnan(result.iloc[0])


def test_rolling_points_reflects_prior_matches_only_no_leakage():
    df = make_df()
    result = rolling_points(df, window=5)
    # Before match index 2 (D), prior results are [W, W] -> points [3, 3] -> mean 3
    assert result.iloc[2] == pytest.approx(3.0)
    # Before match index 3 (L), prior results are [W, W, D] -> points [3, 3, 1] -> mean 7/3
    assert result.iloc[3] == pytest.approx(7 / 3)
    # Before match index 4 (W), prior results are [W, W, D, L] -> points [3, 3, 1, 0] -> mean 7/4
    assert result.iloc[4] == pytest.approx(7 / 4)


def test_rolling_points_window_limits_lookback():
    df = make_df()
    result = rolling_points(df, window=2)
    # Before match index 3, window=2 -> only prior 2 matches [W, D] -> points [3, 1] -> mean 2
    assert result.iloc[3] == pytest.approx(2.0)


def test_rolling_goal_diff_no_leakage():
    df = make_df()
    result = rolling_goal_diff(df, window=5)
    assert math.isnan(result.iloc[0])
    # Before match index 2, prior diffs = [2-0, 3-1] = [2, 2] -> mean 2
    assert result.iloc[2] == pytest.approx(2.0)
