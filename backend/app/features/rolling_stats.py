"""Rolling form stats for Juventus matches.

Both rolling series use `.shift(1)` before `.rolling(...)`: the value attached
to a given match reflects form GOING INTO that match, not including its own
result. This avoids leaking the match's own outcome into its own momentum
snapshot.
"""

import pandas as pd

RESULT_POINTS = {"W": 3, "D": 1, "L": 0}


def match_points(result: str) -> int:
    return RESULT_POINTS[result]


def rolling_points(df: pd.DataFrame, window: int) -> pd.Series:
    points = df["result"].map(match_points)
    return points.shift(1).rolling(window, min_periods=1).mean()


def rolling_goal_diff(df: pd.DataFrame, window: int) -> pd.Series:
    diff = df["goals_for"] - df["goals_against"]
    return diff.shift(1).rolling(window, min_periods=1).mean()
