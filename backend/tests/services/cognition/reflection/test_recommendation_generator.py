"""
Contract tests for SentinelAI's Reflection Recommendation Generator.

Recommendation Generation proposes responsible directions for future
learning from authoritative Reflection Insights.

It does not:

- discover Patterns,
- generate Insights,
- modify Learning Events,
- rewrite Memory,
- execute recommendations,
- alter the Constitution,
- grant authority to itself.

Recommendation proposes.

Recommendation does not execute.
"""

from app.services.cognition.reflection.models import (
    ReflectionInsight,
)

from app.services.cognition.reflection.recommendation_generator import (
    ReflectionRecommendationGenerator,
)


def make_insight(
    *,
    insight_id: str = "insight-1",
    pattern_ids: list[str] | None = None,
    learning_event_ids: list[str] | None = None,
    evidence_ids: list[str] | None = None,
    domain_ids: list[str] | None = None,
    confidence: float = 0.80,
) -> ReflectionInsight:
    """
    Construct one authoritative Reflection Insight.
    """

    return ReflectionInsight(
        insight_id=insight_id,
        title="Recurring learning area: engineering",
        explanation=(
            "Engineering recurs across the examined "
            "learning history."
        ),
        pattern_ids=(
            pattern_ids
            or [
                "pattern-1",
            ]
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
        domain_ids=(
            domain_ids
            or [
                "engineering",
            ]
        ),
        confidence=confidence,
    )


def test_no_insights_produce_no_recommendations():
    """
    Recommendation cannot exist without Insight support.
    """

    generator = ReflectionRecommendationGenerator()

    recommendations = generator.generate([])

    assert recommendations == []


def test_insight_produces_future_learning_recommendation():
    """
    An authoritative Insight may justify a bounded recommendation for
    future learning.
    """

    generator = ReflectionRecommendationGenerator()

    recommendations = generator.generate(
        [
            make_insight(),
        ]
    )

    assert len(recommendations) == 1

    recommendation = recommendations[0]

    assert recommendation.insight_ids == [
        "insight-1",
    ]

    assert recommendation.pattern_ids == [
        "pattern-1",
    ]

    assert recommendation.domain_ids == [
        "engineering",
    ]


def test_recommendation_inherits_only_insight_patterns():
    """
    Recommendation Pattern provenance cannot exceed the Patterns
    supporting its authoritative Insight.
    """

    generator = ReflectionRecommendationGenerator()

    recommendation = generator.generate(
        [
            make_insight(
                pattern_ids=[
                    "pattern-2",
                    "pattern-7",
                ],
            ),
        ]
    )[0]

    assert recommendation.pattern_ids == [
        "pattern-2",
        "pattern-7",
    ]


def test_recommendation_inherits_only_insight_domains():
    """
    Recommendation scope cannot silently expand beyond the domains
    established by its supporting Insight.
    """

    generator = ReflectionRecommendationGenerator()

    recommendation = generator.generate(
        [
            make_insight(
                domain_ids=[
                    "engineering",
                    "reasoning",
                ],
            ),
        ]
    )[0]

    assert recommendation.domain_ids == [
        "engineering",
        "reasoning",
    ]


def test_recommendation_preserves_provenance_order():
    """
    Derived cognition inherits authoritative provenance without silently
    rewriting its order.
    """

    generator = ReflectionRecommendationGenerator()

    recommendation = generator.generate(
        [
            make_insight(
                pattern_ids=[
                    "pattern-4",
                    "pattern-8",
                    "pattern-12",
                ],
                domain_ids=[
                    "engineering",
                    "reasoning",
                    "verification",
                ],
            ),
        ]
    )[0]

    assert recommendation.pattern_ids == [
        "pattern-4",
        "pattern-8",
        "pattern-12",
    ]

    assert recommendation.domain_ids == [
        "engineering",
        "reasoning",
        "verification",
    ]


def test_recommendation_requires_human_approval():
    """
    Recommendation possesses no autonomous execution authority.
    """

    generator = ReflectionRecommendationGenerator()

    recommendation = generator.generate(
        [
            make_insight(),
        ]
    )[0]

    assert recommendation.requires_human_approval is True


def test_recommendation_has_no_execution_state():
    """
    Recommendation is a proposal, not an action.
    """

    generator = ReflectionRecommendationGenerator()

    recommendation = generator.generate(
        [
            make_insight(),
        ]
    )[0]

    assert not hasattr(
        recommendation,
        "executed",
    )

    assert not hasattr(
        recommendation,
        "execution_result",
    )

    assert not hasattr(
        recommendation,
        "action_result",
    )


def test_recommendation_has_no_constitutional_authority():
    """
    Constitutional coherence remains a separate authority judgment.
    """

    generator = ReflectionRecommendationGenerator()

    recommendation = generator.generate(
        [
            make_insight(),
        ]
    )[0]

    assert not hasattr(
        recommendation,
        "constitutionally_coherent",
    )

    assert not hasattr(
        recommendation,
        "authoritative",
    )


def test_recommendation_priority_is_bounded():
    """
    Generated priority must satisfy the Recommendation contract.
    """

    generator = ReflectionRecommendationGenerator()

    recommendation = generator.generate(
        [
            make_insight(),
        ]
    )[0]

    assert recommendation.priority is not None
    assert recommendation.priority >= 1


def test_stronger_insight_does_not_receive_lower_priority():
    """
    Within otherwise equivalent deterministic Insights, stronger
    support should not produce a weaker recommendation priority.
    """

    generator = ReflectionRecommendationGenerator()

    stronger = generator.generate(
        [
            make_insight(
                insight_id="insight-strong",
                confidence=0.90,
            ),
        ]
    )[0]

    weaker = generator.generate(
        [
            make_insight(
                insight_id="insight-weak",
                confidence=0.40,
            ),
        ]
    )[0]

    # Lower numeric value represents greater priority.
    assert stronger.priority <= weaker.priority


def test_recommendation_ids_are_deterministic():
    """
    Identical Insight input must produce identical Recommendation
    identity across repeated reflective operations.
    """

    generator = ReflectionRecommendationGenerator()

    insight = make_insight()

    first = generator.generate(
        [
            insight,
        ]
    )

    second = generator.generate(
        [
            insight,
        ]
    )

    assert (
        first[0].recommendation_id
        == second[0].recommendation_id
    )


def test_recommendation_generation_is_order_independent():
    """
    Reordering equivalent Insight input must not change authoritative
    Recommendation output.
    """

    engineering = make_insight(
        insight_id="insight-engineering",
        pattern_ids=[
            "pattern-engineering",
        ],
        domain_ids=[
            "engineering",
        ],
    )

    reasoning = make_insight(
        insight_id="insight-reasoning",
        pattern_ids=[
            "pattern-reasoning",
        ],
        domain_ids=[
            "reasoning",
        ],
    )

    generator = ReflectionRecommendationGenerator()

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
