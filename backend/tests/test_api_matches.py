from datetime import datetime, timezone

from app.core.constants import COMPETITION_SERIE_A, SOURCE_FOOTBALL_DATA, TEAM_NAME
from app.models.match import Match


def _make_match(**overrides) -> Match:
    defaults = dict(
        external_id=None,
        season="2023-2024",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime(2023, 9, 3, 18, 45, tzinfo=timezone.utc),
        home_team=TEAM_NAME,
        away_team="Inter",
        home_goals=2,
        away_goals=1,
        status="FINISHED",
        source=SOURCE_FOOTBALL_DATA,
    )
    defaults.update(overrides)
    return Match(**defaults)


def test_list_matches_only_returns_juventus_matches(client, db):
    db.add(_make_match())
    db.add(_make_match(home_team="Inter", away_team="Milan", external_id="not-juve"))
    db.commit()

    response = client.get("/api/v1/matches")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["home_team"] == TEAM_NAME


def test_list_matches_computes_result_from_juve_perspective(client, db):
    db.add(_make_match(home_goals=2, away_goals=1))  # Juve home win
    db.add(
        _make_match(
            home_team="Milan",
            away_team=TEAM_NAME,
            home_goals=2,
            away_goals=0,
            match_date=datetime(2023, 9, 10, 18, 45, tzinfo=timezone.utc),
            external_id="away-loss",
        )
    )
    db.commit()

    response = client.get("/api/v1/matches")
    body = response.json()
    results = {item["home_team"] == TEAM_NAME: item["result"] for item in body["items"]}
    assert results[True] == "W"
    assert results[False] == "L"


def test_list_matches_filters_by_result(client, db):
    db.add(_make_match(home_goals=2, away_goals=1, external_id="win"))
    db.add(
        _make_match(
            home_goals=0,
            away_goals=0,
            external_id="draw",
            match_date=datetime(2023, 9, 10, 18, 45, tzinfo=timezone.utc),
        )
    )
    db.commit()

    response = client.get("/api/v1/matches", params={"result": "D"})
    body = response.json()
    assert body["total"] == 1
    assert body["items"][0]["result"] == "D"


def test_get_match_not_found_returns_404(client, db):
    response = client.get("/api/v1/matches/999999")
    assert response.status_code == 404
