from datetime import datetime
from typing import Literal

from pydantic import BaseModel

Outcome = Literal["HOME", "DRAW", "AWAY"]


class PredictionIn(BaseModel):
    match_id: int
    predicted_outcome: Outcome


class PredictionOut(BaseModel):
    id: int
    match_id: int
    predicted_outcome: Outcome
    model_home_prob: float
    model_draw_prob: float
    model_away_prob: float
    is_correct: bool | None
    model_was_correct: bool | None
    created_at: datetime
    resolved_at: datetime | None


class PredictionStats(BaseModel):
    total_resolved: int
    user_correct: int
    model_correct: int
    user_accuracy: float | None  # None until at least one prediction is resolved
    model_accuracy: float | None
    current_streak: int  # consecutive correct predictions ending at the most recent resolved match
    best_streak: int


class PredictionCommunityStats(BaseModel):
    total_predictors: int
    total_resolved: int
    community_correct: int
    model_correct: int
    community_accuracy: float | None  # None until at least one prediction is resolved
    model_accuracy: float | None
