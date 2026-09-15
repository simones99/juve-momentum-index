from datetime import date, datetime, timezone

import pytest

import app.api.routes.matches as matches_routes
from app.core.constants import COMPETITION_SERIE_A, SOURCE_FOOTBALL_DATA, SOURCE_WIKIPEDIA, TEAM_NAME
from app.models.match import Match

TODAY = date(2024, 3, 15)


class _FrozenDate(date):
    @classmethod
    def today(cls):
        return TODAY


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


def test_upcoming_matches_returns_only_scheduled_ordered_by_date_with_venue(client, db):
    db.add(_make_match(external_id="finished", status="FINISHED"))
    db.add(
        _make_match(
            external_id="later",
            away_team="Roma",
            status="SCHEDULED",
            home_goals=None,
            away_goals=None,
            match_date=datetime(2030, 2, 1, tzinfo=timezone.utc),
            venue="Allianz Stadium",
        )
    )
    db.add(
        _make_match(
            external_id="sooner",
            away_team="Napoli",
            status="SCHEDULED",
            home_goals=None,
            away_goals=None,
            match_date=datetime(2030, 1, 1, tzinfo=timezone.utc),
            venue="Stadio Diego Armando Maradona",
        )
    )
    db.commit()

    response = client.get("/api/v1/matches/upcoming")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["away_team"] == "Napoli"
    assert body[0]["venue"] == "Stadio Diego Armando Maradona"
    assert body[1]["away_team"] == "Roma"


def test_upcoming_matches_includes_timed_status_not_just_scheduled(client, db):
    # football-data.org marks a fixture TIMED once kickoff time is
    # confirmed (still SCHEDULED before that) — both are "upcoming, not yet
    # played". Missing TIMED here means the actual next match gets skipped.
    db.add(
        _make_match(
            external_id="timed-next",
            away_team="AC Milan",
            status="TIMED",
            home_goals=None,
            away_goals=None,
            match_date=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
    )
    db.commit()

    response = client.get("/api/v1/matches/upcoming")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["away_team"] == "AC Milan"
    assert body[0]["status"] == "TIMED"


def test_recent_matches_returns_only_finished_in_chronological_order(client, db):
    db.add(
        _make_match(
            external_id="oldest",
            away_team="Roma",
            match_date=datetime(2023, 8, 1, tzinfo=timezone.utc),
        )
    )
    db.add(
        _make_match(
            external_id="newest",
            away_team="Napoli",
            match_date=datetime(2023, 9, 1, tzinfo=timezone.utc),
        )
    )
    db.add(
        _make_match(
            external_id="not-yet-played",
            away_team="Milan",
            status="SCHEDULED",
            home_goals=None,
            away_goals=None,
            match_date=datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
    )
    db.commit()

    response = client.get("/api/v1/matches/recent", params={"limit": 5})
    assert response.status_code == 200
    body = response.json()
    assert [m["away_team"] for m in body] == ["Roma", "Napoli"]
    assert all(m["status"] == "FINISHED" for m in body)


def test_recent_matches_respects_limit_keeping_the_most_recent(client, db):
    for i, opponent in enumerate(["Roma", "Napoli", "Milan"]):
        db.add(
            _make_match(
                external_id=f"m{i}",
                away_team=opponent,
                match_date=datetime(2023, 8 + i, 1, tzinfo=timezone.utc),
            )
        )
    db.commit()

    response = client.get("/api/v1/matches/recent", params={"limit": 2})
    body = response.json()
    assert [m["away_team"] for m in body] == ["Napoli", "Milan"]


def test_live_match_returns_null_when_nothing_is_in_play(client, db, monkeypatch):
    monkeypatch.setattr(matches_routes, "date", _FrozenDate)
    db.add(
        _make_match(
            external_id="scheduled-today",
            status="SCHEDULED",
            home_goals=None,
            away_goals=None,
            match_date=datetime(2024, 3, 15, 20, 45, tzinfo=timezone.utc),
        )
    )
    db.commit()

    response = client.get("/api/v1/matches/live")
    assert response.status_code == 200
    assert response.json() is None


def test_live_match_returns_juve_home_match_in_play(client, db, monkeypatch):
    monkeypatch.setattr(matches_routes, "date", _FrozenDate)
    db.add(
        _make_match(
            external_id="live-home",
            status="IN_PLAY",
            home_goals=1,
            away_goals=0,
            match_date=datetime(2024, 3, 15, 20, 45, tzinfo=timezone.utc),
        )
    )
    db.commit()

    response = client.get("/api/v1/matches/live")
    assert response.status_code == 200
    body = response.json()
    assert body["opponent"] == "Inter"
    assert body["home_away"] == "H"
    assert body["status"] == "IN_PLAY"
    assert body["home_goals"] == 1
    assert body["away_goals"] == 0
    probs = body["probabilities"]
    assert probs["win"] + probs["draw"] + probs["loss"] == pytest.approx(1.0)
    assert body["is_approximate"] is True


def test_live_match_returns_juve_away_match_with_correct_perspective(client, db, monkeypatch):
    monkeypatch.setattr(matches_routes, "date", _FrozenDate)
    db.add(
        _make_match(
            external_id="live-away",
            home_team="Milan",
            away_team=TEAM_NAME,
            status="PAUSED",
            home_goals=0,
            away_goals=1,
            match_date=datetime(2024, 3, 15, 15, 0, tzinfo=timezone.utc),
        )
    )
    db.commit()

    response = client.get("/api/v1/matches/live")
    body = response.json()
    assert body["opponent"] == "Milan"
    assert body["home_away"] == "A"
    # Juve is away and leading 1-0, so the model should favor a Juve win.
    assert body["probabilities"]["win"] > body["probabilities"]["loss"]


def test_live_match_ignores_matches_not_scheduled_today(client, db, monkeypatch):
    monkeypatch.setattr(matches_routes, "date", _FrozenDate)
    db.add(
        _make_match(
            external_id="live-yesterday",
            status="IN_PLAY",
            home_goals=1,
            away_goals=0,
            match_date=datetime(2024, 3, 14, 20, 45, tzinfo=timezone.utc),
        )
    )
    db.commit()

    response = client.get("/api/v1/matches/live")
    assert response.json() is None


def test_list_matches_flags_wikipedia_sourced_matches_as_approximate(client, db):
    db.add(_make_match(external_id="fd-1", source=SOURCE_FOOTBALL_DATA))
    db.add(_make_match(external_id="wiki-1", source=SOURCE_WIKIPEDIA, away_team="Milan"))
    db.commit()

    response = client.get("/api/v1/matches")
    by_source = {m["away_team"]: m["is_approximate_date"] for m in response.json()["items"]}

    assert by_source["Inter"] is False
    assert by_source["Milan"] is True


def test_list_matches_includes_crest_urls_for_known_teams(client, db):
    db.add(_make_match(external_id="crest-1", away_team="SSC Napoli"))
    db.commit()

    response = client.get("/api/v1/matches")
    match = response.json()["items"][0]

    assert match["home_crest_url"] == "https://crests.football-data.org/109.png"
    assert match["away_crest_url"] == "https://crests.football-data.org/113.png"


def test_list_matches_crest_url_is_null_for_unknown_team(client, db):
    db.add(_make_match(external_id="crest-2", away_team="Some Historic Club FC"))
    db.commit()

    response = client.get("/api/v1/matches")
    match = response.json()["items"][0]

    assert match["away_crest_url"] is None
