from pydantic import BaseModel


class LiveProbabilities(BaseModel):
    win: float  # from Juventus' perspective
    draw: float
    loss: float


class LiveMatchOut(BaseModel):
    match_id: int
    opponent: str
    home_away: str  # "H" | "A", Juventus' side
    status: str
    home_goals: int
    away_goals: int
    probabilities: LiveProbabilities
    is_approximate: bool = True  # see adjust_live_probabilities()'s docstring
