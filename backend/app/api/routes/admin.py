"""Optional manual trigger for re-ingestion in production, guarded by a
shared-secret header. Intended for quick refreshes; long-running imports are
still better run via `docker compose run --rm ingest` / a Render Shell
session, since this endpoint is subject to normal HTTP request timeouts.
"""

from fastapi import APIRouter, Header, HTTPException

from app.config import get_settings
from app.ingestion.ingest import default_seasons, update_matches

router = APIRouter(tags=["admin"])


@router.post("/admin/refresh")
def refresh(x_admin_token: str | None = Header(None), seasons: str | None = None) -> dict:
    settings = get_settings()
    if not settings.admin_token:
        raise HTTPException(status_code=404, detail="Not found")
    if x_admin_token != settings.admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")

    season_list = [s.strip() for s in seasons.split(",")] if seasons else default_seasons()
    update_matches(seasons=season_list)
    return {"status": "ok", "seasons": season_list}
