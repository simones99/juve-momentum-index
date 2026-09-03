"""Momentum Index: a single 0-100 score blending Elo trend and recent form.

    momentum_index = 0.5 * elo_normalized + 0.25 * points_norm + 0.25 * goal_diff_norm

Deviation from docs/legacy-mvp-plan.md: the original formula weighted a 0-100
elo_normalized value against raw points-per-game (0-3) and raw goal difference
(unbounded), which are on incompatible scales and would let Elo dominate the
index almost entirely. Here points_rolling5 and goal_diff_rolling5 are also
min-max normalized to 0-100 before the weights are applied, keeping the
original 0.5/0.25/0.25 intent while making the three components comparable.
"""

import pandas as pd

from app.features.rolling_stats import rolling_goal_diff, rolling_points

ELO_WEIGHT = 0.5
POINTS_WEIGHT = 0.25
GOAL_DIFF_WEIGHT = 0.25

NEUTRAL_SCORE = 50.0


def normalize_min_max(series: pd.Series) -> pd.Series:
    """Min-max scales a series to 0-100. NaN inputs stay NaN. A degenerate
    series (all-equal or all-NaN) maps to a flat neutral score rather than
    dividing by zero."""
    min_v, max_v = series.min(), series.max()
    if pd.isna(min_v) or pd.isna(max_v) or max_v == min_v:
        return pd.Series([NEUTRAL_SCORE] * len(series), index=series.index)
    return (series - min_v) / (max_v - min_v) * 100.0


def compute_momentum_index(
    elo_norm: pd.Series, points_norm: pd.Series, goal_diff_norm: pd.Series
) -> pd.Series:
    return ELO_WEIGHT * elo_norm + POINTS_WEIGHT * points_norm + GOAL_DIFF_WEIGHT * goal_diff_norm


def compute_momentum_series(df: pd.DataFrame) -> pd.DataFrame:
    """Takes a Juventus-only match DataFrame sorted chronologically ascending,
    with columns: match_date, elo_after, result, goals_for, goals_against.
    Returns a copy with elo_normalized, points_rolling5/10, goal_diff_rolling5/10
    and momentum_index columns added.
    """
    # kind="stable" preserves the input row order for ties on match_date
    # (e.g. Wikipedia-sourced matches sharing a season-start placeholder
    # date) — pandas' default quicksort is not guaranteed stable, which
    # would otherwise reorder same-date rows non-deterministically between
    # runs even though the caller already hands them in a deterministic
    # (match_date, match_id) order.
    df = df.sort_values("match_date", kind="stable").reset_index(drop=True).copy()

    df["elo_normalized"] = normalize_min_max(df["elo_after"])
    df["points_rolling5"] = rolling_points(df, 5)
    df["points_rolling10"] = rolling_points(df, 10)
    df["goal_diff_rolling5"] = rolling_goal_diff(df, 5)
    df["goal_diff_rolling10"] = rolling_goal_diff(df, 10)

    # Only the very first match(es) lack rolling history; treat that gap as
    # neutral so momentum_index can stay NOT NULL for every match.
    points_norm = normalize_min_max(df["points_rolling5"]).fillna(NEUTRAL_SCORE)
    goal_diff_norm = normalize_min_max(df["goal_diff_rolling5"]).fillna(NEUTRAL_SCORE)

    df["momentum_index"] = compute_momentum_index(df["elo_normalized"], points_norm, goal_diff_norm)
    return df
