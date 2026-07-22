"""
Reflection Builder

Reflection is not generated.

Reflection is organized.

The Builder assembles Patterns, Insights, Recommendations,
and Reflections into a Reflection Registry.

The Builder never modifies Learning Events.

The Builder never performs validation.

The Builder never performs rendering.
"""

from app.core.reflection.models import (
    Insight,
    Pattern,
    Recommendation,
    Reflection,
    ReflectionRegistry,
)


def build_reflection_registry(
    *,
    patterns: list[Pattern],
    insights: list[Insight],
    recommendations: list[Recommendation],
    reflections: list[Reflection],
) -> ReflectionRegistry:
    """
    Assemble SentinelAI's Reflection Registry.

    Responsibilities:

    - Organize reflective objects.
    - Preserve architectural consistency.
    - Return a complete Reflection Registry.

    Non-responsibilities:

    - Pattern discovery
    - Insight generation
    - Recommendation generation
    - Validation
    - Rendering
    - Persistence
    """

    return ReflectionRegistry(
        patterns=patterns,
        insights=insights,
        recommendations=recommendations,
        reflections=reflections,
    )
