"""
Structured contracts for SentinelAI's cognitive verification layer.

These models make the inspection of an existing cognitive result explicit,
inspectable, and reusable across operational domains.

Sprint 16 begins with PlanningResult as the verified subject.

Verification:

- receives an authoritative planning result,
- applies explicit standards,
- performs bounded checks,
- records findings and conditions,
- measures verification coverage,
- calculates verification confidence,
- produces one authoritative VerificationResult.

Verification does not revise planning.
Verification does not make governance decisions.
Verification does not execute actions.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from app.services.cognition.planning.models import (
    PlanningResult,
)


class VerificationSubjectType(StrEnum):
    """
    Supported cognitive result types that may be verified.
    """

    PLANNING_RESULT = "planning_result"


class VerificationScope(StrEnum):
    """
    Declared boundary of one verification operation.
    """

    FULL = "full"
    STRUCTURAL = "structural"
    TRACEABILITY = "traceability"
    COMPLETENESS = "completeness"
    CONSTRAINTS = "constraints"


class VerificationCategory(StrEnum):
    """
    Independent cognitive dimensions examined during verification.
    """

    STRUCTURAL_INTEGRITY = "structural_integrity"
    TRACEABILITY = "traceability"
    COMPLETENESS = "completeness"
    CONSTRAINT_COMPLIANCE = "constraint_compliance"


class VerificationOutcome(StrEnum):
    """
    Result of one bounded verification check.
    """

    PASSED = "passed"
    PASSED_WITH_CONDITIONS = "passed_with_conditions"
    FAILED = "failed"
    NOT_VERIFIABLE = "not_verifiable"
    NOT_APPLICABLE = "not_applicable"


class VerificationSeverity(StrEnum):
    """
    Consequence of leaving a verification finding unresolved.

    Severity represents impact, not confidence.
    """

    INFORMATIONAL = "informational"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class VerificationConfidenceLevel(StrEnum):
    """
    Human-readable confidence bands for verification quality.
    """

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class VerificationStatus(StrEnum):
    """
    Authoritative state of one complete verification operation.
    """

    VERIFIED = "verified"
    VERIFIED_WITH_CONDITIONS = "verified_with_conditions"
    REQUIRES_REVISION = "requires_revision"
    INSUFFICIENT_BASIS = "insufficient_basis"
    BLOCKED = "blocked"


class VerificationContext(BaseModel):
    """
    Input boundary for one planning-verification operation.

    The verifier receives an authoritative PlanningResult and explicit
    verification boundaries. It does not recreate the plan or retrieve
    new evidence independently.
    """

    subject: PlanningResult = Field(
        description=(
            "The authoritative PlanningResult under inspection."
        ),
    )

    subject_type: VerificationSubjectType = (
        VerificationSubjectType.PLANNING_RESULT
    )

    scope: VerificationScope = VerificationScope.FULL

    requested_categories: list[
        VerificationCategory
    ] = Field(
        default_factory=lambda: [
            VerificationCategory.STRUCTURAL_INTEGRITY,
            VerificationCategory.TRACEABILITY,
            VerificationCategory.COMPLETENESS,
            VerificationCategory.CONSTRAINT_COMPLIANCE,
        ],
    )

    governing_constraints: list[str] = Field(
        default_factory=list,
    )

    workspace: str | None = None
    module: str | None = None
    topic: str | None = None
    organization_id: str = "default"

    mission_id: str | None = None
    session_id: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator(
        "organization_id",
        mode="before",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: Any,
    ) -> Any:
        """
        Reject whitespace-only required text.
        """

        if not isinstance(value, str):
            return value

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Value must not be empty."
            )

        return normalized

    @field_validator(
        "workspace",
        "module",
        "topic",
        "mission_id",
        "session_id",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: Any,
    ) -> Any:
        """
        Convert whitespace-only optional text to None.
        """

        if value is None or not isinstance(value, str):
            return value

        normalized = value.strip()

        return normalized or None

    @field_validator(
        "governing_constraints",
        mode="before",
    )
    @classmethod
    def normalize_constraints(
        cls,
        value: Any,
    ) -> Any:
        """
        Normalize and deduplicate governing constraints.
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

    @field_validator(
        "requested_categories",
        mode="after",
    )
    @classmethod
    def deduplicate_categories(
        cls,
        value: list[VerificationCategory],
    ) -> list[VerificationCategory]:
        """
        Preserve category order while removing duplicates.
        """

        return list(
            dict.fromkeys(value)
        )


class VerificationSubject(BaseModel):
    """
    Stable internal reference to the cognitive result being verified.

    Sprint 16 verifies PlanningResult while preserving a subject contract
    that may later support other cognitive result types.
    """

    subject_type: VerificationSubjectType

    objective: str = Field(
        min_length=1,
    )

    subject_status: str

    subject_confidence_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    subject_confidence_level: str

    strategy_name: str | None = None

    step_ids: list[str] = Field(
        default_factory=list,
    )

    dependency_ids: list[str] = Field(
        default_factory=list,
    )

    risk_ids: list[str] = Field(
        default_factory=list,
    )

    constraint_count: int = Field(
        default=0,
        ge=0,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class VerificationStandard(BaseModel):
    """
    One explicit rule or expectation applied to the verified subject.

    Standards remain visible so verification does not rely on hidden
    acceptance criteria.
    """

    standard_id: str = Field(
        min_length=1,
    )

    category: VerificationCategory

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    required: bool = True

    source: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class VerificationCheck(BaseModel):
    """
    One bounded examination of one property of the verified subject.

    A check records what was examined, what was observed, and whether the
    applicable standard was satisfied.
    """

    check_id: str = Field(
        min_length=1,
    )

    category: VerificationCategory

    standard_id: str = Field(
        min_length=1,
    )

    observation: str = Field(
        min_length=1,
    )

    outcome: VerificationOutcome

    severity: VerificationSeverity = (
        VerificationSeverity.INFORMATIONAL
    )

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

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )


class VerificationFinding(BaseModel):
    """
    One meaningful defect, condition, or notable verification observation.

    Findings describe issues. They do not revise the verified subject.
    """

    finding_id: str = Field(
        min_length=1,
    )

    category: VerificationCategory

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    severity: VerificationSeverity

    affected_object_ids: list[str] = Field(
        default_factory=list,
    )

    evidence: list[str] = Field(
        default_factory=list,
    )

    required_resolution: str | None = None

    blocking: bool = False

    source_check_ids: list[str] = Field(
        default_factory=list,
    )

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

class VerificationInspection(BaseModel):
    """
    Structured output produced by one specialist verifier.

    Each verifier returns the standards it applied, the checks it
    completed, and any findings or conditions it discovered.

    It does not calculate verification confidence or final status.
    """

    category: VerificationCategory

    standards: list[VerificationStandard] = Field(
        default_factory=list,
    )

    checks: list[VerificationCheck] = Field(
        default_factory=list,
    )

    findings: list[VerificationFinding] = Field(
        default_factory=list,
    )

    conditions: list[str] = Field(
        default_factory=list,
    )

    inspection_trace: list[str] = Field(
        default_factory=list,
        description=(
            "High-level, user-safe specialist inspection stages. "
            "This is not private chain-of-thought."
        ),
    )

    completed: bool = True

    @model_validator(mode="after")
    def validate_inspection_references(
        self,
    ) -> "VerificationInspection":
        """
        Ensure specialist checks and findings remain internally coherent.
        """

        standard_ids = {
            standard.standard_id
            for standard in self.standards
        }

        check_ids = {
            check.check_id
            for check in self.checks
        }

        for standard in self.standards:
            if standard.category != self.category:
                raise ValueError(
                    "Every inspection standard must match "
                    "the inspection category."
                )

        for check in self.checks:
            if check.category != self.category:
                raise ValueError(
                    "Every inspection check must match "
                    "the inspection category."
                )

            if check.standard_id not in standard_ids:
                raise ValueError(
                    f"Check '{check.check_id}' references "
                    "an unknown specialist standard."
                )

        for finding in self.findings:
            if finding.category != self.category:
                raise ValueError(
                    "Every inspection finding must match "
                    "the inspection category."
                )

            unknown_checks = (
                set(finding.source_check_ids)
                - check_ids
            )

            if unknown_checks:
                raise ValueError(
                    f"Finding '{finding.finding_id}' references "
                    f"unknown check IDs: {sorted(unknown_checks)}"
                )

        return self


class VerificationCoverage(BaseModel):
    """
    Complete record of what the verification operation examined.

    Coverage prevents a partial inspection from being represented as a
    comprehensive verification.
    """

    requested_categories: list[
        VerificationCategory
    ] = Field(
        default_factory=list,
    )

    completed_categories: list[
        VerificationCategory
    ] = Field(
        default_factory=list,
    )

    skipped_categories: list[
        VerificationCategory
    ] = Field(
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

    coverage_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    @model_validator(mode="after")
    def validate_check_counts(
        self,
    ) -> "VerificationCoverage":
        """
        Ensure the recorded outcome counts equal the total check count.
        """

        classified_count = (
            self.passed_count
            + self.conditional_count
            + self.failed_count
            + self.unverifiable_count
            + self.not_applicable_count
        )

        if classified_count != self.check_count:
            raise ValueError(
                "Verification coverage outcome counts must "
                "equal check_count."
            )

        return self


class VerificationConfidenceFactor(BaseModel):
    """
    One explainable factor contributing to verification confidence.
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


class VerificationConfidence(BaseModel):
    """
    Transparent assessment of the verification operation's reliability.

    This evaluates confidence in the inspection itself, not confidence in
    the original reasoning conclusion or planning result.
    """

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    level: VerificationConfidenceLevel

    basis: str = Field(
        min_length=1,
    )

    factors: list[
        VerificationConfidenceFactor
    ] = Field(
        default_factory=list,
    )

    uncertainty: list[str] = Field(
        default_factory=list,
    )


class VerificationResult(BaseModel):
    """
    Complete authoritative output of one verification operation.

    This result records standards, checks, findings, conditions, coverage,
    and verification confidence without modifying the verified subject.
    """

    subject: VerificationSubject

    scope: VerificationScope

    standards: list[VerificationStandard] = Field(
        default_factory=list,
    )

    checks: list[VerificationCheck] = Field(
        default_factory=list,
    )

    findings: list[VerificationFinding] = Field(
        default_factory=list,
    )

    conditions: list[str] = Field(
        default_factory=list,
    )

    coverage: VerificationCoverage

    confidence: VerificationConfidence

    verification_trace: list[str] = Field(
        default_factory=list,
        description=(
            "High-level, user-safe verification stages. "
            "This is not private chain-of-thought."
        ),
    )

    status: VerificationStatus

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @model_validator(mode="after")
    def validate_verification_structure(
        self,
    ) -> "VerificationResult":
        """
        Validate identifiers and references across verification objects.

        This ensures the result forms one coherent inspection record
        rather than disconnected standards, checks, and findings.
        """

        standard_ids = [
            standard.standard_id
            for standard in self.standards
        ]

        check_ids = [
            check.check_id
            for check in self.checks
        ]

        finding_ids = [
            finding.finding_id
            for finding in self.findings
        ]

        if len(standard_ids) != len(
            set(standard_ids)
        ):
            raise ValueError(
                "Verification standard IDs must be unique."
            )

        if len(check_ids) != len(
            set(check_ids)
        ):
            raise ValueError(
                "Verification check IDs must be unique."
            )

        if len(finding_ids) != len(
            set(finding_ids)
        ):
            raise ValueError(
                "Verification finding IDs must be unique."
            )

        valid_standard_ids = set(standard_ids)
        valid_check_ids = set(check_ids)

        for check in self.checks:
            if (
                check.standard_id
                not in valid_standard_ids
            ):
                raise ValueError(
                    f"Check '{check.check_id}' references "
                    f"unknown standard ID "
                    f"'{check.standard_id}'."
                )

        for finding in self.findings:
            unknown_checks = (
                set(finding.source_check_ids)
                - valid_check_ids
            )

            if unknown_checks:
                raise ValueError(
                    f"Finding '{finding.finding_id}' "
                    "references unknown check IDs: "
                    f"{sorted(unknown_checks)}"
                )

        actual_completed_categories = set(
            check.category
            for check in self.checks
        )

        declared_completed_categories = set(
            self.coverage.completed_categories
        )

        if (
            actual_completed_categories
            != declared_completed_categories
        ):
            raise ValueError(
                "Coverage completed_categories must match "
                "the categories represented by checks."
            )

        requested_categories = set(
            self.coverage.requested_categories
        )

        skipped_categories = set(
            self.coverage.skipped_categories
        )

        if not declared_completed_categories.issubset(
            requested_categories
        ):
            raise ValueError(
                "Completed verification categories must be "
                "included in requested_categories."
            )

        if not skipped_categories.issubset(
            requested_categories
        ):
            raise ValueError(
                "Skipped verification categories must be "
                "included in requested_categories."
            )

        if (
            declared_completed_categories
            & skipped_categories
        ):
            raise ValueError(
                "A verification category cannot be both "
                "completed and skipped."
            )

        if self.coverage.check_count != len(
            self.checks
        ):
            raise ValueError(
                "Verification coverage check_count must "
                "equal the number of recorded checks."
            )

        blocking_findings = [
            finding
            for finding in self.findings
            if finding.blocking
        ]

        if (
            self.status
            == VerificationStatus.VERIFIED
            and blocking_findings
        ):
            raise ValueError(
                "A verified result cannot contain "
                "blocking findings."
            )

        failed_checks = [
            check
            for check in self.checks
            if (
                check.outcome
                == VerificationOutcome.FAILED
            )
        ]

        if (
            self.status
            == VerificationStatus.VERIFIED
            and failed_checks
        ):
            raise ValueError(
                "A verified result cannot contain "
                "failed verification checks."
            )

        if (
            self.status
            == VerificationStatus.REQUIRES_REVISION
            and not (
                failed_checks
                or blocking_findings
            )
        ):
            raise ValueError(
                "A requires_revision result must contain "
                "a failed check or blocking finding."
            )

        return self
