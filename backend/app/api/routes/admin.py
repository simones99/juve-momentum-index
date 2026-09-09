"""Optional manual trigger for re-ingestion in production, guarded by a
shared-secret header. Intended for quick refreshes; long-running imports are
still better run via `docker compose run --rm ingest` / a Render Shell
session, since this endpoint is subject to normal HTTP request timeouts.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.ingestion.football_data_client import FootballDataClient
from app.ingestion.ingest import default_seasons, update_matches
from app.live.poller import poll_live_matches

router = APIRouter(tags=["admin"])


def _check_admin_token(x_admin_token: str | None) -> None:
    settings = get_settings()
    if not settings.admin_token:
        raise HTTPException(status_code=404, detail="Not found")
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")


@router.post("/admin/refresh")
def refresh(x_admin_token: str | None = Header(None), seasons: str | None = None) -> dict:
    _check_admin_token(x_admin_token)

    season_list = [s.strip() for s in seasons.split(",")] if seasons else default_seasons()
    update_matches(seasons=season_list)
    return {"status": "ok", "seasons": season_list}


@router.post("/admin/poll-live")
def poll_live(x_admin_token: str | None = Header(None), db: Session = Depends(get_db)) -> dict:
    """Meant to be called every couple of minutes by a scheduler (see
    scripts/scheduled_live_poll.sh) — cheap on days with no Juventus match
    (one DB query, no football-data.org call). Unlike /admin/refresh, this
    never touches Elo/momentum, only today's live status/score."""
    _check_admin_token(x_admin_token)

    settings = get_settings()
    client = FootballDataClient(api_key=settings.football_data_api_key)
    updated = poll_live_matches(db, client)
    return {"status": "ok", "polled": len(updated)}
