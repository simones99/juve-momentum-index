"""init schema

Revision ID: ee2b2f8323b5
Revises: 
Create Date: 2026-09-03 18:52:43.722210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ee2b2f8323b5'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(length=64), nullable=True),
        sa.Column("season", sa.String(length=16), nullable=False),
        sa.Column("competition", sa.String(length=64), nullable=False),
        sa.Column("competition_code", sa.String(length=8), nullable=False),
        sa.Column("match_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("home_team", sa.String(length=128), nullable=False),
        sa.Column("away_team", sa.String(length=128), nullable=False),
        sa.Column("home_goals", sa.Integer(), nullable=True),
        sa.Column("away_goals", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False, server_default="SCHEDULED"),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("external_id", name="uq_matches_external_id"),
        sa.UniqueConstraint(
            "season", "competition_code", "home_team", "away_team", "match_date",
            name="uq_matches_natural_key",
        ),
    )
    op.create_index("ix_matches_match_date", "matches", ["match_date"])
    op.create_index("ix_matches_season", "matches", ["season"])
    op.create_index("ix_matches_teams", "matches", ["home_team", "away_team"])

    op.create_table(
        "elo_ratings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "match_id", sa.Integer(),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("team", sa.String(length=128), nullable=False),
        sa.Column("elo_before", sa.Numeric(8, 2), nullable=False),
        sa.Column("elo_after", sa.Numeric(8, 2), nullable=False),
        sa.Column("rating_date", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("match_id", "team", name="uq_elo_ratings_match_team"),
    )

    op.create_table(
        "juve_momentum",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "match_id", sa.Integer(),
            sa.ForeignKey("matches.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column("season", sa.String(length=16), nullable=False),
        sa.Column("match_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opponent", sa.String(length=128), nullable=False),
        sa.Column("home_away", sa.String(length=1), nullable=False),
        sa.Column("competition_code", sa.String(length=8), nullable=False),
        sa.Column("result", sa.String(length=1), nullable=True),
        sa.Column("goals_for", sa.Integer(), nullable=True),
        sa.Column("goals_against", sa.Integer(), nullable=True),
        sa.Column("elo_before", sa.Numeric(8, 2), nullable=False),
        sa.Column("elo_after", sa.Numeric(8, 2), nullable=False),
        sa.Column("elo_normalized", sa.Numeric(6, 2), nullable=False),
        sa.Column("points_rolling5", sa.Numeric(6, 3), nullable=True),
        sa.Column("points_rolling10", sa.Numeric(6, 3), nullable=True),
        sa.Column("goal_diff_rolling5", sa.Numeric(6, 3), nullable=True),
        sa.Column("goal_diff_rolling10", sa.Numeric(6, 3), nullable=True),
        sa.Column("momentum_index", sa.Numeric(6, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("match_id", name="uq_juve_momentum_match_id"),
    )


def downgrade() -> None:
    op.drop_table("juve_momentum")
    op.drop_table("elo_ratings")
    op.drop_index("ix_matches_teams", table_name="matches")
    op.drop_index("ix_matches_season", table_name="matches")
    op.drop_index("ix_matches_match_date", table_name="matches")
    op.drop_table("matches")
