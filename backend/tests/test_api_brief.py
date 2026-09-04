from datetime import datetime, timedelta, timezone

import pytest

from app.briefs import service as brief_service
from app.briefs.openrouter_client import OpenRouterClient, OpenRouterError
from app.config import Settings
from app.core.constants import (
    COMPETITION_SERIE_A,
    MATCH_STATUS_FINISHED,
    MATCH_STATUS_SCHEDULED,
    MATCH_STATUS_TIMED,
    SOURCE_FOOTBALL_DATA,
    TEAM_NAME,
)
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


def test_match_brief_post_match_defaults_to_template_without_api_key(client, db, monkeypatch):
    matches = _seed_finished_matches(db)
    recompute_all_derived(db)
    db.commit()

    monkeypatch.setattr(brief_service, "get_settings", lambda: Settings(openrouter_api_key=""))

    last_match = matches[-1]
    response = client.get(f"/api/v1/matches/{last_match.id}/brief")
    assert response.status_code == 200
    body = response.json()
    assert body["llm_used"] is False
    assert body["llm_error"] is None
    assert body["display_text"] == body["template_text"]
    assert body["data"]["result"] == "W"
    assert body["data"]["win_probability"] is not None
    total = body["data"]["win_probability"] + body["data"]["draw_probability"] + body["data"]["loss_probability"]
    assert total == pytest.approx(1.0, abs=1e-6)


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
    assert body["data"]["win_probability"] is not None
    total = body["data"]["win_probability"] + body["data"]["draw_probability"] + body["data"]["loss_probability"]
    assert total == pytest.approx(1.0, abs=1e-6)


def test_brief_next_also_finds_timed_status_fixture(client, db):
    # football-data.org marks a fixture TIMED once kickoff time is
    # confirmed (still SCHEDULED before that) — /brief/next must not skip
    # straight past it to a later SCHEDULED one.
    _seed_finished_matches(db)
    db.add(
        Match(
            external_id="timed-next",
            season="2023-2024",
            competition="Serie A",
            competition_code=COMPETITION_SERIE_A,
            match_date=datetime(2023, 10, 1, tzinfo=timezone.utc),
            home_team=TEAM_NAME,
            away_team="Milan",
            home_goals=None,
            away_goals=None,
            status=MATCH_STATUS_TIMED,
            source=SOURCE_FOOTBALL_DATA,
        )
    )
    recompute_all_derived(db)
    db.commit()

    response = client.get("/api/v1/brief/next")
    assert response.status_code == 200
    assert response.json()["data"]["opponent"] == "Milan"


def test_match_brief_lang_en_returns_english_template_text(client, db):
    matches = _seed_finished_matches(db)
    recompute_all_derived(db)
    db.commit()

    last_match = matches[-1]
    response_it = client.get(f"/api/v1/matches/{last_match.id}/brief")
    response_en = client.get(f"/api/v1/matches/{last_match.id}/brief", params={"lang": "en"})
    assert response_it.status_code == response_en.status_code == 200

    body_it = response_it.json()
    body_en = response_en.json()
    assert body_it["display_text"] != body_en["display_text"]
    assert "Momentum Index della partita" in body_it["template_text"][1]
    assert "Match Momentum Index" in body_en["template_text"][1]


def test_brief_next_lang_en_returns_english_head_to_head(client, db):
    _seed_finished_matches(db)
    upcoming = Match(
        external_id="upcoming-en",
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

    response = client.get("/api/v1/brief/next", params={"lang": "en"})
    assert response.status_code == 200
    body = response.json()
    assert "against Napoli" in body["template_text"][0]
    assert "contro" not in "".join(body["template_text"])  # sanity: no stray Italian text leaking through


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
