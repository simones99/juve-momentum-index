"""Persistence helpers for the ingestion pipeline: upsert normalized matches
into the `matches` table, keyed by external_id when available, otherwise by
the natural key (season, competition_code, home_team, away_team, match_date).
"""

from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.constants import SOURCE_WIKIPEDIA
from app.ingestion.normalize import MatchIn
from app.models.ingest_run import IngestRun
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
        existing.venue = match_in.venue or existing.venue
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
        venue=match_in.venue,
        status=match_in.status,
        source=match_in.source,
    )
    db.add(match)
    return match


def delete_wikipedia_rows_for_season(db: Session, season: str, competition_code: str) -> int:
    """Removes Wikipedia-sourced rows for a (season, competition) before
    replacing them with football-data.org data. Needed because the two
    sources give the same real-world match different natural keys (a
    placeholder season-start date vs. the real kickoff date), so the
    upsert's natural-key matching can't tell they're the same fixture and
    would otherwise leave a stale Wikipedia duplicate behind. Returns the
    number of rows removed, for logging."""
    result = db.execute(
        delete(Match).where(
            Match.season == season,
            Match.competition_code == competition_code,
            Match.source == SOURCE_WIKIPEDIA,
        )
    )
    return result.rowcount


def record_ingest_run(
    db: Session,
    *,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    matches_upserted: int,
    source_summary: str,
) -> IngestRun:
    run = IngestRun(
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        matches_upserted=matches_upserted,
        source_summary=source_summary,
    )
    db.add(run)
    return run
