from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("external_id", name="uq_matches_external_id"),
        UniqueConstraint(
            "season", "competition_code", "home_team", "away_team", "match_date",
            name="uq_matches_natural_key",
        ),
        Index("ix_matches_match_date", "match_date"),
        Index("ix_matches_season", "season"),
        Index("ix_matches_teams", "home_team", "away_team"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    season: Mapped[str] = mapped_column(String(16), nullable=False)
    competition: Mapped[str] = mapped_column(String(64), nullable=False)
    competition_code: Mapped[str] = mapped_column(String(8), nullable=False)

    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    home_team: Mapped[str] = mapped_column(String(128), nullable=False)
    away_team: Mapped[str] = mapped_column(String(128), nullable=False)
    home_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)
    away_goals: Mapped[int | None] = mapped_column(Integer, nullable=True)

    venue: Mapped[str | None] = mapped_column(String(128), nullable=True)

    status: Mapped[str] = mapped_column(String(16), nullable=False, default="SCHEDULED")
    source: Mapped[str] = mapped_column(String(32), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
