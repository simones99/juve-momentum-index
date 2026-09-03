"""Pre-match outcome probabilities, built on top of the existing Elo model.

Elo's classic `expected_score()` (see elo.py) returns a single number in
(0, 1): the expected POINTS SHARE for the home side (win=1, draw=0.5,
loss=0). It does not, by itself, split a match into separate win/draw/loss
probabilities.

This module adds a small, explicit heuristic on top of it: draw
probability is modeled as peaking when the two sides are evenly matched
and decaying as the Elo gap widens, then the remaining probability mass is
split between win/loss in proportion to the classic expected score.

DRAW_PEAK_PROBABILITY and DRAW_DECAY_SCALE were backtested with
scripts/backtest_win_probability.py against 6 seasons (2019-20 to 2024-25,
228 matches) of Juventus' actual Serie A results, scored the way a
probabilistic classifier would be (log loss, Brier score, accuracy)
against a uniform baseline and a "predict the training set's W/D/L
frequencies" baseline, using leave-one-season-out cross-validation.

Findings from that backtest (see the script for full output):
  - Blindly grid-searching BOTH constants per fold overfits on ~190
    matches/fold and does not reliably beat the frequency baseline.
  - A single, isolated change - widening DRAW_DECAY_SCALE from 200 to 400
    while leaving DRAW_PEAK_PROBABILITY unchanged - beat every other
    variant (uniform, frequency baseline, unmodified defaults, and full
    per-fold tuning) on mean cross-validated log loss, with the lowest
    variance across folds. That is the one change kept here.
  - Even so, the model's edge over the naive frequency baseline is small
    on this dataset (228 matches, one dominant club) - this remains a
    simplified heuristic, not a rigorously calibrated forecasting model.
"""

import math

from app.features.elo import HOME_ADVANTAGE, expected_score

DRAW_PEAK_PROBABILITY = 0.28  # P(draw) when both sides have identical (home-adjusted) ratings
DRAW_DECAY_SCALE = 400.0  # Elo points; draw probability decays as a Gaussian in the rating gap


def estimate_draw_probability(rating_diff: float, scale: float = DRAW_DECAY_SCALE) -> float:
    return DRAW_PEAK_PROBABILITY * math.exp(-0.5 * (rating_diff / scale) ** 2)


def estimate_match_probabilities(
    rating_home: float, rating_away: float, home_advantage: float = HOME_ADVANTAGE
) -> dict[str, float]:
    """Returns {"home": P(home win), "draw": P(draw), "away": P(away win)},
    each in [0, 1], summing to 1.0. `rating_home`/`rating_away` are current
    (pre-match) Elo ratings; home advantage is applied internally.
    """
    adjusted_home = rating_home + home_advantage
    home_win_share = expected_score(adjusted_home, rating_away)
    draw = estimate_draw_probability(adjusted_home - rating_away)
    return {
        "home": home_win_share * (1 - draw),
        "draw": draw,
        "away": (1 - home_win_share) * (1 - draw),
    }
