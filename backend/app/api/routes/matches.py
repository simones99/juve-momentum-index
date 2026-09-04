from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.constants import MATCH_STATUS_FINISHED, TEAM_NAME, UPCOMING_MATCH_STATUSES
from app.db import get_db
from app.models.match import Match
from app.schemas.match import MatchListResponse, MatchOut

router = APIRouter(tags=["matches"])


def compute_result(m: Match) -> str | None:
    if m.home_goals is None or m.away_goals is None:
        return None
    is_home = m.home_team == TEAM_NAME
    goals_for = m.home_goals if is_home else m.away_goals
    goals_against = m.away_goals if is_home else m.home_goals
    if goals_for > goals_against:
        return "W"
    if goals_for < goals_against:
        return "L"
    return "D"


def match_to_out(m: Match) -> MatchOut:
    return MatchOut(
        id=m.id,
        season=m.season,
        competition=m.competition,
        competition_code=m.competition_code,
        match_date=m.match_date,
        home_team=m.home_team,
        away_team=m.away_team,
        home_goals=m.home_goals,
        away_goals=m.away_goals,
        venue=m.venue,
        status=m.status,
        result=compute_result(m),
    )


@router.get("/matches", response_model=MatchListResponse)
def list_matches(
    season: str | None = None,
    competition: str | None = None,
    home_away: str | None = Query(None, pattern="^[HA]$"),
    opponent: str | None = None,
    result: str | None = Query(None, pattern="^[WDL]$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> MatchListResponse:
    stmt = select(Match).where((Match.home_team == TEAM_NAME) | (Match.away_team == TEAM_NAME))
    if season:
        stmt = stmt.where(Match.season == season)
    if competition:
        stmt = stmt.where(Match.competition_code == competition)
    if opponent:
        stmt = stmt.where((Match.home_team == opponent) | (Match.away_team == opponent))
    if home_away == "H":
        stmt = stmt.where(Match.home_team == TEAM_NAME)
    elif home_away == "A":
        stmt = stmt.where(Match.away_team == TEAM_NAME)
    stmt = stmt.order_by(Match.match_date.desc())

    matches = list(db.scalars(stmt))
    outs = [match_to_out(m) for m in matches]
    if result:
        outs = [o for o in outs if o.result == result]

    total = len(outs)
    start = (page - 1) * page_size
    page_items = outs[start : start + page_size]

    return MatchListResponse(items=page_items, page=page, page_size=page_size, total=total)


@router.get("/matches/upcoming", response_model=list[MatchOut])
def list_upcoming_matches(
    limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)
) -> list[MatchOut]:
    stmt = (
        select(Match)
        .where(
            (Match.home_team == TEAM_NAME) | (Match.away_team == TEAM_NAME),
            Match.status.in_(UPCOMING_MATCH_STATUSES),
        )
        .order_by(Match.match_date.asc())
        .limit(limit)
    )
    return [match_to_out(m) for m in db.scalars(stmt)]


@router.get("/matches/recent", response_model=list[MatchOut])
def list_recent_matches(
    limit: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)
) -> list[MatchOut]:
    stmt = (
        select(Match)
        .where(
            (Match.home_team == TEAM_NAME) | (Match.away_team == TEAM_NAME),
            Match.status == MATCH_STATUS_FINISHED,
        )
        .order_by(Match.match_date.desc())
        .limit(limit)
    )
    return [match_to_out(m) for m in db.scalars(stmt)][::-1]


@router.get("/matches/{match_id}", response_model=MatchOut)
def get_match(match_id: int, db: Session = Depends(get_db)) -> MatchOut:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    return match_to_out(match)


@router.get("/seasons", response_model=list[str])
def list_seasons(db: Session = Depends(get_db)) -> list[str]:
    stmt = (
        select(Match.season)
        .where((Match.home_team == TEAM_NAME) | (Match.away_team == TEAM_NAME))
        .distinct()
        .order_by(Match.season.desc())
    )
    return list(db.scalars(stmt))


@router.get("/competitions", response_model=list[dict])
def list_competitions(db: Session = Depends(get_db)) -> list[dict]:
    stmt = (
        select(Match.competition_code, Match.competition)
        .where((Match.home_team == TEAM_NAME) | (Match.away_team == TEAM_NAME))
        .distinct()
    )
    return [{"code": code, "name": name} for code, name in db.execute(stmt)]
