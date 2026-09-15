from datetime import datetime, timedelta, timezone

from app.api.routes import travel as travel_route
from app.core.constants import (
    COMPETITION_SERIE_A,
    MATCH_STATUS_FINISHED,
    MATCH_STATUS_SCHEDULED,
    MATCH_STATUS_TIMED,
    SOURCE_FOOTBALL_DATA,
    TEAM_NAME,
)
from app.ingestion.geocoding import GeocodingError
from app.ingestion.routing import RoutingError
from app.models.match import Match


def _away_match(**overrides) -> Match:
    defaults = dict(
        external_id=None,
        season="2026-2027",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime.now(timezone.utc) + timedelta(days=10),
        home_team="SSC Napoli",
        away_team=TEAM_NAME,
        home_goals=None,
        away_goals=None,
        status=MATCH_STATUS_SCHEDULED,
        source=SOURCE_FOOTBALL_DATA,
    )
    defaults.update(overrides)
    return Match(**defaults)


def test_away_fixtures_returns_404_when_city_not_found(client, db, monkeypatch):
    def _raise(self, query):
        raise GeocodingError(f"no location found for '{query}'")

    monkeypatch.setattr(travel_route.NominatimClient, "geocode", _raise)

    response = client.get("/api/v1/travel/away-fixtures", params={"from_city": "Nonexistentville"})
    assert response.status_code == 404


def test_away_fixtures_only_includes_scheduled_away_matches(client, db, monkeypatch):
    monkeypatch.setattr(
        travel_route.NominatimClient, "geocode", lambda self, q: (43.6158, 13.5189, "Ancona, Marche, Italia")
    )
    monkeypatch.setattr(travel_route.OsrmClient, "route", lambda self, *a: (300.0, 3.5))

    db.add(_away_match(external_id="scheduled-away"))
    db.add(_away_match(external_id="finished-away", status=MATCH_STATUS_FINISHED, home_goals=1, away_goals=1))
    db.add(_away_match(external_id="scheduled-home", home_team=TEAM_NAME, away_team="SSC Napoli"))
    db.commit()

    response = client.get("/api/v1/travel/away-fixtures", params={"from_city": "Ancona"})
    assert response.status_code == 200
    body = response.json()
    assert len(body["fixtures"]) == 1
    assert body["fixtures"][0]["opponent"] == "SSC Napoli"
    assert body["from_location"]["display_name"] == "Ancona, Marche, Italia"


def test_away_fixtures_includes_timed_status_not_just_scheduled(client, db, monkeypatch):
    # Same TIMED-vs-SCHEDULED gap as /matches/upcoming: football-data.org
    # marks a fixture TIMED once kickoff time is confirmed.
    monkeypatch.setattr(
        travel_route.NominatimClient, "geocode", lambda self, q: (43.6158, 13.5189, "Ancona, Marche, Italia")
    )
    monkeypatch.setattr(travel_route.OsrmClient, "route", lambda self, *a: (300.0, 3.5))

    db.add(_away_match(external_id="timed-away", status=MATCH_STATUS_TIMED))
    db.commit()

    response = client.get("/api/v1/travel/away-fixtures", params={"from_city": "Ancona"})
    assert response.status_code == 200
    assert len(response.json()["fixtures"]) == 1


def test_away_fixtures_uses_real_osrm_distance_and_sorts_by_effort(client, db, monkeypatch):
    monkeypatch.setattr(
        travel_route.NominatimClient, "geocode", lambda self, q: (43.6158, 13.5189, "Ancona, Marche, Italia")
    )

    def fake_route(self, from_lat, from_lon, to_lat, to_lon):
        # Napoli is "far" (10h), Fiorentina is "close" (1h) — easy to assert ordering.
        return (700.0, 10.0) if to_lat == 40.8279 else (100.0, 1.0)

    monkeypatch.setattr(travel_route.OsrmClient, "route", fake_route)

    base_date = datetime.now(timezone.utc) + timedelta(days=5)
    db.add(_away_match(external_id="far", home_team="SSC Napoli", match_date=base_date))
    db.add(_away_match(external_id="close", home_team="ACF Fiorentina", match_date=base_date + timedelta(days=7)))
    db.commit()

    response = client.get("/api/v1/travel/away-fixtures", params={"from_city": "Ancona"})
    body = response.json()
    assert [f["opponent"] for f in body["fixtures"]] == ["ACF Fiorentina", "SSC Napoli"]
    assert body["fixtures"][0]["distance_km"] == 100.0
    assert body["fixtures"][0]["is_estimated"] is False


def test_away_fixtures_falls_back_when_osrm_unreachable(client, db, monkeypatch):
    monkeypatch.setattr(
        travel_route.NominatimClient, "geocode", lambda self, q: (43.6158, 13.5189, "Ancona, Marche, Italia")
    )

    def _raise(self, *args):
        raise RoutingError("simulated OSRM outage")

    monkeypatch.setattr(travel_route.OsrmClient, "route", _raise)

    db.add(_away_match(external_id="fallback-case", home_team="SSC Napoli"))
    db.commit()

    response = client.get("/api/v1/travel/away-fixtures", params={"from_city": "Ancona"})
    assert response.status_code == 200
    fixture = response.json()["fixtures"][0]
    assert fixture["is_estimated"] is True
    assert fixture["distance_km"] is not None


def test_away_fixtures_handles_unknown_stadium_gracefully(client, db, monkeypatch):
    monkeypatch.setattr(
        travel_route.NominatimClient, "geocode", lambda self, q: (43.6158, 13.5189, "Ancona, Marche, Italia")
    )

    db.add(_away_match(external_id="unknown-stadium", home_team="FC Some New Promoted Club"))
    db.commit()

    response = client.get("/api/v1/travel/away-fixtures", params={"from_city": "Ancona"})
    assert response.status_code == 200
    fixture = response.json()["fixtures"][0]
    assert fixture["distance_km"] is None
    assert fixture["effort_score"] is None
    assert fixture["crest_url"] is None


def test_away_fixtures_includes_crest_url_for_known_opponent(client, db, monkeypatch):
    monkeypatch.setattr(
        travel_route.NominatimClient, "geocode", lambda self, q: (43.6158, 13.5189, "Ancona, Marche, Italia")
    )
    monkeypatch.setattr(travel_route.OsrmClient, "route", lambda self, *a: (300.0, 3.5))

    db.add(_away_match(external_id="crest-fixture", home_team="SSC Napoli"))
    db.commit()

    response = client.get("/api/v1/travel/away-fixtures", params={"from_city": "Ancona"})
    body = response.json()

    assert body["fixtures"][0]["crest_url"] == "https://crests.football-data.org/113.png"
