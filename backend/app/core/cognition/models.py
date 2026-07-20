from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4


CognitiveObjectType = Literal[
    "observation",
    "evidence",
    "concept",
    "principle",
    "relationship",
    "learning_event",
    "understanding",
]


@dataclass(slots=True)
class Observation:
    """
    A descriptive record of something SentinelAI perceived.

    Observations contain no interpretation or conclusion.
    """

    observation_id: str
    source: str
    content: str
    observed_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Evidence:
    """
    A traceable reference that anchors a claim to reality.
    """

    evidence_id: str
    title: str
    source: str
    description: str
    supports: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Concept:
    """
    A reusable unit of knowledge recognized by SentinelAI.
    """

    concept_id: str
    name: str
    description: str
    domain_ids: list[str] = field(default_factory=list)
    aliases: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Principle:
    """
    An enduring rule that governs interpretation or action.
    """

    principle_id: str
    name: str
    statement: str
    domain_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Relationship:
    """
    A directed connection between two cognitive objects.
    """

    relationship_id: str
    source_id: str
    predicate: str
    target_id: str
    evidence_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Understanding:
    """
    Organized knowledge produced through disciplined reasoning.
    """

    understanding_id: str
    title: str
    explanation: str
    domain_ids: list[str] = field(default_factory=list)
    concept_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)
    relationship_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class LearningEvent:
    """
    A record of how SentinelAI's understanding changed.
    """

    learning_event_id: str = field(
        default_factory=lambda: str(uuid4())
    )
    source: str = ""
    domain_ids: list[str] = field(default_factory=list)

    observations_added: list[str] = field(default_factory=list)
    evidence_added: list[str] = field(default_factory=list)
    concepts_added: list[str] = field(default_factory=list)
    principles_added: list[str] = field(default_factory=list)
    relationships_added: list[str] = field(default_factory=list)
    understandings_added: list[str] = field(default_factory=list)

    summary: str = ""
    learned_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
@dataclass(slots=True)
class CognitiveRegistry:
    """
    SentinelAI's assembled cognitive state.

    The registry contains what Sentinel has learned without validating,
    interpreting, or modifying the underlying cognitive objects.
    """

    observations: list[Observation] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    concepts: list[Concept] = field(default_factory=list)
    principles: list[Principle] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    understandings: list[Understanding] = field(default_factory=list)
    learning_events: list[LearningEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

