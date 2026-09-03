from datetime import datetime

from pydantic import BaseModel


class ResolvedLocation(BaseModel):
    query: str
    display_name: str
    lat: float
    lon: float


class AwayFixtureOut(BaseModel):
    match_id: int
    opponent: str
    match_date: datetime
    competition: str
    stadium: str | None
    stadium_city: str | None
    distance_km: float | None
    duration_hours: float | None
    is_estimated: bool
    effort_score: float | None
    day_trip_feasible: bool | None


class AwayFixturesResponse(BaseModel):
    from_location: ResolvedLocation
    fixtures: list[AwayFixtureOut]
