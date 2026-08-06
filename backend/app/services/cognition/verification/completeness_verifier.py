"""
Deterministic completeness verification for planning results.

This specialist determines whether a planning subject contains the
information required to be usable for its declared purpose.

It examines:

- strategy presence for actionable planning statuses,
- step presence for actionable planning statuses,
- step completion criteria,
- dependency verification methods,
- assumption explanation and consequence visibility,
- risk mitigation and contingency coverage,
- plan-level success criteria,
- planning-confidence basis,
- visibility of unresolved planning information.

It does not:

- validate planning graph references,
- verify reasoning-to-plan traceability,
- evaluate constraint compliance,
- supply missing planning content,
- calculate verification confidence,
- determine final verification status.
"""

from __future__ import annotations

from app.services.cognition.planning.models import (
    PlanningStatus,
    RiskLevel,
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


class CompletenessVerifier:
    """
    Verify whether a PlanningResult contains its required information.
    """

    CATEGORY = VerificationCategory.COMPLETENESS

    @staticmethod
    def _standard(
        *,
        standard_id: str,
        title: str,
        description: str,
    ) -> VerificationStandard:
        return VerificationStandard(
            standard_id=standard_id,
            category=VerificationCategory.COMPLETENESS,
            title=title,
            description=description,
            required=True,
            source=(
                "SentinelAI Cognitive Planning completeness contract"
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
            category=VerificationCategory.COMPLETENESS,
            standard_id=standard_id,
            observation=observation,
            outcome=outcome,
            severity=severity,
            affected_object_ids=affected_object_ids or [],
            evidence_references=evidence_references or [],
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
            category=VerificationCategory.COMPLETENESS,
            title=title,
            description=description,
            severity=check.severity,
            affected_object_ids=check.affected_object_ids,
            evidence=[
                check.observation,
            ],
            required_resolution=required_resolution,
            blocking=blocking,
            source_check_ids=[
                check.check_id,
            ],
        )

    @staticmethod
    def _requires_actionable_plan(
        status: PlanningStatus,
    ) -> bool:
        """
        Identify statuses that require a strategy and proposed steps.
        """

        return status in {
            PlanningStatus.COMPLETE,
            PlanningStatus.REQUIRES_CLARIFICATION,
        }

    def inspect(
        self,
        *,
        context: VerificationContext,
    ) -> VerificationInspection:
        """
        Inspect one PlanningResult for planning completeness.
        """

        subject = context.subject
        actionable = self._requires_actionable_plan(
            subject.status
        )

        standards = [
            self._standard(
                standard_id="complete-strategy",
                title="Required strategy is present",
                description=(
                    "An actionable planning result must contain one "
                    "selected strategy."
                ),
            ),
            self._standard(
                standard_id="complete-steps",
                title="Required planning steps are present",
                description=(
                    "An actionable planning result must contain at "
                    "least one ordered proposed step."
                ),
            ),
            self._standard(
                standard_id="complete-step-criteria",
                title="Steps contain completion criteria",
                description=(
                    "Every proposed step must contain observable "
                    "completion criteria."
                ),
            ),
            self._standard(
                standard_id="complete-dependencies",
                title="Dependencies are verifiable",
                description=(
                    "Every declared dependency must define how its "
                    "satisfaction can be verified."
                ),
            ),
            self._standard(
                standard_id="complete-assumptions",
                title="Assumptions expose their planning consequence",
                description=(
                    "Every assumption must preserve justification and "
                    "the risk created if it proves false."
                ),
            ),
            self._standard(
                standard_id="complete-risks",
                title="Risks contain response information",
                description=(
                    "Every risk must contain mitigation, and high or "
                    "critical risks must also contain contingency."
                ),
            ),
            self._standard(
                standard_id="complete-success-criteria",
                title="Plan contains success criteria",
                description=(
                    "An actionable plan must define observable "
                    "plan-level success criteria."
                ),
            ),
            self._standard(
                standard_id="complete-confidence-basis",
                title="Planning confidence contains a basis",
                description=(
                    "Planning confidence must explain why its score "
                    "and level were assigned."
                ),
            ),
            self._standard(
                standard_id="complete-unresolved-information",
                title="Unresolved information remains visible",
                description=(
                    "Unverified assumptions and unresolved reasoning "
                    "information must remain represented as planning "
                    "uncertainty."
                ),
            ),
        ]

        checks: list[VerificationCheck] = []
        findings: list[VerificationFinding] = []
        conditions: list[str] = []

        # Strategy presence
        if not actionable:
            strategy_outcome = VerificationOutcome.NOT_APPLICABLE
            strategy_observation = (
                f"Planning status '{subject.status.value}' does not "
                "require an actionable strategy."
            )
        elif subject.strategy is not None:
            strategy_outcome = VerificationOutcome.PASSED
            strategy_observation = (
                "The actionable planning result contains a selected "
                "strategy."
            )
        else:
            strategy_outcome = VerificationOutcome.FAILED
            strategy_observation = (
                "The actionable planning result contains no selected "
                "strategy."
            )

        strategy_check = self._check(
            check_id="check-required-strategy",
            standard_id="complete-strategy",
            observation=strategy_observation,
            outcome=strategy_outcome,
            severity=(
                VerificationSeverity.CRITICAL
                if strategy_outcome == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            recommendation=(
                "Select a supported strategy before treating the plan "
                "as actionable."
                if strategy_outcome == VerificationOutcome.FAILED
                else None
            ),
        )
        checks.append(strategy_check)

        if strategy_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-required-strategy",
                check=strategy_check,
                title="Required strategy is missing",
                description=strategy_observation,
                required_resolution=(
                    "Regenerate the plan with one supported selected "
                    "strategy."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(finding.required_resolution or "")

        # Step presence
        if not actionable:
            steps_outcome = VerificationOutcome.NOT_APPLICABLE
            steps_observation = (
                f"Planning status '{subject.status.value}' does not "
                "require actionable steps."
            )
        elif subject.steps:
            steps_outcome = VerificationOutcome.PASSED
            steps_observation = (
                f"The actionable plan contains {len(subject.steps)} "
                "proposed step(s)."
            )
        else:
            steps_outcome = VerificationOutcome.FAILED
            steps_observation = (
                "The actionable planning result contains no proposed "
                "steps."
            )

        steps_check = self._check(
            check_id="check-required-steps",
            standard_id="complete-steps",
            observation=steps_observation,
            outcome=steps_outcome,
            severity=(
                VerificationSeverity.CRITICAL
                if steps_outcome == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            recommendation=(
                "Decompose the selected strategy into ordered proposed "
                "steps."
                if steps_outcome == VerificationOutcome.FAILED
                else None
            ),
        )
        checks.append(steps_check)

        if steps_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-required-steps",
                check=steps_check,
                title="Required planning steps are missing",
                description=steps_observation,
                required_resolution=(
                    "Generate ordered proposed steps before governance "
                    "review."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(finding.required_resolution or "")

        # Step completion criteria
        missing_step_criteria = [
            step.step_id
            for step in subject.steps
            if not any(
                criterion.strip()
                for criterion in step.completion_criteria
            )
        ]

        if not subject.steps:
            criteria_outcome = VerificationOutcome.NOT_APPLICABLE
            criteria_observation = (
                "No planning steps exist to inspect for completion "
                "criteria."
            )
        elif not missing_step_criteria:
            criteria_outcome = VerificationOutcome.PASSED
            criteria_observation = (
                "Every proposed step contains observable completion "
                "criteria."
            )
        else:
            criteria_outcome = VerificationOutcome.FAILED
            criteria_observation = (
                "The following steps contain no observable completion "
                f"criteria: {missing_step_criteria}"
            )

        criteria_check = self._check(
            check_id="check-step-completion-criteria",
            standard_id="complete-step-criteria",
            observation=criteria_observation,
            outcome=criteria_outcome,
            severity=(
                VerificationSeverity.HIGH
                if criteria_outcome == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            affected_object_ids=missing_step_criteria,
            recommendation=(
                "Add observable completion criteria to every affected "
                "step."
                if criteria_outcome == VerificationOutcome.FAILED
                else None
            ),
        )
        checks.append(criteria_check)

        if criteria_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-step-completion-criteria",
                check=criteria_check,
                title="Step completion criteria are missing",
                description=criteria_observation,
                required_resolution=(
                    "Define observable completion criteria for every "
                    "affected step."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(finding.required_resolution or "")

        # Dependency verification methods
        unverifiable_dependencies = [
            dependency.dependency_id
            for dependency in subject.dependencies
            if not (
                dependency.verification_method
                and dependency.verification_method.strip()
            )
        ]

        if not subject.dependencies:
            dependency_outcome = VerificationOutcome.NOT_APPLICABLE
            dependency_observation = (
                "The plan contains no declared dependencies."
            )
        elif not unverifiable_dependencies:
            dependency_outcome = VerificationOutcome.PASSED
            dependency_observation = (
                "Every declared dependency contains a verification "
                "method."
            )
        else:
            dependency_outcome = VerificationOutcome.FAILED
            dependency_observation = (
                "The following dependencies contain no verification "
                f"method: {unverifiable_dependencies}"
            )

        dependency_check = self._check(
            check_id="check-dependency-verification-methods",
            standard_id="complete-dependencies",
            observation=dependency_observation,
            outcome=dependency_outcome,
            severity=(
                VerificationSeverity.HIGH
                if dependency_outcome == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            affected_object_ids=unverifiable_dependencies,
            recommendation=(
                "Define how every affected dependency will be verified."
                if dependency_outcome == VerificationOutcome.FAILED
                else None
            ),
        )
        checks.append(dependency_check)

        if dependency_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-dependency-verification-methods",
                check=dependency_check,
                title="Dependencies are not verifiable",
                description=dependency_observation,
                required_resolution=(
                    "Add an explicit verification method to every "
                    "affected dependency."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(finding.required_resolution or "")

        # Assumption completeness
        incomplete_assumptions = [
            f"assumption-{index}"
            for index, assumption in enumerate(
                subject.assumptions,
                start=1,
            )
            if not (
                assumption.justification.strip()
                and assumption.risk_if_false.strip()
            )
        ]

        if not subject.assumptions:
            assumption_outcome = VerificationOutcome.NOT_APPLICABLE
            assumption_observation = (
                "The plan contains no declared assumptions."
            )
        elif not incomplete_assumptions:
            assumption_outcome = VerificationOutcome.PASSED
            assumption_observation = (
                "Every declared assumption preserves justification "
                "and risk if false."
            )
        else:
            assumption_outcome = VerificationOutcome.FAILED
            assumption_observation = (
                "The following assumptions lack required explanatory "
                f"information: {incomplete_assumptions}"
            )

        assumption_check = self._check(
            check_id="check-assumption-completeness",
            standard_id="complete-assumptions",
            observation=assumption_observation,
            outcome=assumption_outcome,
            severity=(
                VerificationSeverity.HIGH
                if assumption_outcome == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            affected_object_ids=incomplete_assumptions,
            recommendation=(
                "Preserve justification and risk-if-false for every "
                "affected assumption."
                if assumption_outcome == VerificationOutcome.FAILED
                else None
            ),
        )
        checks.append(assumption_check)

        if assumption_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-assumption-completeness",
                check=assumption_check,
                title="Assumption information is incomplete",
                description=assumption_observation,
                required_resolution=(
                    "Add justification and risk-if-false information "
                    "to every affected assumption."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(finding.required_resolution or "")

        # Risk response coverage
        risks_without_mitigation = [
            risk.risk_id
            for risk in subject.risks
            if not (
                risk.mitigation
                and risk.mitigation.strip()
            )
        ]

        high_risks_without_contingency = [
            risk.risk_id
            for risk in subject.risks
            if (
                risk.impact
                in {
                    RiskLevel.HIGH,
                    RiskLevel.CRITICAL,
                }
                and not (
                    risk.contingency
                    and risk.contingency.strip()
                )
            )
        ]

        incomplete_risks = sorted(
            set(
                risks_without_mitigation
                + high_risks_without_contingency
            )
        )

        if not subject.risks:
            risk_outcome = VerificationOutcome.NOT_APPLICABLE
            risk_observation = (
                "The plan contains no identified risks."
            )
        elif not incomplete_risks:
            risk_outcome = VerificationOutcome.PASSED
            risk_observation = (
                "Every risk contains mitigation and every high-impact "
                "risk contains contingency."
            )
        else:
            risk_outcome = VerificationOutcome.FAILED
            risk_observation = (
                "Risk-response information is incomplete. Risks "
                f"without mitigation: {risks_without_mitigation}; "
                "high-impact risks without contingency: "
                f"{high_risks_without_contingency}."
            )

        risk_check = self._check(
            check_id="check-risk-response-coverage",
            standard_id="complete-risks",
            observation=risk_observation,
            outcome=risk_outcome,
            severity=(
                VerificationSeverity.HIGH
                if risk_outcome == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            affected_object_ids=incomplete_risks,
            recommendation=(
                "Add mitigation to every risk and contingency to every "
                "high- or critical-impact risk."
                if risk_outcome == VerificationOutcome.FAILED
                else None
            ),
        )
        checks.append(risk_check)

        if risk_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-risk-response-coverage",
                check=risk_check,
                title="Risk response information is incomplete",
                description=risk_observation,
                required_resolution=(
                    "Complete mitigation and contingency information "
                    "for every affected risk."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(finding.required_resolution or "")

        # Plan-level success criteria
        has_success_criteria = any(
            criterion.strip()
            for criterion in subject.success_criteria
        )

        if not actionable:
            success_outcome = VerificationOutcome.NOT_APPLICABLE
            success_observation = (
                f"Planning status '{subject.status.value}' does not "
                "require actionable success criteria."
            )
        elif has_success_criteria:
            success_outcome = VerificationOutcome.PASSED
            success_observation = (
                "The plan contains observable plan-level success "
                "criteria."
            )
        else:
            success_outcome = VerificationOutcome.FAILED
            success_observation = (
                "The actionable plan contains no plan-level success "
                "criteria."
            )

        success_check = self._check(
            check_id="check-plan-success-criteria",
            standard_id="complete-success-criteria",
            observation=success_observation,
            outcome=success_outcome,
            severity=(
                VerificationSeverity.HIGH
                if success_outcome == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            recommendation=(
                "Define observable criteria for determining whether "
                "the plan achieved its objective."
                if success_outcome == VerificationOutcome.FAILED
                else None
            ),
        )
        checks.append(success_check)

        if success_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-plan-success-criteria",
                check=success_check,
                title="Plan-level success criteria are missing",
                description=success_observation,
                required_resolution=(
                    "Define observable plan-level success criteria."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(finding.required_resolution or "")

        # Confidence basis
        confidence_basis_present = bool(
            subject.confidence.basis.strip()
        )

        confidence_check = self._check(
            check_id="check-planning-confidence-basis",
            standard_id="complete-confidence-basis",
            observation=(
                "Planning confidence contains an explicit basis."
                if confidence_basis_present
                else (
                    "Planning confidence contains no explanatory basis."
                )
            ),
            outcome=(
                VerificationOutcome.PASSED
                if confidence_basis_present
                else VerificationOutcome.FAILED
            ),
            severity=(
                VerificationSeverity.INFORMATIONAL
                if confidence_basis_present
                else VerificationSeverity.MODERATE
            ),
            recommendation=(
                None
                if confidence_basis_present
                else (
                    "Explain the structured basis for the planning "
                    "confidence assessment."
                )
            ),
        )
        checks.append(confidence_check)

        if not confidence_basis_present:
            finding = self._finding(
                finding_id="finding-planning-confidence-basis",
                check=confidence_check,
                title="Planning confidence basis is missing",
                description=confidence_check.observation,
                required_resolution=(
                    "Record an explicit basis for planning confidence."
                ),
                blocking=False,
            )
            findings.append(finding)
            conditions.append(finding.required_resolution or "")

        # Unresolved information visibility
        unresolved_information = [
            *subject.reasoning_basis.limitations,
            *subject.reasoning_basis.missing_information,
            *[
                assumption.statement
                for assumption in subject.assumptions
                if not assumption.verified
            ],
        ]

        unresolved_information = list(
            dict.fromkeys(
                item.strip()
                for item in unresolved_information
                if item.strip()
            )
        )

        visible_uncertainty = [
            item.strip()
            for item in subject.confidence.uncertainty
            if item.strip()
        ]

        if not unresolved_information:
            unresolved_outcome = VerificationOutcome.NOT_APPLICABLE
            unresolved_observation = (
                "The planning subject records no unresolved information."
            )
        elif visible_uncertainty:
            unresolved_outcome = (
                VerificationOutcome.PASSED_WITH_CONDITIONS
            )
            unresolved_observation = (
                "Unresolved planning information remains visible in "
                "the planning-confidence uncertainty record."
            )
        else:
            unresolved_outcome = VerificationOutcome.FAILED
            unresolved_observation = (
                "The plan contains unresolved information, but planning "
                "confidence exposes no uncertainty."
            )

        unresolved_check = self._check(
            check_id="check-unresolved-information-visibility",
            standard_id="complete-unresolved-information",
            observation=unresolved_observation,
            outcome=unresolved_outcome,
            severity=(
                VerificationSeverity.MODERATE
                if unresolved_outcome == VerificationOutcome.FAILED
                else VerificationSeverity.INFORMATIONAL
            ),
            evidence_references=[
                *unresolved_information,
                *visible_uncertainty,
            ],
            recommendation=(
                "Expose all unresolved reasoning and assumption state "
                "through planning uncertainty."
                if unresolved_outcome == VerificationOutcome.FAILED
                else None
            ),
            uncertainty=unresolved_information,
        )
        checks.append(unresolved_check)

        if unresolved_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-unresolved-information-visibility",
                check=unresolved_check,
                title="Unresolved information is not visible",
                description=unresolved_observation,
                required_resolution=(
                    "Preserve unresolved reasoning information and "
                    "unverified assumptions in planning uncertainty."
                ),
                blocking=False,
            )
            findings.append(finding)
            conditions.append(finding.required_resolution or "")

        return VerificationInspection(
            category=self.CATEGORY,
            standards=standards,
            checks=checks,
            findings=findings,
            conditions=[
                condition
                for condition in dict.fromkeys(conditions)
                if condition
            ],
            inspection_trace=[
                "Inspected required strategy presence.",
                "Inspected required planning-step presence.",
                "Inspected step completion criteria.",
                "Inspected dependency verification methods.",
                "Inspected assumption information.",
                "Inspected risk-response coverage.",
                "Inspected plan-level success criteria.",
                "Inspected planning-confidence basis.",
                "Inspected unresolved-information visibility.",
            ],
            completed=True,
        )
