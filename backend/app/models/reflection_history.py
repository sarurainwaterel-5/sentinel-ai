"""
SQLAlchemy persistence model for SentinelAI Reflection history.

This model stores historical Reflection records.

It is a persistence representation only.

It does not perform Reflection,
interpret cognition,
or grant execution authority.
"""

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    JSON,
    String,
    Text,
)

from app.database import Base


class ReflectionHistoryRecordModel(Base):
    """
    Persistent row representation of one ReflectionRecord.
    """

    __tablename__ = "reflection_history"

    reflection_id = Column(
        String,
        primary_key=True,
        index=True,
    )

    mission_id = Column(
        String,
        nullable=True,
        index=True,
    )

    session_id = Column(
        String,
        nullable=True,
    )

    organization_id = Column(
        String,
        nullable=False,
        default="default",
        index=True,
    )

    # Stored as exact ISO-8601 text so timezone/provenance survives
    # round-trip without dialect-dependent DateTime coercion.
    reflected_at = Column(
        String,
        nullable=False,
        index=True,
    )

    learning_event_ids = Column(
        JSON,
        nullable=False,
        default=list,
    )

    pattern_ids = Column(
        JSON,
        nullable=False,
        default=list,
    )

    insight_ids = Column(
        JSON,
        nullable=False,
        default=list,
    )

    recommendation_ids = Column(
        JSON,
        nullable=False,
        default=list,
    )

    status = Column(
        String,
        nullable=False,
    )

    reflection_confidence_score = Column(
        Float,
        nullable=False,
    )

    reflection_confidence_level = Column(
        String,
        nullable=False,
    )

    coherent = Column(
        Boolean,
        nullable=False,
    )

    constitutional_score = Column(
        Float,
        nullable=False,
    )

    admissible = Column(
        Boolean,
        nullable=False,
    )

    longitudinal_understanding_ids = Column(
        JSON,
        nullable=False,
        default=list,
    )

    reflective_trends = Column(
        JSON,
        nullable=False,
        default=list,
    )
