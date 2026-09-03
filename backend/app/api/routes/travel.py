import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import MATCH_STATUS_SCHEDULED, TEAM_NAME
from app.core.stadiums import STADIUMS
from app.db import get_db
from app.features.travel import build_travel_estimate, estimate_fallback_travel
from app.ingestion.geocoding import GeocodingError, NominatimClient
from app.ingestion.routing import OsrmClient, RoutingError
from app.models.match import Match
from app.schemas.travel import AwayFixtureOut, AwayFixturesResponse, ResolvedLocation

router = APIRouter(tags=["travel"])
logger = logging.getLogger(__name__)


def _build_fixture_out(match: Match, from_coords: tuple[float, float]) -> AwayFixtureOut:
    stadium_info = STADIUMS.get(match.home_team)
    base = dict(
        match_id=match.id,
        opponent=match.home_team,
        match_date=match.match_date,
        competition=match.competition,
        stadium=stadium_info.name if stadium_info else match.venue,
        stadium_city=stadium_info.city if stadium_info else None,
    )

    if stadium_info is None:
        return AwayFixtureOut(
            **base,
            distance_km=None,
            duration_hours=None,
            is_estimated=False,
            effort_score=None,
            day_trip_feasible=None,
        )

    to_coords = (stadium_info.lat, stadium_info.lon)
    is_estimated = False
    try:
        distance_km, duration_hours = OsrmClient().route(
            from_coords[0], from_coords[1], to_coords[0], to_coords[1]
        )
    except RoutingError as exc:
        logger.warning("OSRM unreachable, falling back to estimated travel time: %s", exc)
        distance_km, duration_hours = estimate_fallback_travel(from_coords, to_coords)
        is_estimated = True

    estimate = build_travel_estimate(distance_km, duration_hours, is_estimated, match.match_date)

    return AwayFixtureOut(
        **base,
        distance_km=estimate.distance_km,
        duration_hours=estimate.duration_hours,
        is_estimated=estimate.is_estimated,
        effort_score=estimate.effort_score,
        day_trip_feasible=estimate.day_trip_feasible,
    )


@router.get("/travel/away-fixtures", response_model=AwayFixturesResponse)
def away_fixtures(
    from_city: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> AwayFixturesResponse:
    try:
        lat, lon, display_name = NominatimClient().geocode(from_city)
    except GeocodingError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    stmt = (
        select(Match)
        .where(
            Match.away_team == TEAM_NAME,
            Match.status == MATCH_STATUS_SCHEDULED,
            Match.match_date >= func.now(),
        )
        .order_by(Match.match_date.asc())
    )
    matches = list(db.scalars(stmt))

    fixtures = [_build_fixture_out(m, (lat, lon)) for m in matches]
    fixtures.sort(key=lambda f: (f.effort_score is None, f.effort_score))

    return AwayFixturesResponse(
        from_location=ResolvedLocation(query=from_city, display_name=display_name, lat=lat, lon=lon),
        fixtures=fixtures,
    )
