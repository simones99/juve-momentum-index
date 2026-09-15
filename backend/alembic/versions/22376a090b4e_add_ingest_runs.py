"""add ingest runs

Revision ID: 22376a090b4e
Revises: ba3da1269a3e
Create Date: 2026-09-15 15:56:40.607112

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '22376a090b4e'
down_revision: Union[str, None] = 'ba3da1269a3e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ingest_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("matches_upserted", sa.Integer(), nullable=False),
        sa.Column("source_summary", sa.String(length=256), nullable=False),
    )
    op.create_index("ix_ingest_runs_finished_at", "ingest_runs", ["finished_at"])


def downgrade() -> None:
    op.drop_index("ix_ingest_runs_finished_at", table_name="ingest_runs")
    op.drop_table("ingest_runs")
