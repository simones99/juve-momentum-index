from datetime import date, datetime, timezone

from sqlalchemy import select

from app.core.constants import COMPETITION_SERIE_A, SOURCE_WIKIPEDIA, TEAM_NAME
from app.ingestion.football_data_client import FootballDataClient, FootballDataError
from app.ingestion.ingest import (
    _ingest_competition_from_football_data,
    default_seasons,
    update_matches,
)
from app.models.ingest_run import IngestRun
from app.models.match import Match


def _raw_match(
    match_id: int, home: str, away: str, home_goals: int, away_goals: int, utc_date: str
) -> dict:
    return {
        "id": match_id,
        "utcDate": utc_date,
        "status": "FINISHED",
        "season": {"startDate": "2024-08-17"},
        "competition": {"name": "Serie A", "code": "SA"},
        "homeTeam": {"name": home},
        "awayTeam": {"name": away},
        "score": {"fullTime": {"home": home_goals, "away": away_goals}},
        "venue": "Some Stadium",
    }


def test_ingests_matches_not_involving_juventus(db, monkeypatch):
    # This is the core Fase 2 requirement: today's ingestion only pulls
    # Juventus fixtures, so every other club's Elo resets to 1500 on first
    # appearance. Ingesting whole-competition data must store matches
    # between two OTHER teams too.
    raw_matches = [
        _raw_match(1, "FC Internazionale Milano", "AC Milan", 2, 1, "2024-09-01T18:45:00Z"),
        _raw_match(2, "Juventus FC", "SSC Napoli", 3, 0, "2024-09-08T18:45:00Z"),
    ]
    monkeypatch.setattr(FootballDataClient, "get_competition_matches", lambda self, code, season: raw_matches)

    client = FootballDataClient(api_key="fake-key")
    count = _ingest_competition_from_football_data(db, client, COMPETITION_SERIE_A, "2024-2025")
    db.commit()

    assert count == 2
    derby = db.scalar(select(Match).where(Match.home_team == "Inter Milan", Match.away_team == "AC Milan"))
    assert derby is not None
    assert derby.home_goals == 2

    juve_match = db.scalar(select(Match).where(Match.away_team == "SSC Napoli"))
    assert juve_match is not None
    assert juve_match.home_team == TEAM_NAME


def test_football_data_success_replaces_wikipedia_rows_for_that_season(db, monkeypatch):
    # Simulates a season that started on the Wikipedia fallback (placeholder
    # date) and later gets ingested for real once an API key exists — the
    # two must not coexist as duplicates of the same match.
    wikipedia_row = Match(
        external_id=None,
        season="2024-2025",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime(2024, 8, 15, tzinfo=timezone.utc),  # wikipedia placeholder date
        home_team=TEAM_NAME,
        away_team="SSC Napoli",
        home_goals=3,
        away_goals=0,
        status="FINISHED",
        source=SOURCE_WIKIPEDIA,
    )
    db.add(wikipedia_row)
    db.commit()

    raw_matches = [_raw_match(99, "Juventus FC", "SSC Napoli", 3, 0, "2024-09-08T18:45:00Z")]
    monkeypatch.setattr(FootballDataClient, "get_competition_matches", lambda self, code, season: raw_matches)

    client = FootballDataClient(api_key="fake-key")
    _ingest_competition_from_football_data(db, client, COMPETITION_SERIE_A, "2024-2025")
    db.commit()

    rows = list(
        db.scalars(
            select(Match).where(
                Match.season == "2024-2025", Match.away_team == "SSC Napoli", Match.home_team == TEAM_NAME
            )
        )
    )
    assert len(rows) == 1
    assert rows[0].source == "football-data"
    assert rows[0].external_id == "99"


def test_default_seasons_computed_from_todays_date_not_hardcoded():
    # Matches the real free-tier window observed on 2026-09-04: current
    # season (2026-2027) plus the 3 prior ones.
    assert default_seasons(lookback=3, today=date(2026, 9, 4)) == [
        "2023-2024",
        "2024-2025",
        "2025-2026",
        "2026-2027",
    ]
    # Before Serie A's July rollover, "current" is still the previous season.
    assert default_seasons(lookback=1, today=date(2026, 6, 30)) == ["2024-2025", "2025-2026"]
    assert default_seasons(lookback=1, today=date(2026, 7, 1)) == ["2025-2026", "2026-2027"]


def test_football_data_failure_for_one_season_falls_back_instead_of_crashing_whole_run(db, monkeypatch):
    # A season outside the free tier's window (or any other football-data.org
    # failure) must not take down the rest of the ingestion run — Serie A
    # falls back to Wikipedia per season/competition (see update_matches).
    # update_matches() opens its own session via SessionLocal() rather than
    # taking one as a parameter, so it's redirected to the test's `db`
    # fixture (and its close() neutralized, since the fixture owns that
    # session's lifecycle) instead of touching the real dev database.
    monkeypatch.setattr("app.ingestion.ingest.SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)

    def _raise_out_of_range(self, code, season):
        raise FootballDataError("403: season outside free-tier window")

    monkeypatch.setattr(FootballDataClient, "get_competition_matches", _raise_out_of_range)
    monkeypatch.setattr(
        "app.ingestion.ingest.scrape_serie_a_season",
        lambda season: [
            {
                "match_date": datetime(2019, 9, 1, tzinfo=timezone.utc),
                "home_team": TEAM_NAME,
                "away_team": "SSC Napoli",
                "home_goals": 1,
                "away_goals": 0,
            }
        ],
    )

    update_matches(seasons=["2019-2020"], competitions=[COMPETITION_SERIE_A])  # must not raise

    row = db.scalar(select(Match).where(Match.season == "2019-2020"))
    assert row is not None
    assert row.source == SOURCE_WIKIPEDIA


def test_update_matches_records_a_successful_ingest_run(db, monkeypatch):
    monkeypatch.setattr("app.ingestion.ingest.SessionLocal", lambda: db)
    monkeypatch.setattr(db, "close", lambda: None)

    raw_matches = [
        _raw_match(1, "Juventus FC", "SSC Napoli", 2, 0, "2024-09-08T18:45:00Z"),
        _raw_match(2, "AC Milan", "Inter Milan", 1, 1, "2024-09-01T18:45:00Z"),
    ]
    monkeypatch.setattr(FootballDataClient, "get_competition_matches", lambda self, code, season: raw_matches)

    update_matches(seasons=["2024-2025"], competitions=[COMPETITION_SERIE_A])

    run = db.scalar(select(IngestRun).order_by(IngestRun.id.desc()))
    assert run is not None
    assert run.status == "success"
    assert run.matches_upserted == 2
    assert run.source_summary == "football-data:2"
    assert run.finished_at >= run.started_at
