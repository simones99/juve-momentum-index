"""Orchestrates recomputing elo_ratings and juve_momentum from the matches
table. Run after every ingestion. Cheap enough at MVP data volumes (a few
hundred matches) to just truncate-and-rebuild rather than incrementally
update.
"""

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.constants import TEAM_NAME
from app.features.elo import compute_elo_history
from app.features.momentum_index import compute_momentum_series
from app.models.elo_rating import EloRating
from app.models.juve_momentum import JuveMomentum
from app.models.match import Match


def _load_matches_chronological(db: Session) -> list[Match]:
    return list(db.scalars(select(Match).order_by(Match.match_date.asc())))


def recompute_all_derived(db: Session) -> None:
    matches = _load_matches_chronological(db)

    match_dicts = [
        {
            "match_id": m.id,
            "match_date": m.match_date,
            "home_team": m.home_team,
            "away_team": m.away_team,
            "home_goals": m.home_goals,
            "away_goals": m.away_goals,
        }
        for m in matches
    ]

    elo_points = compute_elo_history(match_dicts)
    match_date_by_id = {m.id: m.match_date for m in matches}

    db.execute(delete(EloRating))
    for point in elo_points:
        db.add(
            EloRating(
                match_id=point.match_id,
                team=point.team,
                elo_before=point.elo_before,
                elo_after=point.elo_after,
                rating_date=match_date_by_id[point.match_id],
            )
        )

    juve_elo_after = {p.match_id: p.elo_after for p in elo_points if p.team == TEAM_NAME}
    juve_elo_before = {p.match_id: p.elo_before for p in elo_points if p.team == TEAM_NAME}

    juve_rows = []
    for m in matches:
        if TEAM_NAME not in (m.home_team, m.away_team):
            continue
        if m.id not in juve_elo_after:
            continue  # unplayed fixture, no elo movement yet

        is_home = m.home_team == TEAM_NAME
        opponent = m.away_team if is_home else m.home_team
        goals_for = m.home_goals if is_home else m.away_goals
        goals_against = m.away_goals if is_home else m.home_goals
        result = "W" if goals_for > goals_against else ("L" if goals_for < goals_against else "D")

        juve_rows.append(
            {
                "match_id": m.id,
                "season": m.season,
                "match_date": m.match_date,
                "opponent": opponent,
                "home_away": "H" if is_home else "A",
                "competition_code": m.competition_code,
                "result": result,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "elo_before": juve_elo_before[m.id],
                "elo_after": juve_elo_after[m.id],
            }
        )

    db.execute(delete(JuveMomentum))
    if not juve_rows:
        return

    df = pd.DataFrame(juve_rows)
    df = compute_momentum_series(df)

    for _, row in df.iterrows():
        db.add(
            JuveMomentum(
                match_id=int(row["match_id"]),
                season=row["season"],
                match_date=row["match_date"],
                opponent=row["opponent"],
                home_away=row["home_away"],
                competition_code=row["competition_code"],
                result=row["result"],
                goals_for=int(row["goals_for"]),
                goals_against=int(row["goals_against"]),
                elo_before=float(row["elo_before"]),
                elo_after=float(row["elo_after"]),
                elo_normalized=float(row["elo_normalized"]),
                points_rolling5=None if pd.isna(row["points_rolling5"]) else float(row["points_rolling5"]),
                points_rolling10=None if pd.isna(row["points_rolling10"]) else float(row["points_rolling10"]),
                goal_diff_rolling5=None
                if pd.isna(row["goal_diff_rolling5"])
                else float(row["goal_diff_rolling5"]),
                goal_diff_rolling10=None
                if pd.isna(row["goal_diff_rolling10"])
                else float(row["goal_diff_rolling10"]),
                momentum_index=float(row["momentum_index"]),
            )
        )
