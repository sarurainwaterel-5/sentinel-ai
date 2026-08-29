"""
Structured contracts for SentinelAI's evidence-grounded reasoning layer.

These models make the path from evidence to conclusion explicit,
inspectable, and reusable across domains.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class EvidenceDisposition(StrEnum):
    """How a piece of evidence relates to a candidate conclusion."""

    SUPPORTING = "supporting"
    CONFLICTING = "conflicting"
    CONTEXTUAL = "contextual"
    UNKNOWN = "unknown"


class ConfidenceLevel(StrEnum):
    """Human-readable confidence bands used across reasoning results."""

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class EvidenceSource(BaseModel):
    """
    Canonical reference to one retrieved evidence item.

    This preserves provenance without coupling reasoning models directly
    to Qdrant point objects.
    """

    document_id: str | None = None
    filename: str | None = None
    file_hash: str | None = None

    module: str | None = None
    topic: str | None = None
    collection: str | None = None
    organization_id: str | None = None

    chunk_index: int | None = None
    score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Normalized retrieval similarity score.",
    )

    text: str = ""
    status: str | None = None
    description: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional source metadata not yet promoted to fields.",
    )


class EvidenceItem(BaseModel):
    """
    One interpreted piece of evidence.

    The analyzer assigns a disposition and explains how the evidence
    relates to the reasoning task.
    """

    statement: str
    disposition: EvidenceDisposition

    source: EvidenceSource

    relevance_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    rationale: str = ""

    supports_claims: list[str] = Field(
        default_factory=list,
    )

    conflicts_with_claims: list[str] = Field(
        default_factory=list,
    )


class EvidenceGap(BaseModel):
    """A missing fact, measurement, or source required for stronger reasoning."""

    description: str
    impact: str
    recommended_source: str | None = None


class EvidenceBundle(BaseModel):
    """
    Organized evidence produced before inference.

    Retrieval finds relevant chunks. Evidence analysis turns those chunks
    into a structured bundle that later engines can reason over.
    """

    question: str

    supporting: list[EvidenceItem] = Field(
        default_factory=list,
    )

    conflicting: list[EvidenceItem] = Field(
        default_factory=list,
    )

    contextual: list[EvidenceItem] = Field(
        default_factory=list,
    )

    unknown: list[EvidenceItem] = Field(
        default_factory=list,
    )

    gaps: list[EvidenceGap] = Field(
        default_factory=list,
    )

    source_count: int = 0
    document_count: int = 0
    domain_count: int = 0

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

class Premise(BaseModel):
    """
    One explicit proposition extracted from evidence.

    A Premise preserves the evidence lineage from which
    the proposition was derived.

    Premises do not represent final conclusions.
    """

    premise_id: str = Field(
        min_length=1,
    )

    statement: str = Field(
        min_length=1,
    )

    evidence_ids: list[str] = Field(
        min_length=1,
    )

    domain_ids: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class PremiseRelationshipKind(StrEnum):
    """
    Canonical relationship types between reasoning premises.
    """

    SUPPORTS = "supports"
    CONFLICTS = "conflicts"
    COMPLEMENTS = "complements"
    INDEPENDENT = "independent"
    UNRESOLVED = "unresolved"


class PremiseRelationship(BaseModel):
    """
    One explicit directional relationship between two Premises.

    Relationship assessment describes how propositions relate.

    It does not synthesize a new proposition.
    """

    source_premise_id: str = Field(
        min_length=1,
    )

    target_premise_id: str = Field(
        min_length=1,
    )

    kind: PremiseRelationshipKind

    basis: str = Field(
        min_length=1,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def validate_distinct_premises(
        self,
    ):
        if (
            self.source_premise_id
            == self.target_premise_id
        ):
            raise ValueError(
                "A premise relationship must reference "
                "two distinct premises."
            )

        return self


class SynthesizedProposition(BaseModel):
    """
    One higher-order proposition derived from multiple
    evidence-grounded Premises.

    A SynthesizedProposition preserves its complete lineage
    back to the Premises and Evidence that support it.

    It is not itself a final inference or conclusion.
    """

    proposition_id: str = Field(
        min_length=1,
    )

    statement: str = Field(
        min_length=1,
    )

    premise_ids: list[str] = Field(
        min_length=2,
        description=(
            "A synthesized proposition must be derived "
            "from at least two Premises."
        ),
    )

    evidence_ids: list[str] = Field(
        min_length=1,
    )

    domain_ids: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

class Assumption(BaseModel):
    """An assumption required to move from evidence toward an inference."""

    statement: str
    justification: str
    risk: str = "unknown"


class Inference(BaseModel):
    """
    A candidate conclusion derived from evidence.

    An inference is not automatically the final conclusion. It remains
    inspectable and may be accepted, rejected, or qualified later.
    """

    statement: str

    supporting_evidence_ids: list[str] = Field(
        default_factory=list,
    )

    conflicting_evidence_ids: list[str] = Field(
        default_factory=list,
    )

    assumptions: list[Assumption] = Field(
        default_factory=list,
    )

    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    limitations: list[str] = Field(
        default_factory=list,
    )


class ConfidenceFactor(BaseModel):
    """One explainable factor contributing to confidence."""

    name: str
    contribution: float = Field(
        ge=-1.0,
        le=1.0,
    )
    explanation: str


class ConfidenceAssessment(BaseModel):
    """
    Transparent confidence assessment for a conclusion.

    Confidence is treated as an explainable assessment, not merely a
    copied retrieval score.
    """

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    level: ConfidenceLevel
    basis: str

    factors: list[ConfidenceFactor] = Field(
        default_factory=list,
    )

    uncertainty: list[str] = Field(
        default_factory=list,
    )


class ReasoningConclusion(BaseModel):
    """
    Final supported conclusion produced by the reasoning engine.
    """

    statement: str

    evidence_summary: str
    inference_summary: str

    confidence: ConfidenceAssessment

    limitations: list[str] = Field(
        default_factory=list,
    )

    alternatives: list[str] = Field(
        default_factory=list,
    )

    missing_information: list[str] = Field(
        default_factory=list,
    )

    recommended_next_step: str | None = None


class ReasoningResult(BaseModel):
    """
    Complete inspectable output of one reasoning operation.
    """

    question: str

    evidence: EvidenceBundle
    
    premises: list[Premise] = Field(
        default_factory=list,
    )

    premise_relationships: list[PremiseRelationship] = Field(
        default_factory=list,
    )

    synthesized_propositions: list[
        SynthesizedProposition
    ] = Field(
        default_factory=list,
    )

    inferences: list[Inference] = Field(
        default_factory=list,
    )

    conclusion: ReasoningConclusion | None = None

    reasoning_trace: list[str] = Field(
        default_factory=list,
        description=(
            "High-level, user-safe reasoning stages. "
            "This is not private chain-of-thought."
        ),
    )

    status: str = "complete"

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

