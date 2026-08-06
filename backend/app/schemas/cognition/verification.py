"""
Public API contracts for SentinelAI's cognitive verification subsystem.

These schemas separate:

- verification objectives and retrieval controls,
- verification scope and categories,
- authoritative structured verification,
- human-readable communication,
- constitutional coherence,
- source provenance,
- workflow metadata.

The internal verification models remain owned by the verification
subsystem.

Verification inspects cognition.

Verification does not replace reasoning, revise planning, make governance
decisions, or execute actions.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class VerificationRequest(BaseModel):
    """
    Request one evidence-aware planning-and-verification operation.

    Sprint 16 verifies a PlanningResult created internally by Sentinel.

    API consumers provide an objective and verification boundaries rather
    than constructing or submitting internal planning objects directly.
    """

    objective: str = Field(
        min_length=1,
        description=(
            "The outcome Sentinel should reason about, plan for, "
            "and verify."
        ),
    )

    workspace: str = Field(
        default="bridge",
        min_length=1,
        description=(
            "The cognitive workspace initiating the verification "
            "operation."
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
        description="Organization boundary used during knowledge retrieval.",
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

    constraints: list[str] = Field(
        default_factory=list,
        description=(
            "Known limitations the generated plan and its verification "
            "must respect."
        ),
    )

    verification_scope: str = Field(
        default="full",
        min_length=1,
        description=(
            "Declared boundary of the verification operation, such as "
            "full, structural, traceability, completeness, or constraints."
        ),
    )

    verification_categories: list[str] = Field(
        default_factory=lambda: [
            "structural_integrity",
            "traceability",
            "completeness",
            "constraint_compliance",
        ],
        description=(
            "Verification dimensions Sentinel should inspect."
        ),
    )

    mission_id: str | None = Field(
        default=None,
        description="Optional teaching or operational mission identifier.",
    )

    session_id: str | None = Field(
        default=None,
        description=(
            "Optional conversation or verification-session identifier."
        ),
    )

    @field_validator(
        "objective",
        "workspace",
        "organization_id",
        "verification_scope",
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

    @field_validator(
        "constraints",
        "verification_categories",
        mode="before",
    )
    @classmethod
    def normalize_text_lists(cls, value: Any) -> Any:
        """
        Normalize text-list fields and remove blank entries.
        """

        if value is None:
            return []

        if not isinstance(value, list):
            return value

        normalized: list[Any] = []
        seen: set[str] = set()

        for item in value:
            if not isinstance(item, str):
                normalized.append(item)
                continue

            cleaned = item.strip()

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            normalized.append(cleaned)

        return normalized


class VerificationConfidenceSummary(BaseModel):
    """
    Consumer-facing confidence in the verification assessment.

    Verification confidence evaluates the quality and coverage of the
    inspection itself. It is distinct from reasoning confidence and
    planning confidence.
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


class VerificationStandardSummary(BaseModel):
    """
    One explicit rule or expectation used to verify the subject.
    """

    standard_id: str = Field(
        min_length=1,
    )

    category: str = Field(
        min_length=1,
    )

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    required: bool = True

    source: str | None = None


class VerificationCheckSummary(BaseModel):
    """
    One bounded examination of a property of the planning subject.
    """

    check_id: str = Field(
        min_length=1,
    )

    category: str = Field(
        min_length=1,
    )

    standard_id: str = Field(
        min_length=1,
    )

    observation: str = Field(
        min_length=1,
    )

    outcome: str

    severity: str

    evidence_references: list[str] = Field(
        default_factory=list,
    )

    affected_object_ids: list[str] = Field(
        default_factory=list,
    )

    recommendation: str | None = None

    uncertainty: list[str] = Field(
        default_factory=list,
    )


class VerificationFindingSummary(BaseModel):
    """
    One meaningful defect, unresolved condition, or notable observation.
    """

    finding_id: str = Field(
        min_length=1,
    )

    category: str = Field(
        min_length=1,
    )

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    severity: str

    affected_object_ids: list[str] = Field(
        default_factory=list,
    )

    evidence: list[str] = Field(
        default_factory=list,
    )

    required_resolution: str | None = None

    blocking: bool = False


class VerificationCoverageSummary(BaseModel):
    """
    Public summary of what the verification operation examined.
    """

    requested_categories: list[str] = Field(
        default_factory=list,
    )

    completed_categories: list[str] = Field(
        default_factory=list,
    )

    skipped_categories: list[str] = Field(
        default_factory=list,
    )

    check_count: int = Field(
        default=0,
        ge=0,
    )

    passed_count: int = Field(
        default=0,
        ge=0,
    )

    conditional_count: int = Field(
        default=0,
        ge=0,
    )

    failed_count: int = Field(
        default=0,
        ge=0,
    )

    unverifiable_count: int = Field(
        default=0,
        ge=0,
    )

    not_applicable_count: int = Field(
        default=0,
        ge=0,
    )


class VerifiedPlanningSubjectSummary(BaseModel):
    """
    Stable public reference to the PlanningResult under verification.

    This summary exposes the subject identity and major planning state
    without duplicating the complete PlanningResponse contract.
    """

    objective: str

    strategy: str | None = None

    planning_status: str

    planning_confidence_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    planning_confidence_level: str

    step_count: int = Field(
        default=0,
        ge=0,
    )

    dependency_count: int = Field(
        default=0,
        ge=0,
    )

    assumption_count: int = Field(
        default=0,
        ge=0,
    )

    risk_count: int = Field(
        default=0,
        ge=0,
    )

    constraint_count: int = Field(
        default=0,
        ge=0,
    )


class VerificationSummary(BaseModel):
    """
    Authoritative structured assessment produced by Verification.

    This section is machine-readable and does not require downstream
    consumers to parse the human-readable verification narrative.
    """

    subject_type: str = "planning_result"

    subject: VerifiedPlanningSubjectSummary

    verification_scope: str

    standards: list[VerificationStandardSummary] = Field(
        default_factory=list,
    )

    checks: list[VerificationCheckSummary] = Field(
        default_factory=list,
    )

    findings: list[VerificationFindingSummary] = Field(
        default_factory=list,
    )

    conditions: list[str] = Field(
        default_factory=list,
    )

    coverage: VerificationCoverageSummary

    confidence: VerificationConfidenceSummary

    verification_trace: list[str] = Field(
        default_factory=list,
        description=(
            "High-level, user-safe verification stages. "
            "This is not private chain-of-thought."
        ),
    )

    status: str


class VerificationCommunicationSummary(BaseModel):
    """
    Human-readable presentation generated after verification is complete.

    These fields may improve clarity but may not change checks, findings,
    conditions, coverage, confidence, or verification status.
    """

    answer: str

    subject_explanation: str

    checks_explanation: str

    findings_explanation: str

    conditions_explanation: str

    confidence_explanation: str


class VerificationCoherenceResult(BaseModel):
    """
    Constitutional coherence evaluation for the verified planning mission.

    Coherence remains independent from verification confidence.
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


class VerificationResponse(BaseModel):
    """
    Final public response from Sentinel's cognitive verification pipeline.

    The response preserves clear boundaries between:

    - verification communication,
    - authoritative structured verification,
    - the planning subject under inspection,
    - constitutional coherence,
    - source provenance,
    - workflow metadata.

    No field in this response represents revision, approval, or execution.
    """

    answer: str

    communication: VerificationCommunicationSummary

    verification: VerificationSummary

    coherence: VerificationCoherenceResult

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
