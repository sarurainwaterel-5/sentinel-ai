"""
SentinelAI Cognitive Verification Engine.

The verification engine coordinates Sentinel's planning-verification
pipeline.

It does not perform specialist verification logic directly.

Instead it orchestrates:

PlanningResult
        ↓
Structural Integrity
        ↓
Traceability
        ↓
Completeness
        ↓
Constraint Compliance
        ↓
Coverage
        ↓
Verification Confidence
        ↓
VerificationResult
"""

from __future__ import annotations

from app.services.cognition.verification.completeness_verifier import (
    CompletenessVerifier,
)
from app.services.cognition.verification.constraint_verifier import (
    ConstraintVerifier,
)
from app.services.cognition.verification.models import (
    VerificationCategory,
    VerificationContext,
    VerificationFinding,
    VerificationInspection,
    VerificationOutcome,
    VerificationResult,
    VerificationSeverity,
    VerificationStatus,
    VerificationSubject,
)
from app.services.cognition.verification.structural_integrity_verifier import (
    StructuralIntegrityVerifier,
)
from app.services.cognition.verification.traceability_verifier import (
    TraceabilityVerifier,
)
from app.services.cognition.verification.verification_confidence_engine import (
    VerificationConfidenceEngine,
)
from app.services.cognition.verification.verification_coverage_engine import (
    VerificationCoverageEngine,
)


class VerificationEngine:
    """
    Coordinate Sentinel's cognitive verification faculty.

    Specialized verification remains delegated to independent engines.
    """

    def __init__(self):
        self.structural_integrity = (
            StructuralIntegrityVerifier()
        )
        self.traceability = TraceabilityVerifier()
        self.completeness = CompletenessVerifier()
        self.constraints = ConstraintVerifier()

        self.coverage = VerificationCoverageEngine()
        self.confidence = VerificationConfidenceEngine()

    @staticmethod
    def _build_subject(
        context: VerificationContext,
    ) -> VerificationSubject:
        """
        Build a stable internal reference to the verified PlanningResult.
        """

        subject = context.subject

        strategy_name = (
            subject.strategy.name
            if subject.strategy is not None
            else None
        )

        return VerificationSubject(
            subject_type=context.subject_type,
            objective=subject.objective.statement,
            subject_status=subject.status.value,
            subject_confidence_score=(
                subject.confidence.score
            ),
            subject_confidence_level=(
                subject.confidence.level.value
            ),
            strategy_name=strategy_name,
            step_ids=[
                step.step_id
                for step in subject.steps
            ],
            dependency_ids=[
                dependency.dependency_id
                for dependency in subject.dependencies
            ],
            risk_ids=[
                risk.risk_id
                for risk in subject.risks
            ],
            constraint_count=len(
                subject.constraints
            ),
            metadata={
                "workspace": context.workspace,
                "module": context.module,
                "topic": context.topic,
                "organization_id": (
                    context.organization_id
                ),
                "mission_id": context.mission_id,
                "session_id": context.session_id,
            },
        )

    @staticmethod
    def _inspection_map(
        engine: "VerificationEngine",
    ) -> dict[
        VerificationCategory,
        object,
    ]:
        """
        Map verification categories to their specialist verifiers.
        """

        return {
            VerificationCategory.STRUCTURAL_INTEGRITY: (
                engine.structural_integrity
            ),
            VerificationCategory.TRACEABILITY: (
                engine.traceability
            ),
            VerificationCategory.COMPLETENESS: (
                engine.completeness
            ),
            VerificationCategory.CONSTRAINT_COMPLIANCE: (
                engine.constraints
            ),
        }

    def _run_inspections(
        self,
        *,
        context: VerificationContext,
    ) -> list[VerificationInspection]:
        """
        Run only the specialist categories requested by the context.
        """

        verifier_map = self._inspection_map(
            self
        )

        inspections: list[
            VerificationInspection
        ] = []

        for category in context.requested_categories:
            verifier = verifier_map.get(
                category
            )

            if verifier is None:
                continue

            inspection = verifier.inspect(
                context=context
            )

            inspections.append(
                inspection
            )

        return inspections

    @staticmethod
    def _aggregate_findings(
        inspections: list[
            VerificationInspection
        ],
    ) -> list[VerificationFinding]:
        """
        Flatten specialist findings while preserving inspection order.
        """

        return [
            finding
            for inspection in inspections
            for finding in inspection.findings
        ]

    @staticmethod
    def _aggregate_conditions(
        inspections: list[
            VerificationInspection
        ],
    ) -> list[str]:
        """
        Preserve unique verification conditions in deterministic order.
        """

        conditions = [
            condition.strip()
            for inspection in inspections
            for condition in inspection.conditions
            if condition.strip()
        ]

        return list(
            dict.fromkeys(conditions)
        )

    @staticmethod
    def _status(
        *,
        inspections: list[
            VerificationInspection
        ],
        findings: list[
            VerificationFinding
        ],
    ) -> VerificationStatus:
        """
        Determine the authoritative verification status.

        Status reflects the condition of the verified subject.

        It does not measure verification confidence.
        """

        if not inspections:
            return VerificationStatus.BLOCKED

        if any(
            not inspection.completed
            for inspection in inspections
        ):
            return VerificationStatus.BLOCKED

        checks = [
            check
            for inspection in inspections
            for check in inspection.checks
        ]

        if any(
            check.outcome
            == VerificationOutcome.NOT_VERIFIABLE
            for check in checks
        ):
            return (
                VerificationStatus.INSUFFICIENT_BASIS
            )

        blocking_findings = [
            finding
            for finding in findings
            if finding.blocking
        ]

        failed_checks = [
            check
            for check in checks
            if check.outcome
            == VerificationOutcome.FAILED
        ]

        if (
            blocking_findings
            or failed_checks
        ):
            return (
                VerificationStatus.REQUIRES_REVISION
            )

        conditional_checks = [
            check
            for check in checks
            if (
                check.outcome
                == VerificationOutcome.PASSED_WITH_CONDITIONS
            )
        ]

        non_blocking_findings = [
            finding
            for finding in findings
            if not finding.blocking
        ]

        if (
            conditional_checks
            or non_blocking_findings
        ):
            return (
                VerificationStatus.VERIFIED_WITH_CONDITIONS
            )

        return VerificationStatus.VERIFIED

    def verify(
        self,
        *,
        context: VerificationContext,
    ) -> VerificationResult:
        """
        Produce one complete verification operation.

        The result is fully inspectable and contains no hidden
        verification reasoning.
        """

        trace: list[str] = []

        trace.append(
            "Received the planning subject."
        )

        inspections = self._run_inspections(
            context=context
        )

        trace.append(
            "Completed requested specialist inspections."
        )

        coverage = self.coverage.assess(
            requested_categories=(
                context.requested_categories
            ),
            inspections=inspections,
        )

        trace.append(
            "Calculated verification coverage."
        )

        confidence = self.confidence.assess(
            coverage=coverage,
            inspections=inspections,
        )

        trace.append(
            "Calculated verification confidence."
        )

        standards = [
            standard
            for inspection in inspections
            for standard in inspection.standards
        ]

        checks = [
            check
            for inspection in inspections
            for check in inspection.checks
        ]

        findings = self._aggregate_findings(
            inspections
        )

        conditions = self._aggregate_conditions(
            inspections
        )

        status = self._status(
            inspections=inspections,
            findings=findings,
        )

        trace.append(
            "Determined verification status."
        )

        trace.append(
            "Produced authoritative verification result."
        )

        return VerificationResult(
            subject=self._build_subject(
                context
            ),
            scope=context.scope,
            standards=standards,
            checks=checks,
            findings=findings,
            conditions=conditions,
            coverage=coverage,
            confidence=confidence,
            verification_trace=trace,
            status=status,
            metadata={
                **context.metadata,
                "requested_category_count": len(
                    context.requested_categories
                ),
                "completed_inspection_count": len(
                    inspections
                ),
            },
        )
