"""
Reflection Engine

The Reflection Engine coordinates disciplined reflection.

The Engine orchestrates Reflection.

It does not discover Patterns.

It does not generate Insights.

It does not generate Recommendations.

It does not validate Reflection.

It does not render Reflection.

Behavior emerges through orchestration.

The Engine transforms completed Learning Events into organized,
validated, and communicable Reflection.
"""

from collections.abc import Callable
from typing import Any

from app.core.cognition.models import LearningEvent
from app.core.reflection.builder import build_reflection_registry
from app.core.reflection.models import (
    Insight,
    Pattern,
    Recommendation,
    Reflection,
)
from app.core.reflection.renderer import render_reflection_registry
from app.core.reflection.validator import validate_reflection_registry


PatternDiscoverer = Callable[[list[LearningEvent]], list[Pattern]]

InsightGenerator = Callable[
    [list[Pattern], list[LearningEvent]],
    list[Insight],
]

RecommendationGenerator = Callable[
    [list[Insight], list[Pattern]],
    list[Recommendation],
]

ReflectionBuilder = Callable[
    [
        list[LearningEvent],
        list[Pattern],
        list[Insight],
        list[Recommendation],
    ],
    Reflection,
]


class ReflectionValidationError(RuntimeError):
    """
    Raised when the Reflection Engine produces an invalid registry.
    """


def run_reflection(
    *,
    learning_events: list[LearningEvent],
    discover_patterns: PatternDiscoverer,
    generate_insights: InsightGenerator,
    generate_recommendations: RecommendationGenerator,
    build_reflection: ReflectionBuilder,
) -> dict[str, Any]:
    """
    Coordinate one complete reflective cycle.

    Engine responsibilities:

    - Receive completed Learning Events.
    - Coordinate Pattern discovery.
    - Coordinate Insight generation.
    - Coordinate Recommendation generation.
    - Coordinate Reflection construction.
    - Assemble the Reflection Registry.
    - Require structural validation.
    - Return a rendered reflective result.

    Engine non-responsibilities:

    - Modifying Learning Events
    - Discovering Patterns directly
    - Generating Insights directly
    - Generating Recommendations directly
    - Repairing invalid Reflection
    - Persisting Reflection
    """

    if not learning_events:
        raise ValueError(
            "Reflection requires at least one Learning Event."
        )

    patterns = discover_patterns(learning_events)

    insights = generate_insights(
        patterns,
        learning_events,
    )

    recommendations = generate_recommendations(
        insights,
        patterns,
    )

    reflection = build_reflection(
        learning_events,
        patterns,
        insights,
        recommendations,
    )

    registry = build_reflection_registry(
        patterns=patterns,
        insights=insights,
        recommendations=recommendations,
        reflections=[reflection],
    )

    if not validate_reflection_registry(registry):
        raise ReflectionValidationError(
            "Reflection Registry is invalid and cannot be rendered."
        )

    return render_reflection_registry(registry)
