"""CLI entrypoint: `python -m app.ingestion.ingest --seasons 2022-2023,2023-2024,2024-2025`

Downloads Juventus matches (Serie A + Champions League) for the given
seasons via football-data.org, falling back to the Wikipedia scraper
(Serie A only) if the API call fails, then recomputes elo/momentum.
"""

import argparse
import logging

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.constants import COMPETITION_SERIE_A, SUPPORTED_COMPETITIONS
from app.db import SessionLocal
from app.features.recompute import recompute_all_derived
from app.ingestion.football_data_client import FootballDataClient, FootballDataError
from app.ingestion.normalize import normalize_football_data_match, normalize_wikipedia_row
from app.ingestion.repository import upsert_match
from app.ingestion.wikipedia_scraper import scrape_serie_a_season

logger = logging.getLogger(__name__)

DEFAULT_SEASONS = ["2022-2023", "2023-2024", "2024-2025"]


def _season_start_year(season: str) -> str:
    return season.split("-")[0]


def _ingest_season_from_football_data(
    db: Session, client: FootballDataClient, team_id: int, season: str, competitions: list[str]
) -> int:
    if not team_id:
        raise FootballDataError("JUVENTUS_TEAM_ID not configured")
    raw_matches = client.get_team_matches(team_id, competitions, season=_season_start_year(season))
    if not raw_matches:
        raise FootballDataError(f"no matches returned for season {season}")
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
    """Downloads/updates Juventus match data for the requested seasons and
    persists it to the DB, then recomputes elo/momentum for the whole dataset."""
    settings = get_settings()
    seasons = seasons or DEFAULT_SEASONS
    competitions = competitions or SUPPORTED_COMPETITIONS

    db: Session = SessionLocal()
    try:
        client = FootballDataClient(api_key=settings.football_data_api_key)

        for season in seasons:
            try:
                count = _ingest_season_from_football_data(
                    db, client, settings.juventus_team_id, season, competitions
                )
                logger.info("season %s: ingested %d matches from football-data.org", season, count)
            except FootballDataError as exc:
                logger.warning(
                    "season %s: football-data.org failed (%s); falling back to Wikipedia (Serie A only)",
                    season,
                    exc,
                )
                if COMPETITION_SERIE_A in competitions:
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
        default=",".join(DEFAULT_SEASONS),
        help="Comma-separated seasons, e.g. 2022-2023,2023-2024,2024-2025",
    )
    args = parser.parse_args()
    seasons = [s.strip() for s in args.seasons.split(",") if s.strip()]
    update_matches(seasons=seasons)


if __name__ == "__main__":
    main()
