"""
Contract tests for SentinelAI's governed Reflection Orchestrator.

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

from copy import deepcopy

from app.services.cognition.reflection.models import (
    ReflectionConfidence,
    ReflectionConfidenceLevel,
    ReflectionInsight,
    ReflectionPattern,
    ReflectionPatternKind,
    ReflectionRecommendation,
    ReflectionRecommendationKind,
    ReflectionResult,
    ReflectionStatus,
)

from app.services.cognition.reflection.reflection_coherence_evaluator import (
    ReflectionCoherenceResult,
)

from app.services.cognition.reflection.reflection_orchestrator import (
    GovernedReflectionResult,
    ReflectionOrchestrator,
)


def make_reflection(
    *,
    confidence_score: float = 0.90,
) -> ReflectionResult:
    pattern = ReflectionPattern(
        pattern_id="pattern-1",
        kind=ReflectionPatternKind.RECURRENCE,
        title="Recurring engineering learning",
        description=(
            "Engineering recurs across accumulated learning."
        ),
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "engineering",
        ],
    )

    insight = ReflectionInsight(
        insight_id="insight-1",
        title="Engineering remains recurrent",
        explanation=(
            "The established Pattern shows recurring "
            "engineering learning."
        ),
        pattern_ids=[
            "pattern-1",
        ],
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "engineering",
        ],
        confidence=confidence_score,
    )

    recommendation = ReflectionRecommendation(
        recommendation_id="recommendation-1",
        kind=ReflectionRecommendationKind.STRENGTHEN,
        title="Continue engineering learning",
        description=(
            "Continue examining the established learning area."
        ),
        insight_ids=[
            "insight-1",
        ],
        pattern_ids=[
            "pattern-1",
        ],
        domain_ids=[
            "engineering",
        ],
        priority=1,
        requires_human_approval=True,
    )

    return ReflectionResult(
        title="Engineering reflection",
        summary="Reflection completed.",
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        patterns=[
            pattern,
        ],
        insights=[
            insight,
        ],
        recommendations=[
            recommendation,
        ],
        confidence=ReflectionConfidence(
            score=confidence_score,
            level=ReflectionConfidenceLevel.HIGH,
            basis="Reflective support was assessed.",
            factors=[],
            uncertainty=[],
        ),
        reflection_trace=[
            "History analyzed.",
            "Patterns discovered.",
            "Insights generated.",
            "Recommendations generated.",
            "Confidence evaluated.",
        ],
        status=ReflectionStatus.COMPLETE,
    )


def make_coherence(
    *,
    coherent: bool = True,
    admissible: bool = True,
    constitutional_score: float = 1.0,
    reflection_confidence: float = 0.90,
    conflicts: list[str] | None = None,
) -> ReflectionCoherenceResult:
    return ReflectionCoherenceResult(
        coherent=coherent,
        admissible=admissible,
        constitutional_score=constitutional_score,
        reflection_confidence=reflection_confidence,
        articles_consulted=[],
        conflicts=conflicts or [],
        recommendations=[],
    )


class StubReflectionEngine:
    def __init__(
        self,
        result: ReflectionResult,
    ):
        self.result = result
        self.calls = 0
        self.received_events = None
        self.received_title = None

    def reflect(
        self,
        *,
        learning_events,
        title,
    ):
        self.calls += 1
        self.received_events = learning_events
        self.received_title = title

        return self.result


class StubCoherenceEvaluator:
    def __init__(
        self,
        result: ReflectionCoherenceResult,
    ):
        self.result = result
        self.calls = 0
        self.received_reflection = None
        self.received_context = None

    def evaluate(
        self,
        *,
        reflection,
        constitutional_context,
    ):
        self.calls += 1
        self.received_reflection = reflection
        self.received_context = constitutional_context

        return self.result


def test_orchestrator_coordinates_reflection_and_coherence():
    reflection = make_reflection()
    coherence = make_coherence()

    reflection_engine = StubReflectionEngine(
        reflection
    )

    coherence_evaluator = StubCoherenceEvaluator(
        coherence
    )

    orchestrator = ReflectionOrchestrator(
        reflection_engine=reflection_engine,
        coherence_evaluator=coherence_evaluator,
    )

    result = orchestrator.reflect(
        learning_events=[],
        title="Engineering reflection",
        constitutional_context=(
            "Reflection remains accountable to reality."
        ),
    )

    assert isinstance(
        result,
        GovernedReflectionResult,
    )

    assert reflection_engine.calls == 1
    assert coherence_evaluator.calls == 1

    assert result.reflection == reflection
    assert result.coherence == coherence


def test_reflection_is_evaluated_before_constitutional_judgment():
    reflection = make_reflection()
    coherence = make_coherence()

    reflection_engine = StubReflectionEngine(
        reflection
    )

    coherence_evaluator = StubCoherenceEvaluator(
        coherence
    )

    orchestrator = ReflectionOrchestrator(
        reflection_engine=reflection_engine,
        coherence_evaluator=coherence_evaluator,
    )

    orchestrator.reflect(
        learning_events=[],
        title="Ordered reflection",
        constitutional_context="Constitution.",
    )

    assert (
        coherence_evaluator.received_reflection
        is reflection
    )


def test_coherent_reflection_is_admissible():
    orchestrator = ReflectionOrchestrator(
        reflection_engine=StubReflectionEngine(
            make_reflection()
        ),
        coherence_evaluator=StubCoherenceEvaluator(
            make_coherence(
                coherent=True,
                admissible=True,
            )
        ),
    )

    result = orchestrator.reflect(
        learning_events=[],
        title="Coherent reflection",
        constitutional_context="Constitution.",
    )

    assert result.admissible is True
    assert result.coherence.coherent is True


def test_incoherent_reflection_is_blocked():
    orchestrator = ReflectionOrchestrator(
        reflection_engine=StubReflectionEngine(
            make_reflection(
                confidence_score=0.99,
            )
        ),
        coherence_evaluator=StubCoherenceEvaluator(
            make_coherence(
                coherent=False,
                admissible=False,
                constitutional_score=0.10,
                reflection_confidence=0.99,
                conflicts=[
                    "Constitutional conflict detected.",
                ],
            )
        ),
    )

    result = orchestrator.reflect(
        learning_events=[],
        title="Incoherent reflection",
        constitutional_context="Constitution.",
    )

    assert result.admissible is False
    assert result.reflection.confidence.score == 0.99
    assert result.coherence.coherent is False
    assert result.coherence.conflicts


def test_orchestrator_does_not_average_confidence_and_coherence():
    orchestrator = ReflectionOrchestrator(
        reflection_engine=StubReflectionEngine(
            make_reflection(
                confidence_score=0.99,
            )
        ),
        coherence_evaluator=StubCoherenceEvaluator(
            make_coherence(
                coherent=False,
                admissible=False,
                constitutional_score=0.10,
                reflection_confidence=0.99,
            )
        ),
    )

    result = orchestrator.reflect(
        learning_events=[],
        title="Independent judgments",
        constitutional_context="Constitution.",
    )

    assert result.reflection.confidence.score == 0.99
    assert result.coherence.constitutional_score == 0.10
    assert result.admissible is False

    assert not hasattr(
        result,
        "combined_score",
    )


def test_orchestrator_preserves_reflection():
    reflection = make_reflection()
    before = deepcopy(reflection)

    orchestrator = ReflectionOrchestrator(
        reflection_engine=StubReflectionEngine(
            reflection
        ),
        coherence_evaluator=StubCoherenceEvaluator(
            make_coherence(
                coherent=False,
                admissible=False,
                constitutional_score=0.20,
                conflicts=[
                    "Reflection is constitutionally incoherent.",
                ],
            )
        ),
    )

    orchestrator.reflect(
        learning_events=[],
        title="Immutable reflection",
        constitutional_context="Constitution.",
    )

    assert reflection == before


def test_orchestrator_preserves_human_approval_boundary():
    reflection = make_reflection()

    orchestrator = ReflectionOrchestrator(
        reflection_engine=StubReflectionEngine(
            reflection
        ),
        coherence_evaluator=StubCoherenceEvaluator(
            make_coherence()
        ),
    )

    result = orchestrator.reflect(
        learning_events=[],
        title="Governed recommendation",
        constitutional_context="Constitution.",
    )

    assert result.admissible is True

    assert (
        result.reflection
        .recommendations[0]
        .requires_human_approval
        is True
    )

    assert not hasattr(
        result,
        "execution_authorized",
    )


def test_constitutional_context_reaches_evaluator_unchanged():
    coherence_evaluator = StubCoherenceEvaluator(
        make_coherence()
    )

    orchestrator = ReflectionOrchestrator(
        reflection_engine=StubReflectionEngine(
            make_reflection()
        ),
        coherence_evaluator=coherence_evaluator,
    )

    context = (
        "Reflection remains accountable to reality "
        "and preserves historical cognition."
    )

    orchestrator.reflect(
        learning_events=[],
        title="Context reflection",
        constitutional_context=context,
    )

    assert (
        coherence_evaluator.received_context
        == context
    )


def test_governed_result_contains_no_user_facing_answer():
    orchestrator = ReflectionOrchestrator(
        reflection_engine=StubReflectionEngine(
            make_reflection()
        ),
        coherence_evaluator=StubCoherenceEvaluator(
            make_coherence()
        ),
    )

    result = orchestrator.reflect(
        learning_events=[],
        title="Structured result",
        constitutional_context="Constitution.",
    )

    assert not hasattr(
        result,
        "answer",
    )

    assert not hasattr(
        result,
        "formatted_response",
    )


def test_governed_result_contains_no_execution_authority():
    orchestrator = ReflectionOrchestrator(
        reflection_engine=StubReflectionEngine(
            make_reflection()
        ),
        coherence_evaluator=StubCoherenceEvaluator(
            make_coherence()
        ),
    )

    result = orchestrator.reflect(
        learning_events=[],
        title="No execution",
        constitutional_context="Constitution.",
    )

    assert not hasattr(
        result,
        "execute",
    )

    assert not hasattr(
        result,
        "execution_authorized",
    )

    assert not hasattr(
        result,
        "execution_result",
    )
