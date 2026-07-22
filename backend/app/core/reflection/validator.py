"""
Reflection Validator

Validation protects reflection.

Validation never creates reflection.

The Validator verifies that Reflection objects are complete,
coherent, and constitutionally valid.

Validation preserves integrity.

It never changes meaning.
"""

from app.core.reflection.models import (
    Insight,
    Pattern,
    Recommendation,
    Reflection,
    ReflectionRegistry,
)


def validate_pattern(pattern: Pattern) -> bool:
    """Validate a Pattern."""

    return all(
        [
            bool(pattern.pattern_id),
            bool(pattern.kind),
            bool(pattern.title),
            bool(pattern.description),
        ]
    )


def validate_insight(insight: Insight) -> bool:
    """Validate an Insight."""

    return all(
        [
            bool(insight.insight_id),
            bool(insight.title),
            bool(insight.explanation),
            len(insight.pattern_ids) > 0,
        ]
    )


def validate_recommendation(
    recommendation: Recommendation,
) -> bool:
    """Validate a Recommendation."""

    return all(
        [
            bool(recommendation.recommendation_id),
            bool(recommendation.kind),
            bool(recommendation.title),
            bool(recommendation.description),
            len(recommendation.insight_ids) > 0,
        ]
    )


def validate_reflection(reflection: Reflection) -> bool:
    """Validate a Reflection."""

    return all(
        [
            bool(reflection.reflection_id),
            bool(reflection.title),
            bool(reflection.summary),
            bool(reflection.status),
            len(reflection.insight_ids) > 0,
        ]
    )


def validate_reflection_registry(
    registry: ReflectionRegistry,
) -> bool:
    """
    Validate the Reflection Registry.

    Ensures every contained object is structurally valid.
    """

    return all(
        [
            all(validate_pattern(p) for p in registry.patterns),
            all(validate_insight(i) for i in registry.insights),
            all(
                validate_recommendation(r)
                for r in registry.recommendations
            ),
            all(
                validate_reflection(r)
                for r in registry.reflections
            ),
        ]
    )

