"""CLI entrypoint: `python -m app.ingestion.ingest [--seasons 2023-2024,2024-2025]`

Downloads EVERY match (Serie A + Champions League) for the given seasons via
football-data.org — not just Juventus' fixtures, so every opponent gets a
real Elo history instead of starting fresh at 1500 the first time it meets
Juve — falling back to the Wikipedia scraper (Serie A only) per competition
if that API call fails, then recomputes elo/momentum. Without `--seasons`,
defaults to the current season plus a few prior ones (see default_seasons()
below) computed from today's date, so this never needs manual bumping as
seasons roll forward.
"""

import argparse
import logging
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.constants import (
    COMPETITION_SERIE_A,
    MATCH_STATUS_FINISHED,
    SOURCE_FOOTBALL_DATA,
    SOURCE_WIKIPEDIA,
    SUPPORTED_COMPETITIONS,
    TEAM_NAME,
    UPCOMING_MATCH_STATUSES,
)
from app.db import SessionLocal
from app.features.recompute import recompute_all_derived
from app.ingestion.football_data_client import FootballDataClient, FootballDataError
from app.ingestion.normalize import normalize_football_data_match, normalize_wikipedia_row
from app.ingestion.repository import delete_wikipedia_rows_for_season, record_ingest_run, upsert_match
from app.ingestion.wikipedia_scraper import scrape_serie_a_season
from app.models.juve_momentum import JuveMomentum
from app.models.match import Match
from app.models.prediction import Prediction
from app.notifications.push_sender import notify_subscribers
from app.predictions.resolver import resolve_predictions

logger = logging.getLogger(__name__)

DEFAULT_SEASON_LOOKBACK = 3  # + the current season = 4, matching the free tier's known rolling window

BRIEF_NOTIFY_WINDOW_HOURS = 48
# Same rolling window as points_rolling5/goal_diff_rolling5, for consistency.
MOMENTUM_SWING_LOOKBACK = 5
MOMENTUM_SWING_THRESHOLD = 15.0  # momentum_index is 0-100; empirically a double-digit swing is noteworthy


def _current_season_start_year(today: date | None = None) -> int:
    """Serie A kicks off mid-August, so treat July onward as "the new season
    has effectively started" (matches football-data.org's own behavior,
    which exposes the new season's fixtures ahead of the first matchday)."""
    today = today or date.today()
    return today.year if today.month >= 7 else today.year - 1


def _season_label(start_year: int) -> str:
    return f"{start_year}-{start_year + 1}"


def default_seasons(lookback: int = DEFAULT_SEASON_LOOKBACK, today: date | None = None) -> list[str]:
    """Current season plus `lookback` prior ones, computed from today's date
    instead of a hardcoded list — football-data.org's free tier only serves
    a rolling ~4-season window, and this keeps requesting the right ones as
    seasons roll forward each year with no manual maintenance. Requesting a
    season outside the actual window degrades gracefully (see
    FootballDataClient._get / update_matches below) rather than failing the
    whole run, so an exact match to the real window isn't required here."""
    current = _current_season_start_year(today)
    return [_season_label(y) for y in range(current - lookback, current + 1)]


def _season_start_year(season: str) -> str:
    return season.split("-")[0]


def _ingest_competition_from_football_data(
    db: Session, client: FootballDataClient, competition_code: str, season: str
) -> int:
    """Ingests EVERY match in the competition/season (not just Juventus'),
    so every team gets a real Elo history. On success, drops any
    Wikipedia-sourced rows already stored for this (season, competition) —
    the natural-key upsert can't otherwise tell a Wikipedia placeholder-date
    row and the real API row are the same match, so without this a season
    that starts on Wikipedia and later gets a real API key ends up with
    duplicates."""
    raw_matches = client.get_competition_matches(competition_code, _season_start_year(season))
    if not raw_matches:
        raise FootballDataError(f"no matches returned for {competition_code} {season}")

    deleted = delete_wikipedia_rows_for_season(db, season, competition_code)
    if deleted:
        logger.info(
            "season %s %s: replacing %d wikipedia-sourced rows with football-data.org",
            season, competition_code, deleted,
        )
    for raw in raw_matches:
        upsert_match(db, normalize_football_data_match(raw))
    return len(raw_matches)


def _ingest_season_from_wikipedia(db: Session, season: str) -> int:
    rows = scrape_serie_a_season(season)
    for row in rows:
        match_in = normalize_wikipedia_row(
            row, season=season, competition="Serie A", competition_code=COMPETITION_SERIE_A
        )
        upsert_match(db, match_in)
    return len(rows)


def _resolve_finished_predictions(db: Session) -> None:
    """Resolves predictions for every Juventus match that finished with
    still-unresolved predictions. Cheap indexed query; `resolve_predictions`
    itself is a no-op once a match has nothing left to resolve, so re-running
    this on every ingest is safe."""
    stmt = (
        select(Match)
        .join(Prediction, Prediction.match_id == Match.id)
        .where(
            (Match.home_team == TEAM_NAME) | (Match.away_team == TEAM_NAME),
            Match.status == MATCH_STATUS_FINISHED,
            Prediction.resolved_at.is_(None),
        )
        .distinct()
    )
    for match in db.scalars(stmt):
        resolve_predictions(db, match)


def _notify_brief_ready(db: Session) -> None:
    """Notifies once per fixture, for the next Juventus match within the
    next 48h, the first time an ingest run sees it with no brief
    notification sent yet — `brief_notified_at` makes this idempotent across
    daily re-runs."""
    cutoff = datetime.now(timezone.utc) + timedelta(hours=BRIEF_NOTIFY_WINDOW_HOURS)
    stmt = (
        select(Match)
        .where(
            (Match.home_team == TEAM_NAME) | (Match.away_team == TEAM_NAME),
            Match.status.in_(UPCOMING_MATCH_STATUSES),
            Match.match_date <= cutoff,
            Match.brief_notified_at.is_(None),
        )
        .order_by(Match.match_date.asc())
        .limit(1)
    )
    match = db.scalar(stmt)
    if match is None:
        return

    opponent = match.away_team if match.home_team == TEAM_NAME else match.home_team
    notify_subscribers(db, "brief", {"title": "Match Brief pronto", "body": f"Juventus – {opponent}"})
    match.brief_notified_at = datetime.now(timezone.utc)
    db.commit()


def _notify_momentum_swing(db: Session) -> None:
    """Compares the Momentum Index of the most recently played Juventus
    match against the one `MOMENTUM_SWING_LOOKBACK` matches before it.
    Unlike the brief-ready hook, there's no persisted "already notified"
    marker here: `recompute_all_derived` rebuilds `juve_momentum` from
    scratch on every ingest run, so if the daily scheduled ingest runs again
    before the next Juventus match, an existing swing is re-evaluated (and
    re-notified) rather than being remembered as already sent."""
    stmt = select(JuveMomentum).order_by(JuveMomentum.match_date.desc()).limit(MOMENTUM_SWING_LOOKBACK + 1)
    recent = list(db.scalars(stmt))
    if len(recent) <= MOMENTUM_SWING_LOOKBACK:
        return

    latest, previous = recent[0], recent[MOMENTUM_SWING_LOOKBACK]
    swing = float(latest.momentum_index) - float(previous.momentum_index)
    if abs(swing) < MOMENTUM_SWING_THRESHOLD:
        return

    direction = "in crescita" if swing > 0 else "in calo"
    notify_subscribers(
        db, "momentum", {"title": "Momentum Juventus " + direction, "body": f"Indice a {latest.momentum_index:.0f}"}
    )


def update_matches(seasons: list[str] | None = None, competitions: list[str] | None = None) -> None:
    """Downloads/updates match data for the requested seasons (the WHOLE
    competition, not just Juventus' fixtures) and persists it to the DB,
    then recomputes elo/momentum for the whole dataset."""
    settings = get_settings()
    seasons = seasons or default_seasons()
    competitions = competitions or SUPPORTED_COMPETITIONS

    db: Session = SessionLocal()
    started_at = datetime.now(timezone.utc)
    source_counts: dict[str, int] = {}
    try:
        client = FootballDataClient(api_key=settings.football_data_api_key)

        for season in seasons:
            for competition_code in competitions:
                try:
                    count = _ingest_competition_from_football_data(db, client, competition_code, season)
                    source_counts[SOURCE_FOOTBALL_DATA] = source_counts.get(SOURCE_FOOTBALL_DATA, 0) + count
                    logger.info(
                        "season %s %s: ingested %d matches from football-data.org",
                        season, competition_code, count,
                    )
                except FootballDataError as exc:
                    has_fallback = competition_code == COMPETITION_SERIE_A
                    logger.warning(
                        "season %s %s: football-data.org failed (%s)%s",
                        season, competition_code, exc,
                        "; falling back to Wikipedia" if has_fallback else " (no fallback for this competition)",
                    )
                    if has_fallback:
                        count = _ingest_season_from_wikipedia(db, season)
                        source_counts[SOURCE_WIKIPEDIA] = source_counts.get(SOURCE_WIKIPEDIA, 0) + count
                        logger.info("season %s: ingested %d matches from Wikipedia fallback", season, count)

        db.commit()

        recompute_all_derived(db)
        db.commit()
        logger.info("Recomputed elo_ratings and juve_momentum")

        _resolve_finished_predictions(db)
        _notify_brief_ready(db)
        _notify_momentum_swing(db)

        record_ingest_run(
            db,
            started_at=started_at,
            finished_at=datetime.now(timezone.utc),
            status="success",
            matches_upserted=sum(source_counts.values()),
            source_summary=", ".join(f"{k}:{v}" for k, v in sorted(source_counts.items())) or "none",
        )
        db.commit()
    finally:
        db.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Update Juventus match data")
    parser.add_argument(
        "--seasons",
        type=str,
        default="",
        help=(
            "Comma-separated seasons, e.g. 2023-2024,2024-2025. "
            "If omitted, defaults to the current season plus the prior "
            f"{DEFAULT_SEASON_LOOKBACK}, computed from today's date."
        ),
    )
    args = parser.parse_args()
    seasons = [s.strip() for s in args.seasons.split(",") if s.strip()] or None
    update_matches(seasons=seasons)


if __name__ == "__main__":
    main()
