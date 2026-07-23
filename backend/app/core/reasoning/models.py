"""
Reasoning Models

Reasoning Models represent the constitutional structures that enable
SentinelAI to derive justified conclusions while preserving cognitive
coherence.

Models define structure.

Models never perform reasoning.

Models remain accountable to reality through traceable evidence,
principles, assumptions, counterarguments, and conclusions.
"""

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.reasoning.language import (
    CoherenceStatus,
    ConclusionStatus,
    EvidencePosition,
)


@dataclass(slots=True)
class Premise:
    """
    An explicit proposition used as a foundation for reasoning.
    """

    premise_id: str
    statement: str

    understanding_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Assumption:
    """
    A proposition accepted provisionally when direct support is incomplete.

    Assumptions must remain explicit so they cannot silently become facts.
    """

    assumption_id: str
    statement: str
    rationale: str

    evidence_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    acknowledged: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class EvidenceAssessment:
    """
    An evaluation of how evidence relates to a proposition.
    """

    assessment_id: str
    proposition_id: str
    evidence_id: str
    position: EvidencePosition
    explanation: str

    weight: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Counterargument:
    """
    A structured challenge to a proposed conclusion.

    Counterarguments protect cognitive coherence by preserving reasonable
    contradictions and alternative interpretations.
    """

    counterargument_id: str
    statement: str
    explanation: str

    challenges_premise_ids: list[str] = field(default_factory=list)
    challenges_conclusion_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Inference:
    """
    A structured connection showing how a conclusion follows from premises,
    evidence, assumptions, and principles.
    """

    inference_id: str
    explanation: str

    premise_ids: list[str] = field(default_factory=list)
    assumption_ids: list[str] = field(default_factory=list)
    evidence_assessment_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Conclusion:
    """
    A revisable judgment derived from available understanding.

    A Conclusion is not a declaration of absolute fact.
    """

    conclusion_id: str
    statement: str
    status: ConclusionStatus
    justification: str

    premise_ids: list[str] = field(default_factory=list)
    assumption_ids: list[str] = field(default_factory=list)
    inference_ids: list[str] = field(default_factory=list)
    evidence_assessment_ids: list[str] = field(default_factory=list)
    counterargument_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    confidence: float | None = None
    uncertainty: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CoherenceAssessment:
    """
    A structural assessment of whether the reasoning objects can remain
    simultaneously consistent.

    Coherence assessment never conceals unresolved contradiction.
    """

    coherence_assessment_id: str
    status: CoherenceStatus
    explanation: str

    premise_ids: list[str] = field(default_factory=list)
    assumption_ids: list[str] = field(default_factory=list)
    conclusion_ids: list[str] = field(default_factory=list)
    contradiction_ids: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReasoningReport:
    """
    One complete and traceable reasoning cycle.
    """

    reasoning_report_id: str = field(
        default_factory=lambda: f"reasoning-report-{uuid4()}"
    )

    title: str = ""
    question: str = ""
    summary: str = ""

    premise_ids: list[str] = field(default_factory=list)
    assumption_ids: list[str] = field(default_factory=list)
    evidence_assessment_ids: list[str] = field(default_factory=list)
    counterargument_ids: list[str] = field(default_factory=list)
    inference_ids: list[str] = field(default_factory=list)
    conclusion_ids: list[str] = field(default_factory=list)
    coherence_assessment_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    reasoned_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ReasoningRegistry:
    """
    SentinelAI's assembled reasoning state.

    The Registry preserves the complete structural record of one or more
    reasoning cycles without performing reasoning itself.
    """

    premises: list[Premise] = field(default_factory=list)
    assumptions: list[Assumption] = field(default_factory=list)
    evidence_assessments: list[EvidenceAssessment] = field(
        default_factory=list
    )
    counterarguments: list[Counterargument] = field(default_factory=list)
    inferences: list[Inference] = field(default_factory=list)
    conclusions: list[Conclusion] = field(default_factory=list)
    coherence_assessments: list[CoherenceAssessment] = field(
        default_factory=list
    )
    reports: list[ReasoningReport] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
