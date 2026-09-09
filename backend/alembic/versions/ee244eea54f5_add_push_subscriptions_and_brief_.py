"""add push subscriptions and brief notified at

Revision ID: ee244eea54f5
Revises: 0093ec837108
Create Date: 2026-09-09 11:34:43.536997

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee244eea54f5'
down_revision: Union[str, None] = '0093ec837108'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("brief_notified_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "push_subscriptions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("endpoint", sa.String(length=512), nullable=False),
        sa.Column("p256dh", sa.String(length=256), nullable=False),
        sa.Column("auth", sa.String(length=256), nullable=False),
        sa.Column("device_id", sa.String(length=64), nullable=True),
        sa.Column("locale", sa.String(length=8), nullable=False, server_default="it"),
        sa.Column("notify_kickoff", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notify_brief", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notify_momentum", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("endpoint", name="uq_push_subscriptions_endpoint"),
    )
    op.create_index("ix_push_subscriptions_device_id", "push_subscriptions", ["device_id"])


def downgrade() -> None:
    op.drop_index("ix_push_subscriptions_device_id", table_name="push_subscriptions")
    op.drop_table("push_subscriptions")
    op.drop_column("matches", "brief_notified_at")
