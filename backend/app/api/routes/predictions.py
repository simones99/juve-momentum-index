from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.briefs.template_brief import _current_elo
from app.core.constants import UPCOMING_MATCH_STATUSES
from app.db import get_db
from app.features.win_probability import estimate_match_probabilities
from app.models.match import Match
from app.models.prediction import Prediction
from app.schemas.prediction import PredictionCommunityStats, PredictionIn, PredictionOut, PredictionStats

router = APIRouter(tags=["predictions"])


def _require_device_id(x_device_id: str | None) -> str:
    if not x_device_id:
        raise HTTPException(status_code=400, detail="X-Device-Id header is required")
    return x_device_id


def _compute_streaks(resolved_in_order: list[Prediction]) -> tuple[int, int]:
    """Longest and current run of consecutive correct predictions, in chronological order."""
    best = 0
    running = 0
    for p in resolved_in_order:
        running = running + 1 if p.is_correct else 0
        best = max(best, running)
    return running, best


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
            select(Prediction)
            .join(Match, Prediction.match_id == Match.id)
            .where(Prediction.device_id == device_id, Prediction.resolved_at.is_not(None))
            .order_by(Match.match_date)
        )
    )
    total = len(resolved)
    user_correct = sum(1 for p in resolved if p.is_correct)
    model_correct = sum(1 for p in resolved if p.model_was_correct)
    current_streak, best_streak = _compute_streaks(resolved)

    return PredictionStats(
        total_resolved=total,
        user_correct=user_correct,
        model_correct=model_correct,
        user_accuracy=(user_correct / total) if total else None,
        model_accuracy=(model_correct / total) if total else None,
        current_streak=current_streak,
        best_streak=best_streak,
    )


@router.get("/predictions/community-stats", response_model=PredictionCommunityStats)
def get_community_prediction_stats(db: Session = Depends(get_db)) -> PredictionCommunityStats:
    resolved = list(db.scalars(select(Prediction).where(Prediction.resolved_at.is_not(None))))
    total = len(resolved)
    community_correct = sum(1 for p in resolved if p.is_correct)
    model_correct = sum(1 for p in resolved if p.model_was_correct)
    total_predictors = db.scalar(
        select(func.count(func.distinct(Prediction.device_id))).where(Prediction.resolved_at.is_not(None))
    )

    return PredictionCommunityStats(
        total_predictors=total_predictors or 0,
        total_resolved=total,
        community_correct=community_correct,
        model_correct=model_correct,
        community_accuracy=(community_correct / total) if total else None,
        model_accuracy=(model_correct / total) if total else None,
    )
