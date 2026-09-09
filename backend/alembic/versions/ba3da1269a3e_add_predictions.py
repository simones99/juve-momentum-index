"""add predictions

Revision ID: ba3da1269a3e
Revises: ee244eea54f5
Create Date: 2026-09-09 14:35:18.930704

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ba3da1269a3e'
down_revision: Union[str, None] = 'ee244eea54f5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("device_id", sa.String(length=64), nullable=False),
        sa.Column(
            "match_id", sa.Integer(),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("predicted_outcome", sa.String(length=4), nullable=False),
        sa.Column("model_home_prob", sa.Numeric(5, 4), nullable=False),
        sa.Column("model_draw_prob", sa.Numeric(5, 4), nullable=False),
        sa.Column("model_away_prob", sa.Numeric(5, 4), nullable=False),
        sa.Column("is_correct", sa.Boolean(), nullable=True),
        sa.Column("model_was_correct", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("device_id", "match_id", name="uq_predictions_device_match"),
    )
    op.create_index("ix_predictions_device_id", "predictions", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_predictions_device_id", table_name="predictions")
    op.drop_table("predictions")
