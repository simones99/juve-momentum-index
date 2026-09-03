from datetime import datetime, timedelta, timezone

from app.briefs import service as brief_service
from app.briefs.openrouter_client import OpenRouterClient, OpenRouterError
from app.config import Settings
from app.core.constants import COMPETITION_SERIE_A, MATCH_STATUS_FINISHED, MATCH_STATUS_SCHEDULED, SOURCE_FOOTBALL_DATA, TEAM_NAME
from app.features.recompute import recompute_all_derived
from app.models.match import Match


def _seed_finished_matches(db) -> list[Match]:
    base_date = datetime(2023, 9, 1, 18, 45, tzinfo=timezone.utc)
    fixtures = [
        ("Inter", TEAM_NAME, "Inter", 0, 2, True),
        (TEAM_NAME, "Milan", TEAM_NAME, 1, 1, True),
        (TEAM_NAME, "Roma", TEAM_NAME, 3, 0, True),
    ]
    matches = []
    for i, (home, away, _, home_goals, away_goals, _) in enumerate(fixtures):
        m = Match(
            external_id=f"m{i}",
            season="2023-2024",
            competition="Serie A",
            competition_code=COMPETITION_SERIE_A,
            match_date=base_date + timedelta(days=7 * i),
            home_team=home,
            away_team=away,
            home_goals=home_goals,
            away_goals=away_goals,
            status=MATCH_STATUS_FINISHED,
            source=SOURCE_FOOTBALL_DATA,
        )
        db.add(m)
        matches.append(m)
    db.flush()
    return matches


def test_match_brief_for_unfinished_match_returns_404(client, db):
    m = Match(
        external_id="future1",
        season="2023-2024",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime(2030, 1, 1, tzinfo=timezone.utc),
        home_team=TEAM_NAME,
        away_team="Napoli",
        home_goals=None,
        away_goals=None,
        status=MATCH_STATUS_SCHEDULED,
        source=SOURCE_FOOTBALL_DATA,
    )
    db.add(m)
    db.commit()

    response = client.get(f"/api/v1/matches/{m.id}/brief")
    assert response.status_code == 404


def test_match_brief_post_match_defaults_to_template_without_api_key(client, db):
    matches = _seed_finished_matches(db)
    recompute_all_derived(db)
    db.commit()

    last_match = matches[-1]
    response = client.get(f"/api/v1/matches/{last_match.id}/brief")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_used"] is False
    assert body["llm_error"] is None
    assert body["display_text"] == body["template_text"]
    assert body["data"]["result"] == "W"


def test_brief_next_uses_upcoming_scheduled_fixture(client, db):
    _seed_finished_matches(db)
    upcoming = Match(
        external_id="upcoming1",
        season="2023-2024",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime(2023, 10, 1, tzinfo=timezone.utc),
        home_team=TEAM_NAME,
        away_team="Napoli",
        home_goals=None,
        away_goals=None,
        status=MATCH_STATUS_SCHEDULED,
        source=SOURCE_FOOTBALL_DATA,
    )
    db.add(upcoming)
    recompute_all_derived(db)
    db.commit()

    response = client.get("/api/v1/brief/next")
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["opponent"] == "Napoli"
    assert body["data"]["matches_considered"] == 3


def test_llm_failure_falls_back_to_template(client, db, monkeypatch):
    matches = _seed_finished_matches(db)
    recompute_all_derived(db)
    db.commit()

    fake_settings = Settings(openrouter_api_key="fake-key", enable_llm_brief=True)
    monkeypatch.setattr(brief_service, "get_settings", lambda: fake_settings)

    def _raise(*args, **kwargs):
        raise OpenRouterError("simulated timeout")

    monkeypatch.setattr(OpenRouterClient, "generate_brief_text", _raise)

    last_match = matches[-1]
    response = client.get(f"/api/v1/matches/{last_match.id}/brief")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_used"] is False
    assert body["llm_error"] == "simulated timeout"
    assert body["display_text"] == body["template_text"]
