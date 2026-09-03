from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class JuveMomentum(Base):
    __tablename__ = "juve_momentum"
    __table_args__ = (UniqueConstraint("match_id", name="uq_juve_momentum_match_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)

    season: Mapped[str] = mapped_column(String(16), nullable=False)
    match_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    opponent: Mapped[str] = mapped_column(String(128), nullable=False)
    home_away: Mapped[str] = mapped_column(String(1), nullable=False)  # "H" | "A"
    competition_code: Mapped[str] = mapped_column(String(8), nullable=False)

    result: Mapped[str | None] = mapped_column(String(1), nullable=True)  # "W" | "D" | "L"
    goals_for: Mapped[int | None] = mapped_column(Integer, nullable=True)
    goals_against: Mapped[int | None] = mapped_column(Integer, nullable=True)

    elo_before: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    elo_after: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    elo_normalized: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)

    points_rolling5: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    points_rolling10: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    goal_diff_rolling5: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)
    goal_diff_rolling10: Mapped[float | None] = mapped_column(Numeric(6, 3), nullable=True)

    momentum_index: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
