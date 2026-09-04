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
from datetime import date

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.constants import COMPETITION_SERIE_A, SUPPORTED_COMPETITIONS
from app.db import SessionLocal
from app.features.recompute import recompute_all_derived
from app.ingestion.football_data_client import FootballDataClient, FootballDataError
from app.ingestion.normalize import normalize_football_data_match, normalize_wikipedia_row
from app.ingestion.repository import delete_wikipedia_rows_for_season, upsert_match
from app.ingestion.wikipedia_scraper import scrape_serie_a_season

logger = logging.getLogger(__name__)

DEFAULT_SEASON_LOOKBACK = 3  # + the current season = 4, matching the free tier's known rolling window


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


def update_matches(seasons: list[str] | None = None, competitions: list[str] | None = None) -> None:
    """Downloads/updates match data for the requested seasons (the WHOLE
    competition, not just Juventus' fixtures) and persists it to the DB,
    then recomputes elo/momentum for the whole dataset."""
    settings = get_settings()
    seasons = seasons or default_seasons()
    competitions = competitions or SUPPORTED_COMPETITIONS

    db: Session = SessionLocal()
    try:
        client = FootballDataClient(api_key=settings.football_data_api_key)

        for season in seasons:
            for competition_code in competitions:
                try:
                    count = _ingest_competition_from_football_data(db, client, competition_code, season)
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
                        logger.info("season %s: ingested %d matches from Wikipedia fallback", season, count)

        db.commit()

        recompute_all_derived(db)
        db.commit()
        logger.info("Recomputed elo_ratings and juve_momentum")
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
