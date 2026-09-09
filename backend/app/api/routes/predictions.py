from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.briefs.template_brief import _current_elo
from app.core.constants import UPCOMING_MATCH_STATUSES
from app.db import get_db
from app.features.win_probability import estimate_match_probabilities
from app.models.match import Match
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionIn, PredictionOut, PredictionStats

router = APIRouter(tags=["predictions"])


def _require_device_id(x_device_id: str | None) -> str:
    if not x_device_id:
        raise HTTPException(status_code=400, detail="X-Device-Id header is required")
    return x_device_id


def _prediction_to_out(p: Prediction) -> PredictionOut:
    return PredictionOut(
        id=p.id,
        match_id=p.match_id,
        predicted_outcome=p.predicted_outcome,
        model_home_prob=float(p.model_home_prob),
        model_draw_prob=float(p.model_draw_prob),
        model_away_prob=float(p.model_away_prob),
        is_correct=p.is_correct,
        model_was_correct=p.model_was_correct,
        created_at=p.created_at,
        resolved_at=p.resolved_at,
    )


@router.post("/predictions", response_model=PredictionOut)
def submit_prediction(
    body: PredictionIn,
    x_device_id: str | None = Header(None),
    db: Session = Depends(get_db),
) -> PredictionOut:
    device_id = _require_device_id(x_device_id)

    match = db.get(Match, body.match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status not in UPCOMING_MATCH_STATUSES or match.match_date <= datetime.now(timezone.utc):
        raise HTTPException(status_code=422, detail="Predictions are only accepted before kickoff")

    probs = estimate_match_probabilities(_current_elo(db, match.home_team), _current_elo(db, match.away_team))

    existing = db.scalar(
        select(Prediction).where(Prediction.device_id == device_id, Prediction.match_id == body.match_id)
    )
    if existing is None:
        existing = Prediction(device_id=device_id, match_id=body.match_id)
        db.add(existing)

    existing.predicted_outcome = body.predicted_outcome
    existing.model_home_prob = probs["home"]
    existing.model_draw_prob = probs["draw"]
    existing.model_away_prob = probs["away"]

    db.commit()
    db.refresh(existing)
    return _prediction_to_out(existing)


@router.get("/predictions/mine", response_model=PredictionOut | None)
def get_my_prediction(
    match_id: int = Query(...),
    x_device_id: str | None = Header(None),
    db: Session = Depends(get_db),
) -> PredictionOut | None:
    device_id = _require_device_id(x_device_id)

    prediction = db.scalar(
        select(Prediction).where(Prediction.device_id == device_id, Prediction.match_id == match_id)
    )
    return _prediction_to_out(prediction) if prediction else None


@router.get("/predictions/stats", response_model=PredictionStats)
def get_prediction_stats(
    x_device_id: str | None = Header(None),
    db: Session = Depends(get_db),
) -> PredictionStats:
    device_id = _require_device_id(x_device_id)

    resolved = list(
        db.scalars(
            select(Prediction).where(Prediction.device_id == device_id, Prediction.resolved_at.is_not(None))
        )
    )
    total = len(resolved)
    user_correct = sum(1 for p in resolved if p.is_correct)
    model_correct = sum(1 for p in resolved if p.model_was_correct)

    return PredictionStats(
        total_resolved=total,
        user_correct=user_correct,
        model_correct=model_correct,
        user_accuracy=(user_correct / total) if total else None,
        model_accuracy=(model_correct / total) if total else None,
    )
