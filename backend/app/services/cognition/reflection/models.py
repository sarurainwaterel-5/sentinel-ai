"""
Structured contracts for SentinelAI's cognitive Reflection Faculty.

Reflection examines accumulated learning across time.

Reflection:

- discovers meaningful historical patterns,
- produces evidence-grounded insights,
- recommends responsible refinements for future learning,
- preserves complete provenance to examined Learning Events,
- measures confidence in the reflective judgment.

Reflection does not:

- modify historical Learning Events,
- rewrite memory,
- execute recommendations,
- manufacture patterns from isolated events,
- grant constitutional authority to itself.

Reflection never edits the past.
It improves the future.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    model_validator,
)


class ReflectionStatus(StrEnum):
    """
    Lifecycle state of one reflective operation.
    """

    COMPLETE = "complete"
    LIMITED = "limited"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class ReflectionPatternKind(StrEnum):
    """
    Canonical kinds of historical patterns recognized by Reflection.
    """

    RECURRENCE = "recurrence"
    STABILITY = "stability"
    REVISION = "revision"
    CONTRADICTION = "contradiction"
    EVIDENCE_GAP = "evidence_gap"
    CONFIDENCE_TREND = "confidence_trend"


class ReflectionRecommendationKind(StrEnum):
    """
    Canonical forms of recommendation produced by Reflection.
    """

    PRESERVE = "preserve"
    STRENGTHEN = "strengthen"
    RECONSIDER = "reconsider"
    INVESTIGATE = "investigate"
    GATHER_EVIDENCE = "gather_evidence"


class ReflectionConfidenceLevel(StrEnum):
    """
    Human-readable confidence bands for reflective support.
    """

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class ReflectionPattern(BaseModel):
    """
    A meaningful structure discovered across multiple Learning Events.

    A Pattern describes history.

    It never modifies the Learning Events from which it was derived.
    """

    pattern_id: str = Field(
        min_length=1,
    )

    kind: ReflectionPatternKind

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    learning_event_ids: list[str] = Field(
        min_length=2,
        description=(
            "Patterns require support from multiple Learning Events."
        ),
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
    )

    domain_ids: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class ReflectionInsight(BaseModel):
    """
    A meaningful interpretation produced from one or more Patterns.

    An Insight explains what accumulated learning history reveals.
    """

    insight_id: str = Field(
        min_length=1,
    )

    title: str = Field(
        min_length=1,
    )

    explanation: str = Field(
        min_length=1,
    )

    pattern_ids: list[str] = Field(
        min_length=1,
    )

    learning_event_ids: list[str] = Field(
        default_factory=list,
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
    )

    domain_ids: list[str] = Field(
        default_factory=list,
    )

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class ReflectionRecommendation(BaseModel):
    """
    A responsible proposal for improving future learning.

    Recommendations possess no execution authority.
    """

    recommendation_id: str = Field(
        min_length=1,
    )

    kind: ReflectionRecommendationKind

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    insight_ids: list[str] = Field(
        min_length=1,
    )

    pattern_ids: list[str] = Field(
        default_factory=list,
    )

    domain_ids: list[str] = Field(
        default_factory=list,
    )

    priority: int | None = Field(
        default=None,
        ge=1,
    )

    requires_human_approval: bool = True

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class ReflectionConfidenceFactor(BaseModel):
    """
    One explainable factor contributing to Reflection confidence.
    """

    name: str = Field(
        min_length=1,
    )

    contribution: float = Field(
        ge=-1.0,
        le=1.0,
    )

    explanation: str = Field(
        min_length=1,
    )


class ReflectionConfidence(BaseModel):
    """
    Confidence in the reflective judgment itself.

    Reflection confidence is separate from:

    - confidence in historical Learning Events,
    - confidence in individual Insights,
    - constitutional coherence,
    - execution authority.
    """

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    level: ReflectionConfidenceLevel

    basis: str = Field(
        min_length=1,
    )

    factors: list[ReflectionConfidenceFactor] = Field(
        default_factory=list,
    )

    uncertainty: list[str] = Field(
        default_factory=list,
    )


class ReflectionResult(BaseModel):
    """
    Complete authoritative output of one reflective operation.

    ReflectionResult preserves the provenance graph:

    Learning Events
        ↓
    Patterns
        ↓
    Insights
        ↓
    Recommendations

    Historical cognition remains immutable.
    """

    title: str = Field(
        min_length=1,
    )

    summary: str = Field(
        min_length=1,
    )

    learning_event_ids: list[str] = Field(
        default_factory=list,
    )

    patterns: list[ReflectionPattern] = Field(
        default_factory=list,
    )

    insights: list[ReflectionInsight] = Field(
        default_factory=list,
    )

    recommendations: list[ReflectionRecommendation] = Field(
        default_factory=list,
    )

    confidence: ReflectionConfidence

    reflection_trace: list[str] = Field(
        default_factory=list,
        description=(
            "High-level, user-safe reflective stages. "
            "This is not private chain-of-thought."
        ),
    )

    status: ReflectionStatus

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @model_validator(mode="after")
    def validate_reflection_structure(
        self,
    ) -> "ReflectionResult":
        """
        Enforce provenance and constitutional Reflection structure.

        This validator protects the integrity of the reflective graph.
        """

        learning_event_ids = set(
            self.learning_event_ids
        )

        pattern_ids = [
            pattern.pattern_id
            for pattern in self.patterns
        ]

        insight_ids = [
            insight.insight_id
            for insight in self.insights
        ]

        recommendation_ids = [
            recommendation.recommendation_id
            for recommendation in self.recommendations
        ]

        if len(pattern_ids) != len(set(pattern_ids)):
            raise ValueError(
                "Reflection pattern IDs must be unique."
            )

        if len(insight_ids) != len(set(insight_ids)):
            raise ValueError(
                "Reflection insight IDs must be unique."
            )

        if len(recommendation_ids) != len(
            set(recommendation_ids)
        ):
            raise ValueError(
                "Reflection recommendation IDs must be unique."
            )

        valid_pattern_ids = set(pattern_ids)
        valid_insight_ids = set(insight_ids)

        for pattern in self.patterns:
            unknown_learning_events = (
                set(pattern.learning_event_ids)
                - learning_event_ids
            )

            if unknown_learning_events:
                raise ValueError(
                    f"Pattern '{pattern.pattern_id}' references "
                    "unknown learning event IDs: "
                    f"{sorted(unknown_learning_events)}"
                )

        for insight in self.insights:
            unknown_patterns = (
                set(insight.pattern_ids)
                - valid_pattern_ids
            )

            if unknown_patterns:
                raise ValueError(
                    f"Insight '{insight.insight_id}' references "
                    "unknown pattern IDs: "
                    f"{sorted(unknown_patterns)}"
                )

            unknown_learning_events = (
                set(insight.learning_event_ids)
                - learning_event_ids
            )

            if unknown_learning_events:
                raise ValueError(
                    f"Insight '{insight.insight_id}' references "
                    "unknown learning event IDs: "
                    f"{sorted(unknown_learning_events)}"
                )

        for recommendation in self.recommendations:
            unknown_insights = (
                set(recommendation.insight_ids)
                - valid_insight_ids
            )

            if unknown_insights:
                raise ValueError(
                    "Recommendation "
                    f"'{recommendation.recommendation_id}' "
                    "references unknown insight IDs: "
                    f"{sorted(unknown_insights)}"
                )

            unknown_patterns = (
                set(recommendation.pattern_ids)
                - valid_pattern_ids
            )

            if unknown_patterns:
                raise ValueError(
                    "Recommendation "
                    f"'{recommendation.recommendation_id}' "
                    "references unknown pattern IDs: "
                    f"{sorted(unknown_patterns)}"
                )

        if (
            self.status == ReflectionStatus.COMPLETE
            and len(learning_event_ids) < 2
        ):
            raise ValueError(
                "A complete Reflection requires multiple learning events."
            )

        if (
            self.status
            == ReflectionStatus.INSUFFICIENT_EVIDENCE
            and (
                self.patterns
                or self.insights
                or self.recommendations
            )
        ):
            raise ValueError(
                "An insufficient_evidence Reflection cannot claim "
                "authoritative patterns, insights, or recommendations."
            )

        return self
