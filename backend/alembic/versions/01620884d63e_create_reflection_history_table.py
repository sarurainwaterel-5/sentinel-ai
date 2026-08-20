"""create reflection history table

Revision ID: 01620884d63e
Revises: 28753b490a74
Create Date: 2026-08-18 15:57:27.537243

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '01620884d63e'
down_revision: Union[str, Sequence[str], None] = '28753b490a74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create durable Reflection history."""

    op.create_table(
        "reflection_history",

        sa.Column(
            "reflection_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "mission_id",
            sa.String(),
            nullable=True,
        ),
        sa.Column(
            "session_id",
            sa.String(),
            nullable=True,
        ),
        sa.Column(
            "organization_id",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "reflected_at",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "learning_event_ids",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "pattern_ids",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "insight_ids",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "recommendation_ids",
            sa.JSON(),
            nullable=False,
        ),

        sa.Column(
            "status",
            sa.String(),
            nullable=False,
        ),
        sa.Column(
            "reflection_confidence_score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "reflection_confidence_level",
            sa.String(),
            nullable=False,
        ),

        sa.Column(
            "coherent",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "constitutional_score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "admissible",
            sa.Boolean(),
            nullable=False,
        ),

        sa.Column(
            "longitudinal_understanding_ids",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "reflective_trends",
            sa.JSON(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "reflection_id"
        ),
    )

    op.create_index(
        op.f(
            "ix_reflection_history_reflection_id"
        ),
        "reflection_history",
        ["reflection_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_reflection_history_mission_id"
        ),
        "reflection_history",
        ["mission_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_reflection_history_organization_id"
        ),
        "reflection_history",
        ["organization_id"],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_reflection_history_reflected_at"
        ),
        "reflection_history",
        ["reflected_at"],
        unique=False,
    )


def downgrade() -> None:
    """Remove durable Reflection history."""

    op.drop_index(
        op.f(
            "ix_reflection_history_reflected_at"
        ),
        table_name="reflection_history",
    )

    op.drop_index(
        op.f(
            "ix_reflection_history_organization_id"
        ),
        table_name="reflection_history",
    )

    op.drop_index(
        op.f(
            "ix_reflection_history_mission_id"
        ),
        table_name="reflection_history",
    )

    op.drop_index(
        op.f(
            "ix_reflection_history_reflection_id"
        ),
        table_name="reflection_history",
    )

    op.drop_table(
        "reflection_history"
    )
    
