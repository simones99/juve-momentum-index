from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (
        UniqueConstraint("device_id", "match_id", name="uq_predictions_device_match"),
        Index("ix_predictions_device_id", "device_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    device_id: Mapped[str] = mapped_column(String(64), nullable=False)
    match_id: Mapped[int] = mapped_column(ForeignKey("matches.id", ondelete="CASCADE"), nullable=False)

    predicted_outcome: Mapped[str] = mapped_column(String(4), nullable=False)  # "HOME" | "DRAW" | "AWAY"

    # Snapshot of the model's own pre-match probabilities at submission time,
    # so /predictions/stats can compare "you vs the model" without needing
    # historical Elo — the model's answer is whatever it said back then.
    model_home_prob: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    model_draw_prob: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    model_away_prob: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)

    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    model_was_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
