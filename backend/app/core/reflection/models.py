from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.reflection.language import (
    PatternKind,
    RecommendationKind,
    ReflectionStatus,
)


@dataclass(slots=True)
class Pattern:
    """
    A meaningful structure discovered across Learning Events.

    Patterns describe recurrence, stability, revision, contradiction,
    evidence gaps, or confidence trends.

    A Pattern never modifies the Learning Events it examines.
    """

    pattern_id: str
    kind: PatternKind
    title: str
    description: str

    learning_event_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Insight:
    """
    A meaningful interpretation produced from one or more Patterns.

    An Insight explains what the examined learning history reveals.
    """

    insight_id: str
    title: str
    explanation: str

    pattern_ids: list[str] = field(default_factory=list)
    learning_event_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Recommendation:
    """
    A responsible proposal for improving future learning.

    Recommendations never modify historical cognition.
    They guide what should be preserved, strengthened, reconsidered,
    investigated, or supported with additional evidence.
    """

    recommendation_id: str
    kind: RecommendationKind
    title: str
    description: str

    insight_ids: list[str] = field(default_factory=list)
    pattern_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    priority: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Reflection:
    """
    One completed examination of accumulated learning.

    Reflection examines history and produces Patterns, Insights, and
    Recommendations without modifying Learning Events or cognitive memory.
    """

    reflection_id: str = field(
        default_factory=lambda: f"reflection-{uuid4()}"
    )

    title: str = ""
    summary: str = ""
    status: ReflectionStatus = "complete"

    learning_event_ids: list[str] = field(default_factory=list)
    pattern_ids: list[str] = field(default_factory=list)
    insight_ids: list[str] = field(default_factory=list)
    recommendation_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    reflected_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReflectionRegistry:
    """
    SentinelAI's assembled reflective state.

    The registry contains completed reflective objects.

    It does not modify the Learning Events or Cognitive Registry from
    which those objects were derived.
    """

    patterns: list[Pattern] = field(default_factory=list)
    insights: list[Insight] = field(default_factory=list)
    recommendations: list[Recommendation] = field(default_factory=list)
    reflections: list[Reflection] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
