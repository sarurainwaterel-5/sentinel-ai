"""
Contract tests for SentinelAI's Reflection Formatter.

The Formatter communicates governed Reflection.

It does not:

- perform Reflection,
- discover Patterns,
- generate Insights,
- generate Recommendations,
- calculate confidence,
- determine constitutional coherence,
- alter admissibility,
- execute Recommendations,
- manufacture unsupported cognition.

Cognition determines content.

Governance determines admissibility.

Formatting determines presentation.
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

from app.services.cognition.reflection.reflection_formatter import (
    ReflectionFormatter,
)

from app.services.cognition.reflection.reflection_orchestrator import (
    GovernedReflectionResult,
)


def make_governed_reflection(
    *,
    coherent: bool = True,
    admissible: bool = True,
    confidence_score: float = 0.90,
    conflicts: list[str] | None = None,
) -> GovernedReflectionResult:
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

    reflection = ReflectionResult(
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

    coherence = ReflectionCoherenceResult(
        coherent=coherent,
        admissible=admissible,
        constitutional_score=(
            1.0
            if coherent
            else 0.20
        ),
        reflection_confidence=confidence_score,
        articles_consulted=[],
        conflicts=conflicts or [],
        recommendations=[],
    )

    return GovernedReflectionResult(
        reflection=reflection,
        coherence=coherence,
        admissible=admissible,
    )


def test_formatter_returns_string():
    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection()
    )

    assert isinstance(output, str)
    assert output.strip()


def test_formatter_preserves_reflection_title():
    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection()
    )

    assert "Engineering reflection" in output


def test_formatter_communicates_patterns():
    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection()
    )

    assert "Recurring engineering learning" in output


def test_formatter_communicates_insights():
    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection()
    )

    assert "Engineering remains recurrent" in output


def test_formatter_communicates_recommendations():
    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection()
    )

    assert "Continue engineering learning" in output


def test_formatter_communicates_confidence():
    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection(
            confidence_score=0.90,
        )
    )

    assert "0.9" in output
    assert "HIGH" in output.upper()


def test_formatter_communicates_constitutional_admissibility():
    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection(
            coherent=True,
            admissible=True,
        )
    )

    assert "admissible" in output.lower()


def test_formatter_surfaces_constitutional_conflicts():
    formatter = ReflectionFormatter()

    conflict = (
        "Recommendation exceeds reflective authority."
    )

    output = formatter.format(
        make_governed_reflection(
            coherent=False,
            admissible=False,
            conflicts=[
                conflict,
            ],
        )
    )

    assert conflict in output
    assert "inadmissible" in output.lower()


def test_formatter_preserves_human_approval_boundary():
    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection()
    )

    assert "human approval" in output.lower()


def test_formatter_does_not_modify_governed_reflection():
    governed = make_governed_reflection()
    before = deepcopy(governed)

    formatter = ReflectionFormatter()

    formatter.format(
        governed
    )

    assert governed == before


def test_formatter_does_not_claim_execution_authority():
    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection()
    )

    forbidden_claims = [
        "execution authorized",
        "executed successfully",
        "recommendation executed",
    ]

    for claim in forbidden_claims:
        assert claim not in output.lower()


def test_formatter_does_not_hide_inadmissible_reflection():
    """
    An inadmissible Reflection remains visible as intellectual history.

    Formatting surfaces the constitutional judgment rather than
    silently deleting the underlying cognition.
    """

    formatter = ReflectionFormatter()

    output = formatter.format(
        make_governed_reflection(
            coherent=False,
            admissible=False,
            conflicts=[
                "Constitutional conflict detected.",
            ],
        )
    )

    assert "Recurring engineering learning" in output
    assert "Engineering remains recurrent" in output
    assert "Constitutional conflict detected." in output
    assert "inadmissible" in output.lower()
