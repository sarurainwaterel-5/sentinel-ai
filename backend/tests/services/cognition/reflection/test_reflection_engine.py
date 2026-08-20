"""
Contract tests for SentinelAI's modern Reflection Engine.

The Reflection Engine coordinates one complete reflective operation.

It does not:

- analyze history directly,
- discover Patterns directly,
- generate Insights directly,
- generate Recommendations directly,
- calculate constitutional coherence,
- format human-readable communication,
- execute recommendations,
- modify Learning Events.

The Engine coordinates cognition.

Specialists own cognition.
"""

from copy import deepcopy

from app.core.cognition.models import LearningEvent

from app.services.cognition.reflection.history_analyzer import (
    ReflectionHistoryAssessment,
    ReflectionHistoryStatus,
)

from app.services.cognition.reflection.models import (
    ReflectionConfidence,
    ReflectionConfidenceLevel,
    ReflectionInsight,
    ReflectionPattern,
    ReflectionPatternKind,
    ReflectionRecommendation,
    ReflectionRecommendationKind,
    ReflectionStatus,
)

from app.services.cognition.reflection.reflection_engine import (
    ReflectionEngine,
)


def make_event(
    *,
    event_id: str,
    domains: list[str] | None = None,
    evidence: list[str] | None = None,
) -> LearningEvent:
    return LearningEvent(
        learning_event_id=event_id,
        source=f"source-{event_id}",
        domain_ids=(
            domains
            or ["engineering"]
        ),
        evidence_added=(
            evidence
            or ["evidence-1"]
        ),
        summary=f"Learning recorded for {event_id}.",
    )


def make_history(
    *,
    status: ReflectionHistoryStatus = (
        ReflectionHistoryStatus.SUFFICIENT
    ),
    event_count: int = 2,
) -> ReflectionHistoryAssessment:
    return ReflectionHistoryAssessment(
        status=status,
        event_count=event_count,
        history_sufficient=(
            status
            == ReflectionHistoryStatus.SUFFICIENT
        ),
        learning_event_ids=[
            f"learning-{i}"
            for i in range(1, event_count + 1)
        ],
        domain_ids=["engineering"],
        shared_domain_ids=(
            ["engineering"]
            if status
            == ReflectionHistoryStatus.SUFFICIENT
            else []
        ),
        evidence_ids=["evidence-1"],
        evidence_count=1,
        events_with_evidence=event_count,
        evidence_coverage=(
            1.0
            if event_count
            else 0.0
        ),
        temporal_span_seconds=86400.0,
        limitations=[],
    )


def make_pattern(
    *,
    learning_event_ids: list[str] | None = None,
) -> ReflectionPattern:
    return ReflectionPattern(
        pattern_id="pattern-1",
        kind=ReflectionPatternKind.RECURRENCE,
        title="Recurring domain: engineering",
        description=(
            "Engineering recurs across Learning Events."
        ),
        learning_event_ids=(
            learning_event_ids
            or [
                "learning-1",
                "learning-2",
            ]
        ),
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "engineering",
        ],
    )

def make_insight(
    *,
    learning_event_ids: list[str] | None = None,
) -> ReflectionInsight:
    return ReflectionInsight(
        insight_id="insight-1",
        title="Recurring learning area: engineering",
        explanation=(
            "Engineering represents a repeated area "
            "within the examined learning history."
        ),
        pattern_ids=[
            "pattern-1",
        ],
        learning_event_ids=(
            learning_event_ids
            or [
                "learning-1",
                "learning-2",
            ]
        ),
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "engineering",
        ],
        confidence=0.80,
    )


def make_recommendation() -> ReflectionRecommendation:
    return ReflectionRecommendation(
        recommendation_id="recommendation-1",
        kind=ReflectionRecommendationKind.STRENGTHEN,
        title="Continue examining engineering",
        description=(
            "Future learning should continue examining "
            "the established engineering Insight."
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


def make_confidence(
    *,
    score: float = 0.84,
) -> ReflectionConfidence:
    return ReflectionConfidence(
        score=score,
        level=(
            ReflectionConfidenceLevel.HIGH
            if score >= 0.75
            else ReflectionConfidenceLevel.LOW
        ),
        basis="Reflective support was assessed.",
        factors=[],
        uncertainty=[],
    )


class StubHistoryAnalyzer:
    def __init__(
        self,
        result: ReflectionHistoryAssessment,
    ):
        self.result = result
        self.calls = 0

    def analyze(
        self,
        learning_events,
    ):
        self.calls += 1
        return self.result


class StubPatternDiscoverer:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.calls = 0

    def discover(
        self,
        learning_events,
    ):
        self.calls += 1
        return self.result


class StubInsightGenerator:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.calls = 0

    def generate(
        self,
        patterns,
    ):
        self.calls += 1
        return self.result


class StubRecommendationGenerator:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.calls = 0

    def generate(
        self,
        insights,
    ):
        self.calls += 1
        return self.result


class StubConfidenceEngine:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.calls = 0

    def evaluate(
        self,
        *,
        history,
        patterns,
        insights,
        recommendations,
    ):
        self.calls += 1
        return self.result


def make_engine(
    *,
    history=None,
    patterns=None,
    insights=None,
    recommendations=None,
    confidence=None,
):
    history_analyzer = StubHistoryAnalyzer(
        history or make_history()
    )

    pattern_discoverer = StubPatternDiscoverer(
        patterns
        if patterns is not None
        else [make_pattern()]
    )

    insight_generator = StubInsightGenerator(
        insights
        if insights is not None
        else [make_insight()]
    )

    recommendation_generator = (
        StubRecommendationGenerator(
            recommendations
            if recommendations is not None
            else [make_recommendation()]
        )
    )

    confidence_engine = StubConfidenceEngine(
        confidence or make_confidence()
    )

    engine = ReflectionEngine(
        history_analyzer=history_analyzer,
        pattern_discoverer=pattern_discoverer,
        insight_generator=insight_generator,
        recommendation_generator=(
            recommendation_generator
        ),
        confidence_engine=confidence_engine,
    )

    return (
        engine,
        history_analyzer,
        pattern_discoverer,
        insight_generator,
        recommendation_generator,
        confidence_engine,
    )


def test_engine_coordinates_complete_reflection():
    """
    Sufficient history should flow through every specialist and produce
    one authoritative ReflectionResult.
    """

    (
        engine,
        history_analyzer,
        pattern_discoverer,
        insight_generator,
        recommendation_generator,
        confidence_engine,
    ) = make_engine()

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ],
        title="Engineering reflection",
    )

    assert result.status == ReflectionStatus.COMPLETE

    assert len(result.patterns) == 1
    assert len(result.insights) == 1
    assert len(result.recommendations) == 1

    assert history_analyzer.calls == 1
    assert pattern_discoverer.calls == 1
    assert insight_generator.calls == 1
    assert recommendation_generator.calls == 1
    assert confidence_engine.calls == 1


def test_insufficient_history_stops_downstream_cognition():
    """
    Pattern Discovery must not run when historical prerequisites are
    unsatisfied.
    """

    (
        engine,
        history_analyzer,
        pattern_discoverer,
        insight_generator,
        recommendation_generator,
        confidence_engine,
    ) = make_engine(
        history=make_history(
            status=(
                ReflectionHistoryStatus
                .INSUFFICIENT_HISTORY
            ),
            event_count=1,
        ),
        patterns=[],
        insights=[],
        recommendations=[],
        confidence=make_confidence(
            score=0.20,
        ),
    )

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-1",
            ),
        ],
        title="Limited reflection",
    )

    assert (
        result.status
        == ReflectionStatus.INSUFFICIENT_EVIDENCE
    )

    assert result.patterns == []
    assert result.insights == []
    assert result.recommendations == []

    assert history_analyzer.calls == 1

    assert pattern_discoverer.calls == 0
    assert insight_generator.calls == 0
    assert recommendation_generator.calls == 0

    # Confidence may still assess the failed reflective basis.
    assert confidence_engine.calls == 1


def test_insufficient_comparability_stops_pattern_discovery():
    """
    Multiple events are not sufficient when they lack a comparable
    reflective basis.
    """

    (
        engine,
        _,
        pattern_discoverer,
        insight_generator,
        recommendation_generator,
        _,
    ) = make_engine(
        history=make_history(
            status=(
                ReflectionHistoryStatus
                .INSUFFICIENT_COMPARABILITY
            ),
            event_count=2,
        ),
        patterns=[],
        insights=[],
        recommendations=[],
        confidence=make_confidence(
            score=0.30,
        ),
    )

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["trading"],
            ),
        ],
        title="Cross-domain reflection",
    )

    assert (
        result.status
        == ReflectionStatus.INSUFFICIENT_EVIDENCE
    )

    assert pattern_discoverer.calls == 0
    assert insight_generator.calls == 0
    assert recommendation_generator.calls == 0


def test_sufficient_history_without_patterns_produces_limited_reflection():
    """
    Enough history to investigate does not guarantee that a Pattern
    exists.
    """

    (
        engine,
        _,
        _,
        insight_generator,
        recommendation_generator,
        confidence_engine,
    ) = make_engine(
        patterns=[],
        insights=[],
        recommendations=[],
        confidence=make_confidence(
            score=0.45,
        ),
    )

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ],
        title="No-pattern reflection",
    )

    assert result.status == ReflectionStatus.LIMITED
    assert result.patterns == []
    assert result.insights == []
    assert result.recommendations == []

    assert insight_generator.calls == 0
    assert recommendation_generator.calls == 0
    assert confidence_engine.calls == 1


def test_patterns_without_insights_produce_limited_reflection():
    """
    Reflection remains limited when Pattern support exists but no
    responsible interpretation is produced.
    """

    (
        engine,
        _,
        _,
        _,
        recommendation_generator,
        _,
    ) = make_engine(
        insights=[],
        recommendations=[],
        confidence=make_confidence(
            score=0.55,
        ),
    )

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ],
        title="Pattern-only reflection",
    )

    assert result.status == ReflectionStatus.LIMITED
    assert len(result.patterns) == 1
    assert result.insights == []
    assert result.recommendations == []

    assert recommendation_generator.calls == 0


def test_complete_reflection_preserves_learning_event_ids():
    """
    The authoritative result must identify exactly which historical
    events were examined.
    """

    event_ids = [
        "learning-8",
        "learning-12",
    ]

    (
        engine,
        *_,
    ) = make_engine(
        patterns=[
            make_pattern(
                learning_event_ids=event_ids,
            ),
        ],
        insights=[
            make_insight(
                learning_event_ids=event_ids,
            ),
        ],
    )

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-8",
            ),
            make_event(
                event_id="learning-12",
            ),
        ],
        title="Historical reflection",
    )

    assert result.learning_event_ids == event_ids


def test_engine_does_not_modify_learning_events():
    """
    Reflection never edits the past.
    """

    events = [
        make_event(
            event_id="learning-1",
        ),
        make_event(
            event_id="learning-2",
        ),
    ]

    original = deepcopy(events)

    engine, *_ = make_engine()

    engine.reflect(
        learning_events=events,
        title="Immutable history reflection",
    )

    assert events == original


def test_engine_preserves_specialist_outputs():
    """
    Coordination may assemble specialist results but must not rewrite
    their authoritative content.
    """

    patterns = [make_pattern()]
    insights = [make_insight()]
    recommendations = [
        make_recommendation()
    ]

    engine, *_ = make_engine(
        patterns=patterns,
        insights=insights,
        recommendations=recommendations,
    )

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ],
        title="Preservation reflection",
    )

    assert result.patterns == patterns
    assert result.insights == insights
    assert result.recommendations == recommendations


def test_engine_produces_high_level_reflection_trace():
    """
    ReflectionResult should expose inspectable stages without exposing
    private chain-of-thought.
    """

    engine, *_ = make_engine()

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ],
        title="Traceable reflection",
    )

    assert result.reflection_trace
    assert len(result.reflection_trace) >= 4


def test_engine_contains_no_constitutional_judgment():
    """
    Constitutional coherence remains downstream from the Reflection
    Engine.
    """

    engine, *_ = make_engine()

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ],
        title="Pre-coherence reflection",
    )

    assert not hasattr(
        result,
        "constitutionally_coherent",
    )

    assert not hasattr(
        result,
        "constitutional_score",
    )

    assert not hasattr(
        result,
        "authoritative",
    )


def test_engine_does_not_format_user_communication():
    """
    ReflectionResult is structured cognition, not prose communication.
    """

    engine, *_ = make_engine()

    result = engine.reflect(
        learning_events=[
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ],
        title="Structured reflection",
    )

    assert not hasattr(
        result,
        "answer",
    )

    assert not hasattr(
        result,
        "formatted_response",
    )
