from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    season: str
    competition: str
    competition_code: str
    match_date: datetime
    home_team: str
    away_team: str
    home_goals: int | None
    away_goals: int | None
    venue: str | None = None
    status: str
    result: str | None = None  # W/D/L from Juventus' perspective, None if not yet played


class MatchListResponse(BaseModel):
    items: list[MatchOut]
    page: int
    page_size: int
    total: int


class CompetitionOut(BaseModel):
    code: str
    name: str
