"""
ReflectionRecord Factory for SentinelAI.

The factory transforms one completed governed Reflection into one
historical ReflectionRecord.

It does not:

- perform Reflection,
- recalculate confidence,
- reinterpret constitutional coherence,
- alter admissibility,
- persist records,
- execute Recommendations.

Historical recording preserves cognition.

It does not create new cognition.
"""

from __future__ import annotations

from datetime import datetime

from app.services.cognition.reflection.reflection_history import (
    ReflectionRecord,
)

from app.services.cognition.reflection.reflection_orchestrator import (
    GovernedReflectionResult,
)


class ReflectionRecordFactory:
    """
    Transform governed Reflection into historical representation.
    """

    def create(
        self,
        *,
        reflection_id: str,
        governed: GovernedReflectionResult,
        reflected_at: datetime,
        mission_id: str | None = None,
        session_id: str | None = None,
        organization_id: str = "default",
        longitudinal_understanding_ids: list[str] | None = None,
        reflective_trends: list[str] | None = None,
    ) -> ReflectionRecord:
        """
        Create one historical ReflectionRecord without modifying the
        governed Reflection.
        """

        reflection = governed.reflection
        coherence = governed.coherence

        return ReflectionRecord(
            reflection_id=reflection_id,
            mission_id=mission_id,
            session_id=session_id,
            organization_id=organization_id,
            reflected_at=reflected_at,
            learning_event_ids=list(
                reflection.learning_event_ids
            ),
            pattern_ids=[
                pattern.pattern_id
                for pattern in reflection.patterns
            ],
            insight_ids=[
                insight.insight_id
                for insight in reflection.insights
            ],
            recommendation_ids=[
                recommendation.recommendation_id
                for recommendation
                in reflection.recommendations
            ],
            status=reflection.status.value,
            reflection_confidence_score=(
                reflection.confidence.score
            ),
            reflection_confidence_level=(
                reflection.confidence.level.value
            ),
            coherent=coherence.coherent,
            constitutional_score=(
                coherence.constitutional_score
            ),
            admissible=governed.admissible,
            longitudinal_understanding_ids=list(
                longitudinal_understanding_ids
                or []
            ),
            reflective_trends=list(
                reflective_trends
                or []
            ),
        )
