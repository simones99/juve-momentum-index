"""Elo rating calculation.

Ratings are computed over every ingested match (the full Serie A and
Champions League schedules for the ingested seasons, not only Juventus'
fixtures; see app/ingestion/ingest.py), in chronological order.

Limitations, also listed in the README:
  - Every team starts from INITIAL_ELO at its first appearance in the
    ingested window; there is no prior history before the first season.
  - Constant K, outcome-only updates (no goal-margin multiplier) and no
    regression towards the mean between seasons.
  - Non-Italian Champions League clubs only appear in CL matches, so their
    ratings rest on few games and are not comparable to domestic ratings.
"""

from dataclasses import dataclass

INITIAL_ELO = 1500.0
K_FACTOR = 20.0
HOME_ADVANTAGE = 65.0


def expected_score(rating_a: float, rating_b: float) -> float:
    """Probability that side A beats side B, given their (already home-adjusted) ratings."""
    return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400.0))


def match_outcome_score(goals_a: int, goals_b: int) -> float:
    if goals_a > goals_b:
        return 1.0
    if goals_a < goals_b:
        return 0.0
    return 0.5


def update_elo(
    rating_home: float,
    rating_away: float,
    home_goals: int,
    away_goals: int,
    k: float = K_FACTOR,
) -> tuple[float, float]:
    """Returns (new_rating_home, new_rating_away) after one match."""
    expected_home = expected_score(rating_home + HOME_ADVANTAGE, rating_away)
    actual_home = match_outcome_score(home_goals, away_goals)
    delta = k * (actual_home - expected_home)
    return rating_home + delta, rating_away - delta


@dataclass(frozen=True)
class EloPoint:
    match_id: int
    team: str
    elo_before: float
    elo_after: float


def compute_elo_history(matches: list[dict]) -> list[EloPoint]:
    """Computes elo_before/elo_after per team for each finished match.

    `matches` must be sorted chronologically ascending and each item must have
    keys: match_id, home_team, away_team, home_goals, away_goals. Unplayed
    fixtures (goals is None) are skipped — they don't move ratings.
    Returns two EloPoints per finished match (home + away).
    """
    ratings: dict[str, float] = {}
    points: list[EloPoint] = []
    for m in matches:
        if m["home_goals"] is None or m["away_goals"] is None:
            continue
        home, away = m["home_team"], m["away_team"]
        rating_home = ratings.get(home, INITIAL_ELO)
        rating_away = ratings.get(away, INITIAL_ELO)
        new_home, new_away = update_elo(rating_home, rating_away, m["home_goals"], m["away_goals"])
        points.append(EloPoint(m["match_id"], home, rating_home, new_home))
        points.append(EloPoint(m["match_id"], away, rating_away, new_away))
        ratings[home] = new_home
        ratings[away] = new_away
    return points
