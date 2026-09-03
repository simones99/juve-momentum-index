"""add venue to matches

Revision ID: 0093ec837108
Revises: ee2b2f8323b5
Create Date: 2026-09-03 21:46:13.273228

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0093ec837108'
down_revision: Union[str, None] = 'ee2b2f8323b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("matches", sa.Column("venue", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("matches", "venue")
