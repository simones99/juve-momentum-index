from datetime import datetime, timedelta, timezone

from app.core.constants import COMPETITION_SERIE_A, SOURCE_FOOTBALL_DATA, TEAM_NAME
from app.models.match import Match
from app.models.prediction import Prediction


def _make_match(**overrides) -> Match:
    defaults = dict(
        external_id="fd-1",
        season="2023-2024",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime.now(timezone.utc) + timedelta(days=1),
        home_team=TEAM_NAME,
        away_team="Inter",
        home_goals=None,
        away_goals=None,
        status="TIMED",
        source=SOURCE_FOOTBALL_DATA,
    )
    defaults.update(overrides)
    return Match(**defaults)


def test_submit_requires_device_id_header(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    response = client.post("/api/v1/predictions", json={"match_id": match.id, "predicted_outcome": "HOME"})

    assert response.status_code == 400


def test_submit_rejects_unknown_match(client):
    response = client.post(
        "/api/v1/predictions",
        json={"match_id": 999999, "predicted_outcome": "HOME"},
        headers={"X-Device-Id": "device-1"},
    )

    assert response.status_code == 404


def test_submit_rejects_match_already_kicked_off(client, db):
    match = _make_match(status="FINISHED", match_date=datetime.now(timezone.utc) - timedelta(days=1))
    db.add(match)
    db.commit()

    response = client.post(
        "/api/v1/predictions",
        json={"match_id": match.id, "predicted_outcome": "HOME"},
        headers={"X-Device-Id": "device-1"},
    )

    assert response.status_code == 422


def test_submit_accepted_before_kickoff_and_snapshots_probabilities(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    response = client.post(
        "/api/v1/predictions",
        json={"match_id": match.id, "predicted_outcome": "HOME"},
        headers={"X-Device-Id": "device-1"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["predicted_outcome"] == "HOME"
    assert 0.0 <= body["model_home_prob"] <= 1.0
    total = body["model_home_prob"] + body["model_draw_prob"] + body["model_away_prob"]
    assert abs(total - 1.0) < 1e-6


def test_submit_upserts_on_repeat_submission(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    client.post(
        "/api/v1/predictions",
        json={"match_id": match.id, "predicted_outcome": "HOME"},
        headers={"X-Device-Id": "device-1"},
    )
    client.post(
        "/api/v1/predictions",
        json={"match_id": match.id, "predicted_outcome": "AWAY"},
        headers={"X-Device-Id": "device-1"},
    )

    rows = db.query(Prediction).filter_by(device_id="device-1", match_id=match.id).all()
    assert len(rows) == 1
    assert rows[0].predicted_outcome == "AWAY"


def test_get_mine_requires_device_id(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    response = client.get(f"/api/v1/predictions/mine?match_id={match.id}")

    assert response.status_code == 400


def test_get_mine_returns_null_when_no_prediction_exists(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    response = client.get(f"/api/v1/predictions/mine?match_id={match.id}", headers={"X-Device-Id": "device-1"})

    assert response.status_code == 200
    assert response.json() is None


def test_get_mine_returns_the_submitted_prediction(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    client.post(
        "/api/v1/predictions",
        json={"match_id": match.id, "predicted_outcome": "DRAW"},
        headers={"X-Device-Id": "device-1"},
    )

    response = client.get(f"/api/v1/predictions/mine?match_id={match.id}", headers={"X-Device-Id": "device-1"})

    assert response.status_code == 200
    assert response.json()["predicted_outcome"] == "DRAW"


def test_stats_requires_device_id(client):
    response = client.get("/api/v1/predictions/stats")

    assert response.status_code == 400


def test_stats_are_none_with_no_resolved_predictions(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    client.post(
        "/api/v1/predictions",
        json={"match_id": match.id, "predicted_outcome": "HOME"},
        headers={"X-Device-Id": "device-1"},
    )

    response = client.get("/api/v1/predictions/stats", headers={"X-Device-Id": "device-1"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_resolved"] == 0
    assert body["user_accuracy"] is None
    assert body["model_accuracy"] is None


def test_stats_aggregate_over_resolved_predictions(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    prediction = Prediction(
        device_id="device-1",
        match_id=match.id,
        predicted_outcome="HOME",
        model_home_prob=0.3,
        model_draw_prob=0.3,
        model_away_prob=0.4,
        is_correct=True,
        model_was_correct=False,
        resolved_at=datetime.now(timezone.utc),
    )
    db.add(prediction)
    db.commit()

    response = client.get("/api/v1/predictions/stats", headers={"X-Device-Id": "device-1"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_resolved"] == 1
    assert body["user_correct"] == 1
    assert body["model_correct"] == 0
    assert body["user_accuracy"] == 1.0
    assert body["model_accuracy"] == 0.0


def test_community_stats_requires_no_device_id(client):
    response = client.get("/api/v1/predictions/community-stats")

    assert response.status_code == 200


def test_community_stats_are_none_with_no_resolved_predictions(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    client.post(
        "/api/v1/predictions",
        json={"match_id": match.id, "predicted_outcome": "HOME"},
        headers={"X-Device-Id": "device-1"},
    )

    response = client.get("/api/v1/predictions/community-stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_predictors"] == 0
    assert body["total_resolved"] == 0
    assert body["community_accuracy"] is None
    assert body["model_accuracy"] is None


def test_community_stats_aggregate_across_devices(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    db.add_all(
        [
            Prediction(
                device_id="device-1",
                match_id=match.id,
                predicted_outcome="HOME",
                model_home_prob=0.3,
                model_draw_prob=0.3,
                model_away_prob=0.4,
                is_correct=True,
                model_was_correct=False,
                resolved_at=datetime.now(timezone.utc),
            ),
            Prediction(
                device_id="device-2",
                match_id=match.id,
                predicted_outcome="AWAY",
                model_home_prob=0.3,
                model_draw_prob=0.3,
                model_away_prob=0.4,
                is_correct=False,
                model_was_correct=False,
                resolved_at=datetime.now(timezone.utc),
            ),
        ]
    )
    db.commit()

    response = client.get("/api/v1/predictions/community-stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_predictors"] == 2
    assert body["total_resolved"] == 2
    assert body["community_correct"] == 1
    assert body["model_correct"] == 0
    assert body["community_accuracy"] == 0.5
    assert body["model_accuracy"] == 0.0


def test_community_stats_ignore_unresolved_predictions(client, db):
    match = _make_match()
    db.add(match)
    db.commit()

    client.post(
        "/api/v1/predictions",
        json={"match_id": match.id, "predicted_outcome": "HOME"},
        headers={"X-Device-Id": "device-1"},
    )
    db.add(
        Prediction(
            device_id="device-2",
            match_id=match.id,
            predicted_outcome="AWAY",
            model_home_prob=0.3,
            model_draw_prob=0.3,
            model_away_prob=0.4,
            is_correct=True,
            model_was_correct=True,
            resolved_at=datetime.now(timezone.utc),
        )
    )
    db.commit()

    response = client.get("/api/v1/predictions/community-stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total_predictors"] == 1
    assert body["total_resolved"] == 1
