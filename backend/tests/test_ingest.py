from datetime import datetime, timezone

from sqlalchemy import select

from app.core.constants import COMPETITION_SERIE_A, SOURCE_WIKIPEDIA, TEAM_NAME
from app.ingestion.football_data_client import FootballDataClient
from app.ingestion.ingest import _ingest_competition_from_football_data
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
