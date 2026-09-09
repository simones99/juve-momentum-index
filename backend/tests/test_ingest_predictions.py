from datetime import datetime, timezone

import app.ingestion.ingest as ingest
from app.core.constants import COMPETITION_SERIE_A, SOURCE_FOOTBALL_DATA, TEAM_NAME
from app.models.match import Match
from app.models.prediction import Prediction


def _make_match(**overrides) -> Match:
    defaults = dict(
        external_id="fd-1",
        season="2023-2024",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime(2024, 3, 15, 20, 45, tzinfo=timezone.utc),
        home_team=TEAM_NAME,
        away_team="Inter",
        home_goals=2,
        away_goals=0,
        status="FINISHED",
        source=SOURCE_FOOTBALL_DATA,
    )
    defaults.update(overrides)
    return Match(**defaults)


def test_resolves_predictions_for_finished_juve_matches(db):
    match = _make_match()
    db.add(match)
    db.commit()

    prediction = Prediction(
        device_id="device-1",
        match_id=match.id,
        predicted_outcome="HOME",
        model_home_prob=0.5,
        model_draw_prob=0.3,
        model_away_prob=0.2,
    )
    db.add(prediction)
    db.commit()

    ingest._resolve_finished_predictions(db)

    db.refresh(prediction)
    assert prediction.resolved_at is not None
    assert prediction.is_correct is True


def test_ignores_matches_with_nothing_unresolved(db):
    match = _make_match()
    db.add(match)
    db.commit()

    prediction = Prediction(
        device_id="device-1",
        match_id=match.id,
        predicted_outcome="AWAY",
        model_home_prob=0.5,
        model_draw_prob=0.3,
        model_away_prob=0.2,
        is_correct=False,
        model_was_correct=True,
        resolved_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )
    db.add(prediction)
    db.commit()

    ingest._resolve_finished_predictions(db)  # must not raise, no-op

    db.refresh(prediction)
    assert prediction.resolved_at == datetime(2024, 1, 1, tzinfo=timezone.utc)
