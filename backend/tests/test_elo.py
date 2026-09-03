import pytest

from app.features.elo import (
    INITIAL_ELO,
    K_FACTOR,
    compute_elo_history,
    expected_score,
    update_elo,
)


def test_expected_score_equal_ratings_is_fifty_fifty():
    assert expected_score(1500, 1500) == pytest.approx(0.5)


def test_expected_score_higher_rating_favored():
    assert expected_score(1600, 1400) > 0.5
    assert expected_score(1400, 1600) < 0.5


def test_update_elo_home_win_matches_hand_computation():
    # rating_home=1500, rating_away=1500, home advantage=65 -> expected_home = expected_score(1565, 1500)
    expected_home = expected_score(1565, 1500)
    new_home, new_away = update_elo(1500, 1500, home_goals=2, away_goals=0, k=K_FACTOR)
    expected_new_home = 1500 + K_FACTOR * (1.0 - expected_home)
    expected_new_away = 1500 - K_FACTOR * (1.0 - expected_home)
    assert new_home == pytest.approx(expected_new_home)
    assert new_away == pytest.approx(expected_new_away)
    assert new_home > 1500
    assert new_away < 1500


def test_update_elo_draw_keeps_ratings_close_but_not_necessarily_equal():
    # equal pre-match ratings + home advantage means a draw is a slight
    # over-performance for the away side, so away should gain rating.
    new_home, new_away = update_elo(1500, 1500, home_goals=1, away_goals=1)
    assert new_away > 1500
    assert new_home < 1500


def test_update_elo_draw_with_no_home_advantage_leaves_ratings_unchanged():
    from app.features import elo as elo_module

    original_home_advantage = elo_module.HOME_ADVANTAGE
    elo_module.HOME_ADVANTAGE = 0.0
    try:
        new_home, new_away = update_elo(1500, 1500, home_goals=1, away_goals=1)
        assert new_home == pytest.approx(1500)
        assert new_away == pytest.approx(1500)
    finally:
        elo_module.HOME_ADVANTAGE = original_home_advantage


def test_compute_elo_history_new_team_starts_at_initial_elo():
    matches = [
        {"match_id": 1, "home_team": "Juventus", "away_team": "Inter", "home_goals": 1, "away_goals": 0},
    ]
    points = compute_elo_history(matches)
    juve_point = next(p for p in points if p.team == "Juventus")
    inter_point = next(p for p in points if p.team == "Inter")
    assert juve_point.elo_before == INITIAL_ELO
    assert inter_point.elo_before == INITIAL_ELO
    assert juve_point.elo_after > INITIAL_ELO
    assert inter_point.elo_after < INITIAL_ELO


def test_compute_elo_history_carries_rating_across_matches():
    matches = [
        {"match_id": 1, "home_team": "Juventus", "away_team": "Inter", "home_goals": 2, "away_goals": 0},
        {"match_id": 2, "home_team": "Milan", "away_team": "Juventus", "home_goals": 0, "away_goals": 1},
    ]
    points = compute_elo_history(matches)
    juve_match2 = next(p for p in points if p.team == "Juventus" and p.match_id == 2)
    juve_match1 = next(p for p in points if p.team == "Juventus" and p.match_id == 1)
    assert juve_match2.elo_before == juve_match1.elo_after


def test_compute_elo_history_skips_unplayed_fixtures():
    matches = [
        {"match_id": 1, "home_team": "Juventus", "away_team": "Inter", "home_goals": None, "away_goals": None},
    ]
    assert compute_elo_history(matches) == []
