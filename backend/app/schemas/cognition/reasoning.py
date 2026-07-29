"""
Public API contracts for SentinelAI's cognition subsystem.

These schemas separate:

- request and retrieval controls,
- authoritative structured reasoning,
- human-readable communication,
- constitutional coherence,
- source provenance,
- workflow metadata.

The internal reasoning models remain owned by the reasoning subsystem.
These API schemas expose a stable, consumer-friendly representation.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReasoningRequest(BaseModel):
    """
    Request one evidence-grounded reasoning operation.

    The request exposes retrieval boundaries without coupling API
    consumers directly to Qdrant or the retrieval implementation.
    """

    question: str = Field(
        min_length=1,
        description="The question Sentinel should investigate.",
    )

    workspace: str = Field(
        default="bridge",
        min_length=1,
        description=(
            "The cognitive workspace initiating the reasoning operation."
        ),
    )

    module: str | None = Field(
        default=None,
        description=(
            "Optional knowledge-module filter, such as engineering, "
            "trading, sre, or incident_response."
        ),
    )

    topic: str | None = Field(
        default=None,
        description="Optional topic filter within the selected module.",
    )

    organization_id: str = Field(
        default="default",
        min_length=1,
        description="Organization boundary used during retrieval.",
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=25,
        description="Maximum number of knowledge chunks to retrieve.",
    )

    score_threshold: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum semantic similarity score accepted during retrieval."
        ),
    )

    mission_id: str | None = Field(
        default=None,
        description="Optional teaching or operational mission identifier.",
    )

    session_id: str | None = Field(
        default=None,
        description="Optional conversation or reasoning-session identifier.",
    )

    @field_validator(
        "question",
        "workspace",
        "organization_id",
        mode="before",
    )
    @classmethod
    def normalize_required_text(cls, value: Any) -> Any:
        """
        Reject whitespace-only required values and normalize boundaries.
        """

        if not isinstance(value, str):
            return value

        normalized = value.strip()

        if not normalized:
            raise ValueError("Value must not be empty.")

        return normalized

    @field_validator(
        "module",
        "topic",
        "mission_id",
        "session_id",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value: Any) -> Any:
        """
        Normalize optional text and convert whitespace-only values to None.
        """

        if value is None or not isinstance(value, str):
            return value

        normalized = value.strip()

        return normalized or None


class ConfidenceSummary(BaseModel):
    """
    Consumer-facing confidence representation.

    The values originate from the deterministic ConfidenceEngine.
    """

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    level: str

    basis: str

    factors: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    uncertainty: list[str] = Field(
        default_factory=list,
    )


class EvidenceSourceSummary(BaseModel):
    """
    Stable source-provenance representation for API consumers.

    This model does not expose Qdrant-specific point structures.
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
    )

    text: str = ""

    status: str | None = None
    description: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class EvidenceSummary(BaseModel):
    """
    Summary and provenance of the evidence used during reasoning.
    """

    source_count: int = Field(
        default=0,
        ge=0,
    )

    document_count: int = Field(
        default=0,
        ge=0,
    )

    domain_count: int = Field(
        default=0,
        ge=0,
    )

    sources: list[EvidenceSourceSummary] = Field(
        default_factory=list,
    )

    gaps: list[str] = Field(
        default_factory=list,
    )


class ReasoningSummary(BaseModel):
    """
    Authoritative structured judgment produced by Sentinel's reasoning core.

    This section is machine-readable and does not require natural-language
    parsing by downstream agents or interfaces.
    """

    conclusion: str | None = None

    evidence_summary: str | None = None

    inference_summary: str | None = None

    confidence: ConfidenceSummary

    evidence: EvidenceSummary

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

    reasoning_trace: list[str] = Field(
        default_factory=list,
        description=(
            "High-level, user-safe reasoning stages. "
            "This is not private chain-of-thought."
        ),
    )

    status: str


class CommunicationSummary(BaseModel):
    """
    Human-readable presentation generated after reasoning is complete.

    These fields may improve clarity but may not alter Sentinel's
    authoritative conclusion, confidence, limitations, or next step.
    """

    answer: str

    evidence_explanation: str

    confidence_explanation: str

    limitations_explanation: str

    next_step_explanation: str


class CoherenceResult(BaseModel):
    """
    Constitutional coherence evaluation.

    Coherence remains independent from evidentiary confidence.
    """

    coherent: bool

    constitutional_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    articles_consulted: list[str] = Field(
        default_factory=list,
    )

    conflicts: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )


class ReasoningResponse(BaseModel):
    """
    Final public response from Sentinel's cognition pipeline.

    The response preserves clear boundaries between:

    - communication,
    - authoritative reasoning,
    - constitutional coherence,
    - source provenance,
    - workflow metadata.
    """

    answer: str

    communication: CommunicationSummary

    reasoning: ReasoningSummary

    coherence: CoherenceResult

    constitutional_sources: list[str] = Field(
        default_factory=list,
    )

    knowledge_sources: list[str] = Field(
        default_factory=list,
    )

    workspace: str

    module: str | None = None

    topic: str | None = None

    organization_id: str = "default"

    mission_id: str | None = None

    session_id: str | None = None
