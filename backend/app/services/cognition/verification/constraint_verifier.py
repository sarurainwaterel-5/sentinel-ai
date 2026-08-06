"""
Deterministic constraint verification for planning results.

This specialist verifies that explicit governing constraints remain
preserved throughout the planning subject and that structured operational
boundaries remain intact.

It examines:

- governing-constraint preservation,
- objective-constraint preservation,
- planning-result constraint visibility,
- human-approval boundaries,
- non-execution step states.

Sprint 16 deliberately avoids pretending that arbitrary natural-language
constraint violations can be detected reliably through loose semantic
inference.

It does not:

- repair constraint violations,
- generate replacement strategies or steps,
- verify structural graph integrity,
- verify reasoning traceability,
- assess general planning completeness,
- calculate verification confidence,
- determine final verification status.
"""

from __future__ import annotations

from app.services.cognition.planning.models import (
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


class ConstraintVerifier:
    """
    Verify preservation of explicit constraints and operating boundaries.
    """

    CATEGORY = VerificationCategory.CONSTRAINT_COMPLIANCE

    @staticmethod
    def _normalize(
        value: str,
    ) -> str:
        """
        Normalize text for deterministic constraint comparison.
        """

        return " ".join(
            value.casefold().split()
        )

    @classmethod
    def _normalized_map(
        cls,
        values: list[str],
    ) -> dict[str, str]:
        """
        Map normalized constraint text to its original representation.
        """

        return {
            cls._normalize(value): value
            for value in values
            if value.strip()
        }

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
                VerificationCategory.CONSTRAINT_COMPLIANCE
            ),
            title=title,
            description=description,
            required=True,
            source=(
                "SentinelAI Cognitive Planning constraint contract"
            ),
        )

    @staticmethod
    def _check(
        *,
        check_id: str,
        standard_id: str,
        observation: str,
        outcome: VerificationOutcome,
        severity: VerificationSeverity = (
            VerificationSeverity.INFORMATIONAL
        ),
        affected_object_ids: list[str] | None = None,
        evidence_references: list[str] | None = None,
        recommendation: str | None = None,
        uncertainty: list[str] | None = None,
    ) -> VerificationCheck:
        return VerificationCheck(
            check_id=check_id,
            category=(
                VerificationCategory.CONSTRAINT_COMPLIANCE
            ),
            standard_id=standard_id,
            observation=observation,
            outcome=outcome,
            severity=severity,
            affected_object_ids=(
                affected_object_ids or []
            ),
            evidence_references=(
                evidence_references or []
            ),
            recommendation=recommendation,
            uncertainty=uncertainty or [],
        )

    @staticmethod
    def _finding(
        *,
        finding_id: str,
        check: VerificationCheck,
        title: str,
        description: str,
        required_resolution: str,
        blocking: bool,
    ) -> VerificationFinding:
        return VerificationFinding(
            finding_id=finding_id,
            category=(
                VerificationCategory.CONSTRAINT_COMPLIANCE
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

    @classmethod
    def _missing_constraints(
        cls,
        *,
        required: list[str],
        recorded: list[str],
    ) -> list[str]:
        """
        Return required constraints absent from the recorded collection.
        """

        recorded_normalized = set(
            cls._normalized_map(recorded)
        )

        return [
            original
            for normalized, original in (
                cls._normalized_map(required)
                .items()
            )
            if normalized not in recorded_normalized
        ]

    def inspect(
        self,
        *,
        context: VerificationContext,
    ) -> VerificationInspection:
        """
        Inspect one PlanningResult for explicit constraint preservation.
        """

        subject = context.subject

        standards = [
            self._standard(
                standard_id="constraint-governing-preservation",
                title="Governing constraints are preserved",
                description=(
                    "Every governing constraint supplied to verification "
                    "must remain visible in the planning result."
                ),
            ),
            self._standard(
                standard_id="constraint-objective-preservation",
                title="Objective constraints are preserved",
                description=(
                    "Every constraint recorded in the planning objective "
                    "must remain visible in the planning result."
                ),
            ),
            self._standard(
                standard_id="constraint-result-visibility",
                title="Planning constraints remain explicit",
                description=(
                    "A planning result must expose its declared "
                    "constraints rather than relying on hidden state."
                ),
            ),
            self._standard(
                standard_id="constraint-human-approval",
                title="Human approval boundary is preserved",
                description=(
                    "Every proposed planning step must remain explicitly "
                    "gated by human approval."
                ),
            ),
            self._standard(
                standard_id="constraint-non-execution",
                title="Planning remains non-executing",
                description=(
                    "Planning step state must remain proposed, blocked, "
                    "or approval-required."
                ),
            ),
        ]

        checks: list[VerificationCheck] = []
        findings: list[VerificationFinding] = []
        conditions: list[str] = []

        # Governing constraint preservation
        missing_governing = self._missing_constraints(
            required=context.governing_constraints,
            recorded=subject.constraints,
        )

        if not context.governing_constraints:
            governing_outcome = (
                VerificationOutcome.NOT_APPLICABLE
            )
            governing_observation = (
                "No governing constraints were supplied to the "
                "verification operation."
            )
        elif not missing_governing:
            governing_outcome = VerificationOutcome.PASSED
            governing_observation = (
                "Every governing constraint remains visible in the "
                "planning result."
            )
        else:
            governing_outcome = VerificationOutcome.FAILED
            governing_observation = (
                "The following governing constraints are absent from "
                f"the planning result: {missing_governing}"
            )

        governing_check = self._check(
            check_id="check-governing-constraint-preservation",
            standard_id="constraint-governing-preservation",
            observation=governing_observation,
            outcome=governing_outcome,
            severity=(
                VerificationSeverity.HIGH
                if governing_outcome
                == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            evidence_references=[
                *context.governing_constraints,
                *subject.constraints,
            ],
            affected_object_ids=missing_governing,
            recommendation=(
                "Restore every missing governing constraint to the "
                "planning result before governance review."
                if governing_outcome
                == VerificationOutcome.FAILED
                else None
            ),
        )

        checks.append(governing_check)

        if governing_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id=(
                    "finding-governing-constraint-preservation"
                ),
                check=governing_check,
                title="Governing constraints were dropped",
                description=governing_observation,
                required_resolution=(
                    "Regenerate or revise the plan so every governing "
                    "constraint remains explicitly represented."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        # Objective constraint preservation
        objective_constraints = (
            subject.objective.constraints
        )

        missing_objective = self._missing_constraints(
            required=objective_constraints,
            recorded=subject.constraints,
        )

        if not objective_constraints:
            objective_outcome = (
                VerificationOutcome.NOT_APPLICABLE
            )
            objective_observation = (
                "The planning objective contains no declared "
                "constraints."
            )
        elif not missing_objective:
            objective_outcome = VerificationOutcome.PASSED
            objective_observation = (
                "Every objective constraint remains visible in the "
                "planning result."
            )
        else:
            objective_outcome = VerificationOutcome.FAILED
            objective_observation = (
                "The following objective constraints are absent from "
                f"the planning result: {missing_objective}"
            )

        objective_check = self._check(
            check_id="check-objective-constraint-preservation",
            standard_id="constraint-objective-preservation",
            observation=objective_observation,
            outcome=objective_outcome,
            severity=(
                VerificationSeverity.HIGH
                if objective_outcome
                == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            evidence_references=[
                *objective_constraints,
                *subject.constraints,
            ],
            affected_object_ids=missing_objective,
            recommendation=(
                "Restore every missing objective constraint to the "
                "planning result."
                if objective_outcome
                == VerificationOutcome.FAILED
                else None
            ),
        )

        checks.append(objective_check)

        if objective_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id=(
                    "finding-objective-constraint-preservation"
                ),
                check=objective_check,
                title="Objective constraints were dropped",
                description=objective_observation,
                required_resolution=(
                    "Regenerate or revise the plan so every objective "
                    "constraint remains explicitly represented."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        # Explicit result visibility
        constraints_expected = bool(
            context.governing_constraints
            or objective_constraints
        )

        if not constraints_expected:
            visibility_outcome = (
                VerificationOutcome.NOT_APPLICABLE
            )
            visibility_observation = (
                "No explicit constraints were supplied or recorded at "
                "the objective boundary."
            )
        elif subject.constraints:
            visibility_outcome = VerificationOutcome.PASSED
            visibility_observation = (
                f"The planning result explicitly exposes "
                f"{len(subject.constraints)} constraint(s)."
            )
        else:
            visibility_outcome = VerificationOutcome.FAILED
            visibility_observation = (
                "Constraints were expected, but the planning result "
                "contains no explicit constraint record."
            )

        visibility_check = self._check(
            check_id="check-planning-constraint-visibility",
            standard_id="constraint-result-visibility",
            observation=visibility_observation,
            outcome=visibility_outcome,
            severity=(
                VerificationSeverity.CRITICAL
                if visibility_outcome
                == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            evidence_references=subject.constraints,
            recommendation=(
                "Expose all declared constraints in PlanningResult."
                if visibility_outcome
                == VerificationOutcome.FAILED
                else None
            ),
        )

        checks.append(visibility_check)

        if visibility_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-planning-constraint-visibility",
                check=visibility_check,
                title="Planning constraints are hidden or absent",
                description=visibility_observation,
                required_resolution=(
                    "Restore the explicit PlanningResult constraint "
                    "record before further governance review."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        # Human approval boundary
        steps_without_approval = [
            step.step_id
            for step in subject.steps
            if not step.requires_human_approval
        ]

        approval_preserved = not steps_without_approval

        approval_check = self._check(
            check_id="check-constraint-human-approval",
            standard_id="constraint-human-approval",
            observation=(
                "Every planning step remains explicitly gated by "
                "human approval."
                if approval_preserved
                else (
                    "The following planning steps are not explicitly "
                    f"approval-gated: {steps_without_approval}"
                )
            ),
            outcome=(
                VerificationOutcome.PASSED
                if approval_preserved
                else VerificationOutcome.FAILED
            ),
            severity=(
                VerificationSeverity.INFORMATIONAL
                if approval_preserved
                else VerificationSeverity.CRITICAL
            ),
            affected_object_ids=steps_without_approval,
            recommendation=(
                None
                if approval_preserved
                else (
                    "Restore explicit human approval requirements for "
                    "every affected planning step."
                )
            ),
        )

        checks.append(approval_check)

        if not approval_preserved:
            finding = self._finding(
                finding_id="finding-constraint-human-approval",
                check=approval_check,
                title="Human approval boundary was violated",
                description=approval_check.observation,
                required_resolution=(
                    "Require explicit human approval for every proposed "
                    "planning step."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        # Non-execution boundary
        invalid_step_states = [
            step.step_id
            for step in subject.steps
            if step.status not in {
                PlanningStepStatus.PROPOSED,
                PlanningStepStatus.BLOCKED,
                PlanningStepStatus.REQUIRES_APPROVAL,
            }
        ]

        non_execution_preserved = not invalid_step_states

        execution_check = self._check(
            check_id="check-constraint-non-execution",
            standard_id="constraint-non-execution",
            observation=(
                "Every planning step remains in a supported "
                "non-execution state."
                if non_execution_preserved
                else (
                    "The following planning steps contain unsupported "
                    f"execution state: {invalid_step_states}"
                )
            ),
            outcome=(
                VerificationOutcome.PASSED
                if non_execution_preserved
                else VerificationOutcome.FAILED
            ),
            severity=(
                VerificationSeverity.INFORMATIONAL
                if non_execution_preserved
                else VerificationSeverity.CRITICAL
            ),
            affected_object_ids=invalid_step_states,
            recommendation=(
                None
                if non_execution_preserved
                else (
                    "Return every affected step to a proposed, blocked, "
                    "or approval-required state."
                )
            ),
        )

        checks.append(execution_check)

        if not non_execution_preserved:
            finding = self._finding(
                finding_id="finding-constraint-non-execution",
                check=execution_check,
                title="Planning crossed the execution boundary",
                description=execution_check.observation,
                required_resolution=(
                    "Remove execution state from the planning subject "
                    "and preserve execution for a separate approved "
                    "faculty."
                ),
                blocking=True,
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
                "Inspected governing-constraint preservation.",
                "Inspected objective-constraint preservation.",
                "Inspected planning-result constraint visibility.",
                "Inspected human-approval boundaries.",
                "Inspected non-execution boundaries.",
            ],
            completed=True,
        )
