import pytest

from app.features.win_probability import (
    estimate_draw_probability,
    estimate_match_probabilities,
)


def test_probabilities_sum_to_one():
    probs = estimate_match_probabilities(1500, 1500)
    assert probs["home"] + probs["draw"] + probs["away"] == pytest.approx(1.0)


def test_equal_ratings_favor_home_via_home_advantage():
    probs = estimate_match_probabilities(1500, 1500)
    assert probs["home"] > probs["away"]


def test_draw_probability_peaks_at_zero_diff():
    assert estimate_draw_probability(0) == pytest.approx(0.28)
    assert estimate_draw_probability(200) < estimate_draw_probability(0)
    assert estimate_draw_probability(-200) == pytest.approx(estimate_draw_probability(200))


def test_large_rating_gap_favors_stronger_side_and_shrinks_draw():
    even_draw = estimate_match_probabilities(1500, 1500)["draw"]
    probs = estimate_match_probabilities(1800, 1400)
    assert probs["home"] > 0.7
    assert probs["home"] > probs["away"] + probs["draw"]
    assert probs["draw"] < even_draw


def test_underdog_at_home_can_still_be_disfavored():
    probs = estimate_match_probabilities(1400, 1800)
    assert probs["away"] > probs["home"]


def test_probabilities_always_in_unit_range():
    for home, away in [(1500, 1500), (1000, 2000), (2000, 1000), (1500, 1499)]:
        probs = estimate_match_probabilities(home, away)
        for value in probs.values():
            assert 0.0 <= value <= 1.0
