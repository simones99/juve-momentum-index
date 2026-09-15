"""Tracks each ingestion run so the app can show data freshness (see
/healthz and the site footer) instead of leaving staleness invisible.
"""

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class IngestRun(Base):
    __tablename__ = "ingest_runs"
    __table_args__ = (Index("ix_ingest_runs_finished_at", "finished_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    matches_upserted: Mapped[int] = mapped_column(Integer, nullable=False)
    source_summary: Mapped[str] = mapped_column(String(256), nullable=False)
