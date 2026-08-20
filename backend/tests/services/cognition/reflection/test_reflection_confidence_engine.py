"""
Contract tests for SentinelAI's Reflection Confidence Engine.

Reflection Confidence measures how strongly the complete reflective
record supports the Reflection judgment.

It does not:

- determine constitutional coherence,
- execute recommendations,
- replace Pattern or Insight confidence,
- modify reflective artifacts,
- manufacture missing historical support.
"""

from app.services.cognition.reflection.history_analyzer import (
    ReflectionHistoryAssessment,
    ReflectionHistoryStatus,
)

from app.services.cognition.reflection.models import (
    ReflectionConfidenceLevel,
    ReflectionInsight,
    ReflectionPattern,
    ReflectionPatternKind,
    ReflectionRecommendation,
    ReflectionRecommendationKind,
)

from app.services.cognition.reflection.reflection_confidence_engine import (
    ReflectionConfidenceEngine,
)


def make_history(
    *,
    status: ReflectionHistoryStatus = (
        ReflectionHistoryStatus.SUFFICIENT
    ),
    event_count: int = 3,
    evidence_coverage: float = 1.0,
    limitations: list[str] | None = None,
) -> ReflectionHistoryAssessment:
    return ReflectionHistoryAssessment(
        status=status,
        event_count=event_count,
        history_sufficient=(
            status == ReflectionHistoryStatus.SUFFICIENT
        ),
        learning_event_ids=[
            f"learning-{i}"
            for i in range(1, event_count + 1)
        ],
        domain_ids=["engineering"],
        shared_domain_ids=(
            ["engineering"]
            if status == ReflectionHistoryStatus.SUFFICIENT
            else []
        ),
        evidence_ids=["evidence-1"],
        evidence_count=1,
        events_with_evidence=round(
            event_count * evidence_coverage
        ),
        evidence_coverage=evidence_coverage,
        temporal_span_seconds=86400.0,
        limitations=limitations or [],
    )


def make_pattern(
    *,
    event_count: int = 3,
) -> ReflectionPattern:
    return ReflectionPattern(
        pattern_id="pattern-1",
        kind=ReflectionPatternKind.RECURRENCE,
        title="Recurring engineering learning",
        description=(
            "Engineering recurs across accumulated learning."
        ),
        learning_event_ids=[
            f"learning-{i}"
            for i in range(1, event_count + 1)
        ],
        evidence_ids=["evidence-1"],
        domain_ids=["engineering"],
    )


def make_insight(
    *,
    confidence: float = 0.85,
) -> ReflectionInsight:
    return ReflectionInsight(
        insight_id="insight-1",
        title="Engineering is a recurring learning area",
        explanation=(
            "The historical Pattern indicates repeated "
            "engineering-related learning."
        ),
        pattern_ids=["pattern-1"],
        learning_event_ids=[
            "learning-1",
            "learning-2",
            "learning-3",
        ],
        evidence_ids=["evidence-1"],
        domain_ids=["engineering"],
        confidence=confidence,
    )


def make_recommendation() -> ReflectionRecommendation:
    return ReflectionRecommendation(
        recommendation_id="recommendation-1",
        kind=ReflectionRecommendationKind.STRENGTHEN,
        title="Continue strengthening engineering learning",
        description=(
            "Future learning should continue examining "
            "the established engineering Pattern."
        ),
        insight_ids=["insight-1"],
        pattern_ids=["pattern-1"],
        domain_ids=["engineering"],
        priority=1,
        requires_human_approval=True,
    )


def test_strong_reflective_record_produces_high_confidence():
    engine = ReflectionConfidenceEngine()

    result = engine.evaluate(
        history=make_history(),
        patterns=[make_pattern()],
        insights=[make_insight()],
        recommendations=[make_recommendation()],
    )

    assert result.level == ReflectionConfidenceLevel.HIGH
    assert 0.0 <= result.score <= 1.0
    assert result.factors
    assert result.basis


def test_insufficient_history_produces_low_confidence():
    engine = ReflectionConfidenceEngine()

    result = engine.evaluate(
        history=make_history(
            status=(
                ReflectionHistoryStatus.INSUFFICIENT_HISTORY
            ),
            event_count=1,
            evidence_coverage=1.0,
            limitations=[
                "Only one Learning Event was available.",
            ],
        ),
        patterns=[],
        insights=[],
        recommendations=[],
    )

    assert result.level == ReflectionConfidenceLevel.LOW
    assert result.score < 0.5
    assert result.uncertainty


def test_partial_evidence_coverage_reduces_confidence():
    engine = ReflectionConfidenceEngine()

    complete = engine.evaluate(
        history=make_history(
            evidence_coverage=1.0,
        ),
        patterns=[make_pattern()],
        insights=[make_insight()],
        recommendations=[make_recommendation()],
    )

    partial = engine.evaluate(
        history=make_history(
            evidence_coverage=0.5,
            limitations=[
                "One or more Learning Events lack evidence.",
            ],
        ),
        patterns=[make_pattern()],
        insights=[make_insight()],
        recommendations=[make_recommendation()],
    )

    assert partial.score < complete.score


def test_broader_pattern_support_does_not_reduce_confidence():
    engine = ReflectionConfidenceEngine()

    narrow = engine.evaluate(
        history=make_history(
            event_count=2,
        ),
        patterns=[
            make_pattern(
                event_count=2,
            ),
        ],
        insights=[
            make_insight(
                confidence=0.75,
            ),
        ],
        recommendations=[make_recommendation()],
    )

    broad = engine.evaluate(
        history=make_history(
            event_count=5,
        ),
        patterns=[
            make_pattern(
                event_count=5,
            ),
        ],
        insights=[
            make_insight(
                confidence=0.75,
            ),
        ],
        recommendations=[make_recommendation()],
    )

    assert broad.score >= narrow.score


def test_higher_insight_confidence_does_not_reduce_reflection_confidence():
    engine = ReflectionConfidenceEngine()

    weaker = engine.evaluate(
        history=make_history(),
        patterns=[make_pattern()],
        insights=[
            make_insight(
                confidence=0.40,
            ),
        ],
        recommendations=[make_recommendation()],
    )

    stronger = engine.evaluate(
        history=make_history(),
        patterns=[make_pattern()],
        insights=[
            make_insight(
                confidence=0.90,
            ),
        ],
        recommendations=[make_recommendation()],
    )

    assert stronger.score >= weaker.score


def test_missing_insights_limit_reflection_confidence():
    engine = ReflectionConfidenceEngine()

    result = engine.evaluate(
        history=make_history(),
        patterns=[make_pattern()],
        insights=[],
        recommendations=[],
    )

    assert result.level != ReflectionConfidenceLevel.HIGH
    assert result.uncertainty


def test_confidence_factors_are_explainable():
    engine = ReflectionConfidenceEngine()

    result = engine.evaluate(
        history=make_history(
            evidence_coverage=0.5,
        ),
        patterns=[make_pattern()],
        insights=[make_insight()],
        recommendations=[make_recommendation()],
    )

    names = {
        factor.name
        for factor in result.factors
    }

    assert "historical_sufficiency" in names
    assert "pattern_support" in names
    assert "evidence_coverage" in names
    assert "insight_confidence" in names
    assert "traceability" in names


def test_confidence_is_bounded():
    engine = ReflectionConfidenceEngine()

    result = engine.evaluate(
        history=make_history(),
        patterns=[make_pattern()],
        insights=[make_insight()],
        recommendations=[make_recommendation()],
    )

    assert 0.0 <= result.score <= 1.0


def test_confidence_has_no_constitutional_authority():
    engine = ReflectionConfidenceEngine()

    result = engine.evaluate(
        history=make_history(),
        patterns=[make_pattern()],
        insights=[make_insight()],
        recommendations=[make_recommendation()],
    )

    assert not hasattr(
        result,
        "constitutionally_coherent",
    )

    assert not hasattr(
        result,
        "authoritative",
    )


def test_confidence_does_not_modify_reflective_artifacts():
    engine = ReflectionConfidenceEngine()

    history = make_history()
    patterns = [make_pattern()]
    insights = [make_insight()]
    recommendations = [make_recommendation()]

    before = (
        history.model_dump(),
        [p.model_dump() for p in patterns],
        [i.model_dump() for i in insights],
        [r.model_dump() for r in recommendations],
    )

    engine.evaluate(
        history=history,
        patterns=patterns,
        insights=insights,
        recommendations=recommendations,
    )

    after = (
        history.model_dump(),
        [p.model_dump() for p in patterns],
        [i.model_dump() for i in insights],
        [r.model_dump() for r in recommendations],
    )

    assert before == after
