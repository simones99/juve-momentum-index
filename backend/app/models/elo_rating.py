from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EloRating(Base):
    __tablename__ = "elo_ratings"
    __table_args__ = (UniqueConstraint("match_id", "team", name="uq_elo_ratings_match_team"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)
    team: Mapped[str] = mapped_column(String(128), nullable=False)
    elo_before: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    elo_after: Mapped[float] = mapped_column(Numeric(8, 2), nullable=False)
    rating_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
