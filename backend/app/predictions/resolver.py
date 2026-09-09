"""Resolves predictions against the real outcome once a Juventus match
finishes. Called once per FINISHED match (see `update_matches`); safe to
call repeatedly, since it only touches predictions that don't yet have
`resolved_at` set.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.match import Match
from app.models.prediction import Prediction


def _actual_outcome(match: Match) -> str:
    if match.home_goals > match.away_goals:
        return "HOME"
    if match.home_goals < match.away_goals:
        return "AWAY"
    return "DRAW"


def _model_outcome(prediction: Prediction) -> str:
    probs = {
        "HOME": float(prediction.model_home_prob),
        "DRAW": float(prediction.model_draw_prob),
        "AWAY": float(prediction.model_away_prob),
    }
    return max(probs, key=probs.get)


def resolve_predictions(db: Session, match: Match) -> int:
    """Resolves every not-yet-resolved prediction for `match`. Returns the
    number of predictions resolved (0 if the match has no final score yet,
    or nothing was left unresolved)."""
    if match.home_goals is None or match.away_goals is None:
        return 0

    unresolved = list(
        db.scalars(select(Prediction).where(Prediction.match_id == match.id, Prediction.resolved_at.is_(None)))
    )
    if not unresolved:
        return 0

    actual = _actual_outcome(match)
    now = datetime.now(timezone.utc)
    for prediction in unresolved:
        prediction.is_correct = prediction.predicted_outcome == actual
        prediction.model_was_correct = _model_outcome(prediction) == actual
        prediction.resolved_at = now

    db.commit()
    return len(unresolved)
