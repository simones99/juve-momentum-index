"""Persistence helpers for the ingestion pipeline: upsert normalized matches
into the `matches` table, keyed by external_id when available, otherwise by
the natural key (season, competition_code, home_team, away_team, match_date).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.normalize import MatchIn
from app.models.match import Match


def upsert_match(db: Session, match_in: MatchIn) -> Match:
    existing: Match | None = None
    if match_in.external_id:
        existing = db.scalar(select(Match).where(Match.external_id == match_in.external_id))
    if existing is None:
        existing = db.scalar(
            select(Match).where(
                Match.season == match_in.season,
                Match.competition_code == match_in.competition_code,
                Match.home_team == match_in.home_team,
                Match.away_team == match_in.away_team,
                Match.match_date == match_in.match_date,
            )
        )

    if existing is not None:
        existing.external_id = match_in.external_id or existing.external_id
        existing.competition = match_in.competition
        existing.home_goals = match_in.home_goals
        existing.away_goals = match_in.away_goals
        existing.status = match_in.status
        existing.source = match_in.source
        return existing

    match = Match(
        external_id=match_in.external_id,
        season=match_in.season,
        competition=match_in.competition,
        competition_code=match_in.competition_code,
        match_date=match_in.match_date,
        home_team=match_in.home_team,
        away_team=match_in.away_team,
        home_goals=match_in.home_goals,
        away_goals=match_in.away_goals,
        status=match_in.status,
        source=match_in.source,
    )
    db.add(match)
    return match
