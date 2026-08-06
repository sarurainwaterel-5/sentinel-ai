"""
Deterministic structural-integrity verification for planning results.

This specialist verifies that the planning subject forms one coherent,
inspectable planning graph.

It examines:

- identifier uniqueness,
- contiguous step sequencing,
- step references to dependencies and risks,
- dependency and risk references to steps,
- required objects for the recorded planning status,
- human-approval boundaries,
- non-execution state integrity.

It does not:

- repair the plan,
- evaluate reasoning traceability,
- evaluate semantic completeness,
- calculate verification confidence,
- determine final verification status.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

from app.services.cognition.planning.models import (
    PlanningStatus,
    PlanningStepStatus,
)
from app.services.cognition.verification.models import (
    VerificationCategory,
    VerificationCheck,
    VerificationContext,
    VerificationFinding,
    VerificationInspection,
    VerificationOutcome,
    VerificationSeverity,
    VerificationStandard,
)


class StructuralIntegrityVerifier:
    """
    Verify the internal graph and state integrity of a PlanningResult.
    """

    CATEGORY = VerificationCategory.STRUCTURAL_INTEGRITY

    @staticmethod
    def _duplicates(
        values: Iterable[str],
    ) -> list[str]:
        """
        Return duplicate values in deterministic sorted order.
        """

        counts = Counter(values)

        return sorted(
            value
            for value, count in counts.items()
            if count > 1
        )

    @staticmethod
    def _standard(
        *,
        standard_id: str,
        title: str,
        description: str,
    ) -> VerificationStandard:
        return VerificationStandard(
            standard_id=standard_id,
            category=(
                VerificationCategory.STRUCTURAL_INTEGRITY
            ),
            title=title,
            description=description,
            required=True,
            source=(
                "SentinelAI Cognitive Planning structural contract"
            ),
        )

    @staticmethod
    def _check(
        *,
        check_id: str,
        standard_id: str,
        observation: str,
        passed: bool,
        affected_object_ids: list[str] | None = None,
        recommendation: str | None = None,
        severity: VerificationSeverity = (
            VerificationSeverity.HIGH
        ),
    ) -> VerificationCheck:
        return VerificationCheck(
            check_id=check_id,
            category=(
                VerificationCategory.STRUCTURAL_INTEGRITY
            ),
            standard_id=standard_id,
            observation=observation,
            outcome=(
                VerificationOutcome.PASSED
                if passed
                else VerificationOutcome.FAILED
            ),
            severity=(
                VerificationSeverity.INFORMATIONAL
                if passed
                else severity
            ),
            affected_object_ids=(
                affected_object_ids or []
            ),
            recommendation=(
                None
                if passed
                else recommendation
            ),
        )

    @staticmethod
    def _finding_from_check(
        *,
        finding_id: str,
        check: VerificationCheck,
        title: str,
        description: str,
        required_resolution: str,
        blocking: bool = True,
    ) -> VerificationFinding:
        return VerificationFinding(
            finding_id=finding_id,
            category=(
                VerificationCategory.STRUCTURAL_INTEGRITY
            ),
            title=title,
            description=description,
            severity=check.severity,
            affected_object_ids=(
                check.affected_object_ids
            ),
            evidence=[
                check.observation,
            ],
            required_resolution=required_resolution,
            blocking=blocking,
            source_check_ids=[
                check.check_id,
            ],
        )

    def _identifier_check(
        self,
        *,
        object_name: str,
        values: list[str],
        standard_id: str,
        check_id: str,
    ) -> tuple[
        VerificationCheck,
        VerificationFinding | None,
    ]:
        duplicates = self._duplicates(values)
        passed = not duplicates

        check = self._check(
            check_id=check_id,
            standard_id=standard_id,
            observation=(
                f"All {object_name} identifiers are unique."
                if passed
                else (
                    f"Duplicate {object_name} identifiers were "
                    f"found: {duplicates}"
                )
            ),
            passed=passed,
            affected_object_ids=duplicates,
            recommendation=(
                f"Assign a unique identifier to every "
                f"{object_name} object."
            ),
            severity=VerificationSeverity.CRITICAL,
        )

        if passed:
            return check, None

        finding = self._finding_from_check(
            finding_id=f"finding-{check_id}",
            check=check,
            title=(
                f"Duplicate {object_name} identifiers"
            ),
            description=(
                f"The planning subject contains duplicate "
                f"{object_name} identifiers, preventing reliable "
                "graph references."
            ),
            required_resolution=(
                f"Replace duplicate {object_name} identifiers "
                "and update every affected reference."
            ),
        )

        return check, finding

    def inspect(
        self,
        *,
        context: VerificationContext,
    ) -> VerificationInspection:
        """
        Inspect one PlanningResult for structural integrity.
        """

        subject = context.subject
        standards: list[VerificationStandard] = [
            self._standard(
                standard_id="structure-unique-step-ids",
                title="Step identifiers are unique",
                description=(
                    "Every planning step must have a unique identifier."
                ),
            ),
            self._standard(
                standard_id="structure-unique-dependency-ids",
                title="Dependency identifiers are unique",
                description=(
                    "Every planning dependency must have a unique "
                    "identifier."
                ),
            ),
            self._standard(
                standard_id="structure-unique-risk-ids",
                title="Risk identifiers are unique",
                description=(
                    "Every planning risk must have a unique identifier."
                ),
            ),
            self._standard(
                standard_id="structure-contiguous-sequence",
                title="Step sequencing is contiguous",
                description=(
                    "Step sequence values must begin at one and remain "
                    "contiguous."
                ),
            ),
            self._standard(
                standard_id="structure-reference-integrity",
                title="Planning references resolve",
                description=(
                    "Steps, dependencies, and risks may reference only "
                    "objects that exist in the planning subject."
                ),
            ),
            self._standard(
                standard_id="structure-status-integrity",
                title="Planning status matches structure",
                description=(
                    "The recorded planning status must be compatible "
                    "with the strategy and steps present."
                ),
            ),
            self._standard(
                standard_id="structure-human-authority",
                title="Human approval remains required",
                description=(
                    "Every proposed Sprint 16 planning step must remain "
                    "explicitly approval-gated."
                ),
            ),
            self._standard(
                standard_id="structure-non-execution",
                title="Planning remains non-executing",
                description=(
                    "Planning steps must remain proposed, blocked, or "
                    "approval-required rather than claiming execution."
                ),
            ),
        ]

        checks: list[VerificationCheck] = []
        findings: list[VerificationFinding] = []
        conditions: list[str] = []

        step_ids = [
            step.step_id
            for step in subject.steps
        ]

        dependency_ids = [
            dependency.dependency_id
            for dependency in subject.dependencies
        ]

        risk_ids = [
            risk.risk_id
            for risk in subject.risks
        ]

        for object_name, values, standard_id, check_id in [
            (
                "step",
                step_ids,
                "structure-unique-step-ids",
                "check-unique-step-ids",
            ),
            (
                "dependency",
                dependency_ids,
                "structure-unique-dependency-ids",
                "check-unique-dependency-ids",
            ),
            (
                "risk",
                risk_ids,
                "structure-unique-risk-ids",
                "check-unique-risk-ids",
            ),
        ]:
            check, finding = self._identifier_check(
                object_name=object_name,
                values=values,
                standard_id=standard_id,
                check_id=check_id,
            )

            checks.append(check)

            if finding is not None:
                findings.append(finding)
                conditions.append(
                    finding.required_resolution or finding.description
                )

        sequences = sorted(
            step.sequence
            for step in subject.steps
        )

        expected_sequences = list(
            range(1, len(subject.steps) + 1)
        )

        sequence_valid = (
            sequences == expected_sequences
        )

        sequence_check = self._check(
            check_id="check-contiguous-step-sequence",
            standard_id="structure-contiguous-sequence",
            observation=(
                "Step sequencing begins at one and is contiguous."
                if sequence_valid
                else (
                    f"Observed step sequence values {sequences}; "
                    f"expected {expected_sequences}."
                )
            ),
            passed=sequence_valid,
            affected_object_ids=step_ids,
            recommendation=(
                "Renumber steps so sequence values begin at one "
                "and remain contiguous."
            ),
            severity=VerificationSeverity.HIGH,
        )

        checks.append(sequence_check)

        if not sequence_valid:
            finding = self._finding_from_check(
                finding_id="finding-step-sequence-integrity",
                check=sequence_check,
                title="Invalid planning step sequence",
                description=(
                    "The step sequence does not form one contiguous "
                    "ordered course of action."
                ),
                required_resolution=(
                    "Renumber the planning steps into a contiguous "
                    "sequence beginning at one."
                ),
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        valid_step_ids = set(step_ids)
        valid_dependency_ids = set(dependency_ids)
        valid_risk_ids = set(risk_ids)

        unknown_references: list[str] = []
        affected_objects: list[str] = []

        for step in subject.steps:
            for dependency_id in step.dependency_ids:
                if dependency_id not in valid_dependency_ids:
                    unknown_references.append(
                        f"{step.step_id} -> {dependency_id}"
                    )
                    affected_objects.append(step.step_id)

            for risk_id in step.risk_ids:
                if risk_id not in valid_risk_ids:
                    unknown_references.append(
                        f"{step.step_id} -> {risk_id}"
                    )
                    affected_objects.append(step.step_id)

        for dependency in subject.dependencies:
            for step_id in dependency.required_before_step_ids:
                if step_id not in valid_step_ids:
                    unknown_references.append(
                        f"{dependency.dependency_id} -> {step_id}"
                    )
                    affected_objects.append(
                        dependency.dependency_id
                    )

        for risk in subject.risks:
            for step_id in risk.affected_step_ids:
                if step_id not in valid_step_ids:
                    unknown_references.append(
                        f"{risk.risk_id} -> {step_id}"
                    )
                    affected_objects.append(risk.risk_id)

        references_valid = not unknown_references

        reference_check = self._check(
            check_id="check-reference-integrity",
            standard_id="structure-reference-integrity",
            observation=(
                "All planning graph references resolve."
                if references_valid
                else (
                    "Unresolved planning references were found: "
                    f"{sorted(set(unknown_references))}"
                )
            ),
            passed=references_valid,
            affected_object_ids=sorted(
                set(affected_objects)
            ),
            recommendation=(
                "Repair or remove every reference to a planning "
                "object that does not exist."
            ),
            severity=VerificationSeverity.CRITICAL,
        )

        checks.append(reference_check)

        if not references_valid:
            finding = self._finding_from_check(
                finding_id="finding-reference-integrity",
                check=reference_check,
                title="Unresolved planning references",
                description=(
                    "The planning graph contains references to "
                    "objects that are not present."
                ),
                required_resolution=(
                    "Repair all unresolved step, dependency, and "
                    "risk references before further verification."
                ),
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        status_valid = True
        status_observation = (
            "Planning status is compatible with the subject structure."
        )

        if subject.status == PlanningStatus.COMPLETE:
            status_valid = (
                subject.strategy is not None
                and bool(subject.steps)
            )

        elif (
            subject.status
            == PlanningStatus.INSUFFICIENT_REASONING
        ):
            status_valid = (
                subject.strategy is None
                and not subject.steps
            )

        elif subject.status == PlanningStatus.BLOCKED:
            status_valid = True

        elif (
            subject.status
            == PlanningStatus.REQUIRES_CLARIFICATION
        ):
            status_valid = (
                subject.strategy is not None
            )

        if not status_valid:
            status_observation = (
                f"Planning status '{subject.status.value}' is not "
                "compatible with the strategy or steps present."
            )

        status_check = self._check(
            check_id="check-status-integrity",
            standard_id="structure-status-integrity",
            observation=status_observation,
            passed=status_valid,
            affected_object_ids=step_ids,
            recommendation=(
                "Reconcile the recorded planning status with the "
                "strategy and steps actually present."
            ),
            severity=VerificationSeverity.HIGH,
        )

        checks.append(status_check)

        if not status_valid:
            finding = self._finding_from_check(
                finding_id="finding-status-integrity",
                check=status_check,
                title="Planning status conflicts with structure",
                description=status_observation,
                required_resolution=(
                    "Correct the planning status or regenerate the "
                    "planning result."
                ),
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        unapproved_steps = [
            step.step_id
            for step in subject.steps
            if not step.requires_human_approval
        ]

        approval_valid = not unapproved_steps

        approval_check = self._check(
            check_id="check-human-approval-boundary",
            standard_id="structure-human-authority",
            observation=(
                "Every proposed planning step requires human approval."
                if approval_valid
                else (
                    "The following steps are not explicitly "
                    f"approval-gated: {unapproved_steps}"
                )
            ),
            passed=approval_valid,
            affected_object_ids=unapproved_steps,
            recommendation=(
                "Require explicit human approval for every proposed "
                "planning step."
            ),
            severity=VerificationSeverity.CRITICAL,
        )

        checks.append(approval_check)

        if not approval_valid:
            finding = self._finding_from_check(
                finding_id="finding-human-approval-boundary",
                check=approval_check,
                title="Human approval boundary missing",
                description=(
                    "One or more proposed steps could advance without "
                    "an explicit approval requirement."
                ),
                required_resolution=(
                    "Restore human approval requirements before the "
                    "plan is eligible for governance review."
                ),
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        invalid_execution_states = [
            step.step_id
            for step in subject.steps
            if step.status not in {
                PlanningStepStatus.PROPOSED,
                PlanningStepStatus.BLOCKED,
                PlanningStepStatus.REQUIRES_APPROVAL,
            }
        ]

        non_execution_valid = (
            not invalid_execution_states
        )

        non_execution_check = self._check(
            check_id="check-non-execution-boundary",
            standard_id="structure-non-execution",
            observation=(
                "Every planning step remains in a non-executing state."
                if non_execution_valid
                else (
                    "Steps contain unsupported execution states: "
                    f"{invalid_execution_states}"
                )
            ),
            passed=non_execution_valid,
            affected_object_ids=invalid_execution_states,
            recommendation=(
                "Return every planning step to a proposed, blocked, "
                "or approval-required state."
            ),
            severity=VerificationSeverity.CRITICAL,
        )

        checks.append(non_execution_check)

        if not non_execution_valid:
            finding = self._finding_from_check(
                finding_id="finding-non-execution-boundary",
                check=non_execution_check,
                title="Planning contains execution state",
                description=(
                    "The planning subject contains a step state outside "
                    "the approved non-execution boundary."
                ),
                required_resolution=(
                    "Remove execution state from the planning result "
                    "and route approved work through a future execution "
                    "faculty."
                ),
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        return VerificationInspection(
            category=self.CATEGORY,
            standards=standards,
            checks=checks,
            findings=findings,
            conditions=list(
                dict.fromkeys(conditions)
            ),
            inspection_trace=[
                "Inspected planning identifiers.",
                "Inspected step sequencing.",
                "Inspected planning graph references.",
                "Inspected status compatibility.",
                "Inspected human-approval boundaries.",
                "Inspected non-execution state integrity.",
            ],
            completed=True,
        )
