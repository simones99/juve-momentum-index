from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MomentumPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    match_id: int
    match_date: datetime
    season: str
    opponent: str
    home_away: str
    competition_code: str
    result: str | None
    goals_for: int | None
    goals_against: int | None
    elo_before: float
    elo_after: float
    elo_normalized: float
    points_rolling5: float | None
    points_rolling10: float | None
    goal_diff_rolling5: float | None
    goal_diff_rolling10: float | None
    momentum_index: float


class MomentumKpi(BaseModel):
    max_momentum: float | None
    min_momentum: float | None
    longest_win_streak: int
    current_streak: str | None


class MomentumOverview(BaseModel):
    series: list[MomentumPoint]
    kpi: MomentumKpi
