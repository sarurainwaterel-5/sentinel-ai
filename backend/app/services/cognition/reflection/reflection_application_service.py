"""
Reflection Application Service for SentinelAI.

The application service coordinates the public Reflection workflow.

Sequence:

1. Resolve authoritative Learning Events.
2. Produce governed Reflection.
3. Create historical ReflectionRecord.
4. Persist historical Reflection.
5. Format governed Reflection.
6. Map authoritative results to the public response contract.

The service coordinates authorities.

It does not:

- create Learning Events,
- resolve history itself,
- perform Reflection,
- calculate confidence,
- determine constitutional coherence,
- rewrite governed cognition,
- reinterpret historical Reflection,
- execute Recommendations.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import uuid4

from app.services.cognition.reflection.learning_event_resolver import (
    LearningEventResolver,
)

from app.services.cognition.reflection.reflection_api import (
    ReflectionAPIRequest,
    ReflectionAPIResponse,
)

from app.services.cognition.reflection.reflection_formatter import (
    ReflectionFormatter,
)

from app.services.cognition.reflection.reflection_orchestrator import (
    ReflectionOrchestrator,
)

from app.services.cognition.reflection.reflection_record_factory import (
    ReflectionRecordFactory,
)


class ReflectionApplicationService:
    """
    Coordinate one complete governed Reflection application workflow.

    Persistence records completed cognitive outcomes.

    Persistence does not determine their validity.
    """

    def __init__(
        self,
        *,
        resolver: LearningEventResolver,
        orchestrator: ReflectionOrchestrator,
        formatter: ReflectionFormatter,
        record_factory: ReflectionRecordFactory | None = None,
        history_repository=None,
        reflection_id_factory: Callable[[], str] | None = None,
        clock: Callable[[], datetime] | None = None,
    ):
        self.resolver = resolver
        self.orchestrator = orchestrator
        self.formatter = formatter

        self.record_factory = (
            record_factory
            or ReflectionRecordFactory()
        )

        self.history_repository = (
            history_repository
        )

        self.reflection_id_factory = (
            reflection_id_factory
            or (
                lambda: str(
                    uuid4()
                )
            )
        )

        self.clock = (
            clock
            or (
                lambda: datetime.now(
                    UTC
                )
            )
        )

    def reflect(
        self,
        request: ReflectionAPIRequest,
    ) -> ReflectionAPIResponse:
        """
        Execute one governed Reflection application workflow.
        """

        learning_events = (
            self.resolver.resolve(
                request.learning_event_ids
            )
        )

        governed = (
            self.orchestrator.reflect(
                learning_events=learning_events,
                title=request.title,
                constitutional_context=(
                    request.constitutional_context
                ),
            )
        )

        if (
            self.history_repository
            is not None
        ):
            record = (
                self.record_factory.create(
                    reflection_id=(
                        self.reflection_id_factory()
                    ),
                    governed=governed,
                    reflected_at=self.clock(),
                    mission_id=request.mission_id,
                    session_id=request.session_id,
                    organization_id=(
                        request.organization_id
                    ),
                )
            )

            self.history_repository.save(
                record
            )

        formatted = (
            self.formatter.format(
                governed
            )
        )

        reflection = governed.reflection
        coherence = governed.coherence

        human_approval_required = any(
            recommendation.requires_human_approval
            for recommendation
            in reflection.recommendations
        )

        return ReflectionAPIResponse(
            title=reflection.title,
            status=reflection.status.value,
            admissible=governed.admissible,
            coherent=coherence.coherent,
            reflection_confidence_score=(
                reflection.confidence.score
            ),
            reflection_confidence_level=(
                reflection.confidence.level.value
            ),
            constitutional_score=(
                coherence.constitutional_score
            ),
            learning_event_ids=list(
                reflection.learning_event_ids
            ),
            pattern_count=len(
                reflection.patterns
            ),
            insight_count=len(
                reflection.insights
            ),
            recommendation_count=len(
                reflection.recommendations
            ),
            human_approval_required=(
                human_approval_required
            ),
            formatted_reflection=formatted,
            mission_id=request.mission_id,
            session_id=request.session_id,
            organization_id=(
                request.organization_id
            ),
        )
