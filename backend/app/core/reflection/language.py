"""
Reflection Language

This module defines the canonical vocabulary used by SentinelAI's
Reflection subsystem.

Reflection examines learning across time.

It never modifies historical learning.
It produces structured insight and recommendations for future learning.
"""

from typing import Final, Literal


ReflectionStatus = Literal[
    "complete",
    "limited",
    "insufficient_evidence",
]

PatternKind = Literal[
    "recurrence",
    "stability",
    "revision",
    "contradiction",
    "evidence_gap",
    "confidence_trend",
]

RecommendationKind = Literal[
    "preserve",
    "strengthen",
    "reconsider",
    "investigate",
    "gather_evidence",
]


REFLECTION_DEFINITION: Final[str] = (
    "Reflection is the disciplined examination of learning across time "
    "in order to refine future understanding while remaining accountable "
    "to reality."
)

REFLECTION_LAW: Final[str] = (
    "Reflection never edits the past. It improves the future."
)

INSIGHT_DEFINITION: Final[str] = (
    "An Insight is a meaningful pattern discovered across learning history."
)

RECOMMENDATION_DEFINITION: Final[str] = (
    "A Recommendation proposes a responsible refinement for future learning "
    "without modifying historical memory."
)

PATTERN_DEFINITION: Final[str] = (
    "A Pattern is a recurring, stable, revised, contradictory, or incomplete "
    "structure discovered across multiple learning events."
)

EVIDENCE_GAP_DEFINITION: Final[str] = (
    "An Evidence Gap identifies understanding whose support is absent, weak, "
    "outdated, or insufficient."
)

CONTRADICTION_DEFINITION: Final[str] = (
    "A Contradiction identifies cognitive objects or learning events that "
    "cannot remain simultaneously coherent without further examination."
)

STABILITY_DEFINITION: Final[str] = (
    "Stability describes understanding that remains consistently supported "
    "across learning events."
)

CONFIDENCE_TREND_DEFINITION: Final[str] = (
    "A Confidence Trend describes how confidence in understanding changes "
    "across time."
)

LEARNING_OPPORTUNITY_DEFINITION: Final[str] = (
    "A Learning Opportunity identifies where future observation or evidence "
    "could improve understanding."
)


CANONICAL_REFLECTION_TERMS: Final[dict[str, str]] = {
    "reflection": REFLECTION_DEFINITION,
    "insight": INSIGHT_DEFINITION,
    "recommendation": RECOMMENDATION_DEFINITION,
    "pattern": PATTERN_DEFINITION,
    "evidence_gap": EVIDENCE_GAP_DEFINITION,
    "contradiction": CONTRADICTION_DEFINITION,
    "stability": STABILITY_DEFINITION,
    "confidence_trend": CONFIDENCE_TREND_DEFINITION,
    "learning_opportunity": LEARNING_OPPORTUNITY_DEFINITION,
}

