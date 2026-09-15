from datetime import timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.ingest_run import IngestRun

router = APIRouter(tags=["health"])


@router.get("/healthz")
def healthz(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    last_successful = db.scalar(
        select(IngestRun.finished_at)
        .where(IngestRun.status == "success")
        .order_by(IngestRun.finished_at.desc())
        .limit(1)
    )
    return {
        "status": "ok",
        "last_successful_ingest_at": last_successful.astimezone(timezone.utc).isoformat() if last_successful else None,
    }
