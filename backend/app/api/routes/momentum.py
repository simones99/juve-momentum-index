from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.juve_momentum import JuveMomentum
from app.schemas.momentum import MomentumKpi, MomentumOverview, MomentumPoint

router = APIRouter(tags=["momentum"])


def _compute_kpi(rows: list[JuveMomentum]) -> MomentumKpi:
    """`rows` must be chronologically ascending."""
    if not rows:
        return MomentumKpi(max_momentum=None, min_momentum=None, longest_win_streak=0, current_streak=None)

    momentums = [float(r.momentum_index) for r in rows]

    longest = current = 0
    for r in rows:
        if r.result == "W":
            current += 1
            longest = max(longest, current)
        else:
            current = 0

    tail_result = rows[-1].result
    streak_len = 0
    for r in reversed(rows):
        if r.result == tail_result:
            streak_len += 1
        else:
            break
    current_streak = f"{streak_len}{tail_result}" if tail_result else None

    return MomentumKpi(
        max_momentum=max(momentums),
        min_momentum=min(momentums),
        longest_win_streak=longest,
        current_streak=current_streak,
    )


@router.get("/momentum/overview", response_model=MomentumOverview)
def momentum_overview(season: str | None = None, db: Session = Depends(get_db)) -> MomentumOverview:
    stmt = select(JuveMomentum).order_by(JuveMomentum.match_date.asc())
    if season:
        stmt = stmt.where(JuveMomentum.season == season)
    rows = list(db.scalars(stmt))
    return MomentumOverview(
        series=[MomentumPoint.model_validate(r) for r in rows],
        kpi=_compute_kpi(rows),
    )


@router.get("/momentum/series", response_model=list[MomentumPoint])
def momentum_series(
    season: str | None = None,
    competition: str | None = None,
    from_: datetime | None = Query(None, alias="from"),
    to: datetime | None = None,
    db: Session = Depends(get_db),
) -> list[MomentumPoint]:
    stmt = select(JuveMomentum).order_by(JuveMomentum.match_date.asc())
    if season:
        stmt = stmt.where(JuveMomentum.season == season)
    if competition:
        stmt = stmt.where(JuveMomentum.competition_code == competition)
    if from_:
        stmt = stmt.where(JuveMomentum.match_date >= from_)
    if to:
        stmt = stmt.where(JuveMomentum.match_date <= to)
    rows = list(db.scalars(stmt))
    return [MomentumPoint.model_validate(r) for r in rows]
