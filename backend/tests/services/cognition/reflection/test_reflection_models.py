"""
Contract tests for SentinelAI's cognitive Reflection Faculty.

Reflection examines accumulated Learning Events.

It does not:

- modify historical Learning Events,
- manufacture patterns from isolated events,
- execute recommendations,
- allow confidence to override constitutional coherence.

These tests establish the structural laws of modern Reflection.
"""

import pytest
from pydantic import ValidationError

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


def make_pattern(
    *,
    pattern_id: str = "pattern-1",
    learning_event_ids: list[str] | None = None,
) -> ReflectionPattern:
    return ReflectionPattern(
        pattern_id=pattern_id,
        kind=ReflectionPatternKind.RECURRENCE,
        title="Repeated reasoning weakness",
        description=(
            "Reasoning support was repeatedly unavailable "
            "across the examined learning history."
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
            "evidence-2",
        ],
        domain_ids=[
            "engineering",
        ],
    )


def make_insight(
    *,
    insight_id: str = "insight-1",
    pattern_ids: list[str] | None = None,
) -> ReflectionInsight:
    return ReflectionInsight(
        insight_id=insight_id,
        title="Reasoning provenance requires strengthening",
        explanation=(
            "Repeated failures indicate that reasoning provenance "
            "should receive additional attention in future learning."
        ),
        pattern_ids=(
            pattern_ids
            or [
                "pattern-1",
            ]
        ),
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        domain_ids=[
            "engineering",
        ],
        confidence=0.86,
    )


def make_recommendation(
    *,
    recommendation_id: str = "recommendation-1",
    insight_ids: list[str] | None = None,
    pattern_ids: list[str] | None = None,
) -> ReflectionRecommendation:
    return ReflectionRecommendation(
        recommendation_id=recommendation_id,
        kind=ReflectionRecommendationKind.STRENGTHEN,
        title="Strengthen reasoning provenance",
        description=(
            "Future learning should preserve stronger visible "
            "reasoning-to-evidence traceability."
        ),
        insight_ids=(
            insight_ids
            or [
                "insight-1",
            ]
        ),
        pattern_ids=(
            pattern_ids
            or [
                "pattern-1",
            ]
        ),
        domain_ids=[
            "engineering",
        ],
        priority=1,
        requires_human_approval=True,
    )


def make_confidence() -> ReflectionConfidence:
    return ReflectionConfidence(
        score=0.84,
        level=ReflectionConfidenceLevel.HIGH,
        basis=(
            "The reflected pattern is supported by multiple "
            "historical learning events."
        ),
        factors=[],
        uncertainty=[],
    )


def test_pattern_requires_multiple_learning_events():
    """
    A historical Pattern cannot be established from one isolated event.
    """

    with pytest.raises(ValidationError):
        make_pattern(
            learning_event_ids=[
                "learning-1",
            ],
        )


def test_reflection_result_preserves_complete_provenance_graph():
    """
    Every Pattern, Insight, and Recommendation reference must resolve
    within the same authoritative ReflectionResult.
    """

    result = ReflectionResult(
        title="Reasoning provenance reflection",
        summary=(
            "Repeated provenance weaknesses were identified "
            "across accumulated learning."
        ),
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        patterns=[
            make_pattern(),
        ],
        insights=[
            make_insight(),
        ],
        recommendations=[
            make_recommendation(),
        ],
        confidence=make_confidence(),
        reflection_trace=[
            "Examined accumulated learning history.",
            "Discovered historical patterns.",
            "Generated evidence-grounded insights.",
            "Produced recommendations for future learning.",
        ],
        status=ReflectionStatus.COMPLETE,
    )

    assert result.status == ReflectionStatus.COMPLETE
    assert len(result.learning_event_ids) == 2
    assert result.patterns[0].learning_event_ids == [
        "learning-1",
        "learning-2",
    ]


def test_unknown_pattern_reference_is_rejected():
    """
    Insights cannot reference Patterns that were not produced by the
    same reflective operation.
    """

    with pytest.raises(
        ValidationError,
        match="unknown pattern",
    ):
        ReflectionResult(
            title="Invalid reflection",
            summary="Invalid provenance graph.",
            learning_event_ids=[
                "learning-1",
                "learning-2",
            ],
            patterns=[
                make_pattern(),
            ],
            insights=[
                make_insight(
                    pattern_ids=[
                        "pattern-does-not-exist",
                    ],
                ),
            ],
            recommendations=[],
            confidence=make_confidence(),
            status=ReflectionStatus.LIMITED,
        )


def test_unknown_insight_reference_is_rejected():
    """
    Recommendations cannot reference unknown Insights.
    """

    with pytest.raises(
        ValidationError,
        match="unknown insight",
    ):
        ReflectionResult(
            title="Invalid reflection",
            summary="Invalid recommendation provenance.",
            learning_event_ids=[
                "learning-1",
                "learning-2",
            ],
            patterns=[
                make_pattern(),
            ],
            insights=[
                make_insight(),
            ],
            recommendations=[
                make_recommendation(
                    insight_ids=[
                        "insight-does-not-exist",
                    ],
                ),
            ],
            confidence=make_confidence(),
            status=ReflectionStatus.LIMITED,
        )


def test_pattern_may_only_reference_examined_learning_history():
    """
    Patterns cannot claim support from Learning Events outside the
    history supplied to the reflective operation.
    """

    with pytest.raises(
        ValidationError,
        match="unknown learning event",
    ):
        ReflectionResult(
            title="Invalid reflection",
            summary="Pattern exceeds examined history.",
            learning_event_ids=[
                "learning-1",
                "learning-2",
            ],
            patterns=[
                make_pattern(
                    learning_event_ids=[
                        "learning-1",
                        "learning-99",
                    ],
                ),
            ],
            insights=[],
            recommendations=[],
            confidence=make_confidence(),
            status=(
                ReflectionStatus.INSUFFICIENT_EVIDENCE
            ),
        )


def test_single_learning_event_cannot_produce_complete_reflection():
    """
    One isolated Learning Event is not sufficient historical evidence
    for a completed Reflection.
    """

    with pytest.raises(
        ValidationError,
        match="multiple learning events",
    ):
        ReflectionResult(
            title="Insufficient history",
            summary=(
                "Only one Learning Event was available."
            ),
            learning_event_ids=[
                "learning-1",
            ],
            patterns=[],
            insights=[],
            recommendations=[],
            confidence=ReflectionConfidence(
                score=0.20,
                level=ReflectionConfidenceLevel.LOW,
                basis=(
                    "Historical evidence is insufficient."
                ),
                uncertainty=[
                    (
                        "Only one Learning Event was available "
                        "for reflection."
                    ),
                ],
            ),
            status=ReflectionStatus.COMPLETE,
        )


def test_insufficient_evidence_preserves_uncertainty():
    """
    Reflection must expose insufficient historical support rather than
    manufacture Patterns or Insights.
    """

    result = ReflectionResult(
        title="Insufficient reflective evidence",
        summary=(
            "Available cognitive history does not support "
            "a responsible historical pattern."
        ),
        learning_event_ids=[
            "learning-1",
        ],
        patterns=[],
        insights=[],
        recommendations=[],
        confidence=ReflectionConfidence(
            score=0.18,
            level=ReflectionConfidenceLevel.LOW,
            basis=(
                "Only one Learning Event was available."
            ),
            uncertainty=[
                (
                    "Additional historical learning is required "
                    "before recurrence can be established."
                ),
            ],
        ),
        reflection_trace=[
            "Examined available learning history.",
            "Historical support was insufficient for pattern discovery.",
        ],
        status=ReflectionStatus.INSUFFICIENT_EVIDENCE,
    )

    assert result.patterns == []
    assert result.insights == []
    assert result.recommendations == []
    assert result.confidence.uncertainty


def test_recommendations_have_no_execution_authority():
    """
    Reflection may recommend future learning but cannot execute it.
    """

    recommendation = make_recommendation()

    assert recommendation.requires_human_approval is True

    assert not hasattr(
        recommendation,
        "executed",
    )

    assert not hasattr(
        recommendation,
        "execution_result",
    )


def test_reflection_confidence_does_not_encode_constitutional_authority():
    """
    Reflection confidence measures reflective support only.

    Constitutional coherence remains a separate authority judgment.
    """

    confidence = ReflectionConfidence(
        score=0.97,
        level=ReflectionConfidenceLevel.HIGH,
        basis=(
            "Historical support for the reflection is strong."
        ),
    )

    assert confidence.score == 0.97

    assert not hasattr(
        confidence,
        "constitutionally_coherent",
    )

    assert not hasattr(
        confidence,
        "authoritative",
    )
