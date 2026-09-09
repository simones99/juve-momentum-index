from datetime import datetime, timezone

from app.core.constants import COMPETITION_SERIE_A, SOURCE_FOOTBALL_DATA, TEAM_NAME
from app.models.match import Match
from app.models.prediction import Prediction
from app.predictions.resolver import resolve_predictions


def _make_match(**overrides) -> Match:
    defaults = dict(
        external_id="fd-1",
        season="2023-2024",
        competition="Serie A",
        competition_code=COMPETITION_SERIE_A,
        match_date=datetime(2024, 3, 15, 20, 45, tzinfo=timezone.utc),
        home_team=TEAM_NAME,
        away_team="Inter",
        home_goals=None,
        away_goals=None,
        status="TIMED",
        source=SOURCE_FOOTBALL_DATA,
    )
    defaults.update(overrides)
    return Match(**defaults)


def _make_prediction(match_id: int, **overrides) -> Prediction:
    defaults = dict(
        device_id="device-1",
        match_id=match_id,
        predicted_outcome="HOME",
        model_home_prob=0.5,
        model_draw_prob=0.3,
        model_away_prob=0.2,
    )
    defaults.update(overrides)
    return Prediction(**defaults)


def test_returns_zero_when_match_has_no_final_score(db):
    match = _make_match(status="TIMED", home_goals=None, away_goals=None)
    db.add(match)
    db.commit()

    assert resolve_predictions(db, match) == 0


def test_correct_user_prediction_and_correct_model_prediction(db):
    match = _make_match(status="FINISHED", home_goals=2, away_goals=0)
    db.add(match)
    db.commit()

    prediction = _make_prediction(match.id, predicted_outcome="HOME", model_home_prob=0.6, model_draw_prob=0.25, model_away_prob=0.15)
    db.add(prediction)
    db.commit()

    resolved = resolve_predictions(db, match)

    assert resolved == 1
    assert prediction.is_correct is True
    assert prediction.model_was_correct is True
    assert prediction.resolved_at is not None


def test_wrong_user_prediction_and_wrong_model_prediction(db):
    match = _make_match(status="FINISHED", home_goals=0, away_goals=1)
    db.add(match)
    db.commit()

    prediction = _make_prediction(match.id, predicted_outcome="HOME", model_home_prob=0.6, model_draw_prob=0.25, model_away_prob=0.15)
    db.add(prediction)
    db.commit()

    resolve_predictions(db, match)

    assert prediction.is_correct is False
    assert prediction.model_was_correct is False


def test_draw_outcome_is_resolved_correctly(db):
    match = _make_match(status="FINISHED", home_goals=1, away_goals=1)
    db.add(match)
    db.commit()

    prediction = _make_prediction(match.id, predicted_outcome="DRAW", model_home_prob=0.3, model_draw_prob=0.45, model_away_prob=0.25)
    db.add(prediction)
    db.commit()

    resolve_predictions(db, match)

    assert prediction.is_correct is True
    assert prediction.model_was_correct is True


def test_already_resolved_predictions_are_left_untouched(db):
    match = _make_match(status="FINISHED", home_goals=2, away_goals=0)
    db.add(match)
    db.commit()

    already_resolved_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    prediction = _make_prediction(
        match.id,
        predicted_outcome="AWAY",
        is_correct=False,
        model_was_correct=False,
        resolved_at=already_resolved_at,
    )
    db.add(prediction)
    db.commit()

    resolved = resolve_predictions(db, match)

    assert resolved == 0
    assert prediction.resolved_at == already_resolved_at
