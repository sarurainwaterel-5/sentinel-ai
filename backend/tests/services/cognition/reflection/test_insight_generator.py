"""
Contract tests for SentinelAI's Reflection Insight Generator.

Insight Generation interprets authoritative Reflection Patterns.

It does not:

- discover Patterns,
- invent Learning Event provenance,
- invent Evidence provenance,
- generate Recommendations,
- execute actions,
- determine constitutional authority.

Interpretation may compress evidence.

Interpretation may never exceed evidence.
"""

from app.services.cognition.reflection.insight_generator import (
    ReflectionInsightGenerator,
)

from app.services.cognition.reflection.models import (
    ReflectionPattern,
    ReflectionPatternKind,
)


def make_pattern(
    *,
    pattern_id: str = "pattern-1",
    domain: str = "engineering",
    learning_event_ids: list[str] | None = None,
    evidence_ids: list[str] | None = None,
) -> ReflectionPattern:
    """
    Construct one authoritative historical Pattern.
    """

    return ReflectionPattern(
        pattern_id=pattern_id,
        kind=ReflectionPatternKind.RECURRENCE,
        title=f"Recurring domain: {domain}",
        description=(
            f"The domain '{domain}' appears across "
            "multiple Learning Events."
        ),
        learning_event_ids=(
            learning_event_ids
            or [
                "learning-1",
                "learning-2",
            ]
        ),
        evidence_ids=(
            evidence_ids
            if evidence_ids is not None
            else [
                "evidence-1",
            ]
        ),
        domain_ids=[
            domain,
        ],
    )


def test_no_patterns_produce_no_insights():
    """
    Insight cannot exist without Pattern support.
    """

    generator = ReflectionInsightGenerator()

    insights = generator.generate([])

    assert insights == []


def test_pattern_produces_structural_insight():
    """
    An authoritative Pattern may produce an Insight describing what
    the established historical structure reveals.
    """

    generator = ReflectionInsightGenerator()

    insights = generator.generate(
        [
            make_pattern(),
        ]
    )

    assert len(insights) == 1

    insight = insights[0]

    assert insight.pattern_ids == [
        "pattern-1",
    ]

    assert insight.domain_ids == [
        "engineering",
    ]

    assert insight.learning_event_ids == [
        "learning-1",
        "learning-2",
    ]


def test_insight_inherits_learning_event_provenance():
    """
    Insight Learning Event provenance must come from its supporting
    Pattern rather than being independently manufactured.
    """

    generator = ReflectionInsightGenerator()

    insights = generator.generate(
        [
            make_pattern(
                learning_event_ids=[
                    "learning-4",
                    "learning-8",
                    "learning-12",
                ],
            ),
        ]
    )

    assert insights[0].learning_event_ids == [
        "learning-4",
        "learning-8",
        "learning-12",
    ]


def test_insight_inherits_only_pattern_evidence():
    """
    Insight evidence cannot exceed the evidence established by its
    supporting Pattern.
    """

    generator = ReflectionInsightGenerator()

    insights = generator.generate(
        [
            make_pattern(
                evidence_ids=[
                    "evidence-2",
                    "evidence-7",
                ],
            ),
        ]
    )

    assert insights[0].evidence_ids == [
        "evidence-2",
        "evidence-7",
    ]


def test_pattern_without_evidence_does_not_gain_evidence():
    """
    Insight Generation cannot manufacture Evidence provenance when the
    supporting Pattern contains none.
    """

    generator = ReflectionInsightGenerator()

    insights = generator.generate(
        [
            make_pattern(
                evidence_ids=[],
            ),
        ]
    )

    assert insights[0].evidence_ids == []


def test_multiple_patterns_remain_traceable():
    """
    Independently established Patterns remain independently traceable
    through their generated Insights.
    """

    generator = ReflectionInsightGenerator()

    insights = generator.generate(
        [
            make_pattern(
                pattern_id="pattern-engineering",
                domain="engineering",
            ),
            make_pattern(
                pattern_id="pattern-reasoning",
                domain="reasoning",
            ),
        ]
    )

    assert len(insights) == 2

    support = {
        insight.pattern_ids[0]
        for insight in insights
    }

    assert support == {
        "pattern-engineering",
        "pattern-reasoning",
    }


def test_insight_confidence_is_bounded():
    """
    Generated Insight confidence must remain within the canonical
    confidence interval.
    """

    generator = ReflectionInsightGenerator()

    insight = generator.generate(
        [
            make_pattern(),
        ]
    )[0]

    assert insight.confidence is not None
    assert 0.0 <= insight.confidence <= 1.0


def test_broader_historical_support_does_not_reduce_confidence():
    """
    Within otherwise equivalent deterministic Patterns, broader
    historical support should not reduce structural Insight confidence.
    """

    generator = ReflectionInsightGenerator()

    narrow = generator.generate(
        [
            make_pattern(
                pattern_id="pattern-narrow",
                learning_event_ids=[
                    "learning-1",
                    "learning-2",
                ],
            ),
        ]
    )[0]

    broad = generator.generate(
        [
            make_pattern(
                pattern_id="pattern-broad",
                learning_event_ids=[
                    "learning-1",
                    "learning-2",
                    "learning-3",
                    "learning-4",
                ],
            ),
        ]
    )[0]

    assert broad.confidence >= narrow.confidence


def test_insight_ids_are_deterministic():
    """
    Identical authoritative Pattern input produces identical Insight
    identity across repeated reflective operations.
    """

    generator = ReflectionInsightGenerator()

    pattern = make_pattern()

    first = generator.generate(
        [
            pattern,
        ]
    )

    second = generator.generate(
        [
            pattern,
        ]
    )

    assert (
        first[0].insight_id
        == second[0].insight_id
    )


def test_insight_generation_is_order_independent():
    """
    Reordering equivalent Pattern input must not alter authoritative
    Insight output.
    """

    engineering = make_pattern(
        pattern_id="pattern-engineering",
        domain="engineering",
    )

    reasoning = make_pattern(
        pattern_id="pattern-reasoning",
        domain="reasoning",
    )

    generator = ReflectionInsightGenerator()

    forward = generator.generate(
        [
            engineering,
            reasoning,
        ]
    )

    reverse = generator.generate(
        [
            reasoning,
            engineering,
        ]
    )

    assert forward == reverse


def test_insight_has_no_recommendation_or_execution_authority():
    """
    Insight explains Pattern meaning.

    It does not prescribe or execute future behavior.
    """

    generator = ReflectionInsightGenerator()

    insight = generator.generate(
        [
            make_pattern(),
        ]
    )[0]

    assert not hasattr(
        insight,
        "recommendation",
    )

    assert not hasattr(
        insight,
        "action",
    )

    assert not hasattr(
        insight,
        "execution_result",
    )

    assert not hasattr(
        insight,
        "constitutionally_coherent",
    )
