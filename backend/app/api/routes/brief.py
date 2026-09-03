from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.briefs.service import get_post_match_brief, get_pre_match_brief
from app.core.constants import MATCH_STATUS_FINISHED, MATCH_STATUS_SCHEDULED, TEAM_NAME
from app.db import get_db
from app.models.match import Match
from app.schemas.brief import BriefResponse

router = APIRouter(tags=["brief"])


@router.get("/matches/{match_id}/brief", response_model=BriefResponse)
def match_brief(
    match_id: int, n: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)
) -> BriefResponse:
    match = db.get(Match, match_id)
    if match is None:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status != MATCH_STATUS_FINISHED:
        raise HTTPException(
            status_code=404,
            detail="Match not finished yet; use /brief/next for upcoming fixtures",
        )
    try:
        return get_post_match_brief(db, match_id, n)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/brief/next", response_model=BriefResponse)
def next_match_brief(n: int = Query(5, ge=1, le=20), db: Session = Depends(get_db)) -> BriefResponse:
    stmt = (
        select(Match)
        .where(
            (Match.home_team == TEAM_NAME) | (Match.away_team == TEAM_NAME),
            Match.status == MATCH_STATUS_SCHEDULED,
        )
        .order_by(Match.match_date.asc())
        .limit(1)
    )
    next_match = db.scalar(stmt)
    opponent = None
    if next_match:
        opponent = next_match.away_team if next_match.home_team == TEAM_NAME else next_match.home_team
    return get_pre_match_brief(db, opponent, n)
