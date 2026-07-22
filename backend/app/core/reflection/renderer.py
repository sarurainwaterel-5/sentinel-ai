"""
Reflection Renderer

Rendering communicates reflection.

The Renderer transforms Reflection objects into coherent,
human-readable representations.

Rendering never creates reflection.

Rendering never validates reflection.

Rendering communicates understanding while preserving traceability.
"""

from app.core.reflection.models import (
    Insight,
    Pattern,
    Recommendation,
    Reflection,
    ReflectionRegistry,
)


def render_pattern(pattern: Pattern) -> dict:
    """Render a Pattern."""

    return pattern.to_dict()


def render_insight(insight: Insight) -> dict:
    """Render an Insight."""

    return insight.to_dict()


def render_recommendation(
    recommendation: Recommendation,
) -> dict:
    """Render a Recommendation."""

    return recommendation.to_dict()


def render_reflection(
    reflection: Reflection,
) -> dict:
    """Render a Reflection."""

    return reflection.to_dict()


def render_reflection_registry(
    registry: ReflectionRegistry,
) -> dict:
    """
    Render the complete Reflection Registry.

    Rendering communicates reflection without modifying it.
    """

    return {
        "patterns": [
            render_pattern(pattern)
            for pattern in registry.patterns
        ],
        "insights": [
            render_insight(insight)
            for insight in registry.insights
        ],
        "recommendations": [
            render_recommendation(rec)
            for rec in registry.recommendations
        ],
        "reflections": [
            render_reflection(reflection)
            for reflection in registry.reflections
        ],
    }
