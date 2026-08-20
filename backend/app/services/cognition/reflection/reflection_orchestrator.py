"""
Governed Reflection Orchestrator for SentinelAI.

The Reflection Orchestrator coordinates:

Learning Events
    ->
Reflection Engine
    ->
Reflection Result
    ->
Constitutional Coherence
    ->
Governed Reflection Result

It does not:

- perform Reflection itself,
- calculate Reflection confidence,
- determine constitutional coherence itself,
- rewrite reflective cognition,
- repair constitutional conflicts,
- execute Recommendations,
- format user-facing communication.

Cognition produces Reflection.

Constitution governs admissibility.

Orchestration preserves both judgments.
"""

from __future__ import annotations

from pydantic import BaseModel

from app.core.cognition.models import (
    LearningEvent,
)

from app.services.cognition.reflection.models import (
    ReflectionResult,
)

from app.services.cognition.reflection.reflection_coherence_evaluator import (
    ReflectionCoherenceEvaluator,
    ReflectionCoherenceResult,
)

from app.services.cognition.reflection.reflection_engine import (
    ReflectionEngine,
)


class GovernedReflectionResult(BaseModel):
    """
    One Reflection together with its constitutional judgment.

    This object preserves separate cognitive and governance authorities.

    It does not grant execution authority.
    """

    reflection: ReflectionResult

    coherence: ReflectionCoherenceResult

    admissible: bool


class ReflectionOrchestrator:
    """
    Coordinate Reflection and constitutional evaluation.

    The orchestrator owns sequencing.

    ReflectionEngine owns reflective cognition.

    ReflectionCoherenceEvaluator owns constitutional admissibility.
    """

    def __init__(
        self,
        *,
        reflection_engine=None,
        coherence_evaluator=None,
    ):
        self.reflection_engine = (
            reflection_engine
            or ReflectionEngine()
        )

        self.coherence_evaluator = (
            coherence_evaluator
            or ReflectionCoherenceEvaluator()
        )

    def reflect(
        self,
        *,
        learning_events: list[LearningEvent],
        title: str,
        constitutional_context: str,
    ) -> GovernedReflectionResult:
        """
        Execute one governed Reflection operation.

        Sequence:

        1. Produce authoritative Reflection.
        2. Submit that exact Reflection to constitutional evaluation.
        3. Preserve both judgments without combining them.
        4. Derive governed admissibility exclusively from Constitution.
        """

        reflection = (
            self.reflection_engine.reflect(
                learning_events=learning_events,
                title=title,
            )
        )

        coherence = (
            self.coherence_evaluator.evaluate(
                reflection=reflection,
                constitutional_context=constitutional_context,
            )
        )

        return GovernedReflectionResult(
            reflection=reflection,
            coherence=coherence,
            admissible=coherence.admissible,
        )
