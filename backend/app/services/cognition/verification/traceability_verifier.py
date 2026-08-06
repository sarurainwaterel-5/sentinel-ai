"""
Deterministic traceability verification for planning results.

This specialist verifies that the proposed plan remains connected to the
authoritative reasoning basis that preceded it.

It examines:

- availability of a supported reasoning conclusion,
- explicit strategy support from reasoning,
- connection between recorded strategy support and the conclusion,
- explanatory rationale for every proposed step,
- preservation of reasoning uncertainty in planning confidence.

It does not:

- rerun reasoning,
- rewrite strategy or steps,
- inspect planning-graph integrity,
- evaluate general completeness,
- evaluate constraint compliance,
- calculate verification confidence,
- determine final verification status.
"""

from __future__ import annotations

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


class TraceabilityVerifier:
    """
    Verify the path from reasoning basis to strategy to planning steps.
    """

    CATEGORY = VerificationCategory.TRACEABILITY

    @staticmethod
    def _normalize(value: str | None) -> str:
        """
        Normalize text for deterministic comparison.
        """

        if value is None:
            return ""

        return " ".join(
            value.casefold().split()
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
            category=VerificationCategory.TRACEABILITY,
            title=title,
            description=description,
            required=True,
            source=(
                "SentinelAI Cognitive Planning traceability contract"
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
        evidence_references: list[str] | None = None,
        affected_object_ids: list[str] | None = None,
        recommendation: str | None = None,
        uncertainty: list[str] | None = None,
    ) -> VerificationCheck:
        return VerificationCheck(
            check_id=check_id,
            category=VerificationCategory.TRACEABILITY,
            standard_id=standard_id,
            observation=observation,
            outcome=outcome,
            severity=severity,
            evidence_references=(
                evidence_references or []
            ),
            affected_object_ids=(
                affected_object_ids or []
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
            category=VerificationCategory.TRACEABILITY,
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
    def _support_matches_conclusion(
        cls,
        *,
        conclusion: str,
        support_statements: list[str],
    ) -> bool:
        """
        Determine whether strategy support visibly references the
        authoritative reasoning conclusion.

        Sprint 16 uses deterministic normalized text comparison rather
        than semantic inference.
        """

        normalized_conclusion = cls._normalize(
            conclusion
        )

        if not normalized_conclusion:
            return False

        for statement in support_statements:
            normalized_statement = cls._normalize(
                statement
            )

            if not normalized_statement:
                continue

            if (
                normalized_statement
                == normalized_conclusion
            ):
                return True

            if (
                normalized_conclusion
                in normalized_statement
                or normalized_statement
                in normalized_conclusion
            ):
                return True

        return False

    def inspect(
        self,
        *,
        context: VerificationContext,
    ) -> VerificationInspection:
        """
        Inspect one PlanningResult for reasoning-to-plan traceability.
        """

        subject = context.subject
        reasoning_basis = subject.reasoning_basis
        strategy = subject.strategy

        standards = [
            self._standard(
                standard_id="trace-reasoning-basis",
                title="Supported reasoning basis exists",
                description=(
                    "A plan must preserve the authoritative reasoning "
                    "conclusion that justified planning."
                ),
            ),
            self._standard(
                standard_id="trace-strategy-support",
                title="Strategy records reasoning support",
                description=(
                    "The selected strategy must explicitly record the "
                    "reasoning that supports it."
                ),
            ),
            self._standard(
                standard_id="trace-conclusion-connection",
                title="Strategy support connects to conclusion",
                description=(
                    "At least one strategy-support statement must "
                    "visibly correspond to the authoritative reasoning "
                    "conclusion."
                ),
            ),
            self._standard(
                standard_id="trace-step-rationale",
                title="Every step contains rationale",
                description=(
                    "Every proposed step must explain why it exists "
                    "and how it advances the selected strategy."
                ),
            ),
            self._standard(
                standard_id="trace-uncertainty-preservation",
                title="Reasoning uncertainty remains visible",
                description=(
                    "When reasoning contains limitations or missing "
                    "information, planning confidence must preserve "
                    "visible uncertainty."
                ),
            ),
        ]

        checks: list[VerificationCheck] = []
        findings: list[VerificationFinding] = []
        conditions: list[str] = []

        conclusion = reasoning_basis.conclusion

        reasoning_available = bool(
            conclusion
            and conclusion.strip()
            and reasoning_basis.reasoning_status
            == "complete"
        )

        reasoning_check = self._check(
            check_id="check-reasoning-basis",
            standard_id="trace-reasoning-basis",
            observation=(
                "A completed authoritative reasoning conclusion "
                "is available to support planning."
                if reasoning_available
                else (
                    "The planning subject does not contain a completed "
                    "authoritative reasoning conclusion."
                )
            ),
            outcome=(
                VerificationOutcome.PASSED
                if reasoning_available
                else VerificationOutcome.NOT_VERIFIABLE
            ),
            severity=(
                VerificationSeverity.INFORMATIONAL
                if reasoning_available
                else VerificationSeverity.CRITICAL
            ),
            evidence_references=(
                [conclusion]
                if conclusion
                else []
            ),
            recommendation=(
                None
                if reasoning_available
                else (
                    "Produce a supported reasoning conclusion before "
                    "attempting to verify planning traceability."
                )
            ),
            uncertainty=(
                []
                if reasoning_available
                else [
                    "The source reasoning conclusion is unavailable."
                ]
            ),
        )

        checks.append(reasoning_check)

        if not reasoning_available:
            finding = self._finding(
                finding_id="finding-reasoning-basis",
                check=reasoning_check,
                title="Reasoning basis unavailable",
                description=(
                    "The plan cannot be traced to an authoritative "
                    "completed reasoning conclusion."
                ),
                required_resolution=(
                    "Rerun evidence-grounded reasoning and regenerate "
                    "the planning result from a supported conclusion."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        strategy_support = (
            strategy.supported_by_reasoning
            if strategy is not None
            else []
        )

        strategy_supported = bool(
            strategy is not None
            and strategy_support
            and any(
                statement.strip()
                for statement in strategy_support
            )
        )

        strategy_check = self._check(
            check_id="check-strategy-reasoning-support",
            standard_id="trace-strategy-support",
            observation=(
                f"The selected strategy records "
                f"{len(strategy_support)} reasoning-support "
                "statement(s)."
                if strategy_supported
                else (
                    "The selected strategy does not record explicit "
                    "reasoning support."
                )
            ),
            outcome=(
                VerificationOutcome.PASSED
                if strategy_supported
                else VerificationOutcome.FAILED
            ),
            severity=(
                VerificationSeverity.INFORMATIONAL
                if strategy_supported
                else VerificationSeverity.HIGH
            ),
            evidence_references=strategy_support,
            affected_object_ids=(
                [strategy.name]
                if strategy is not None
                else []
            ),
            recommendation=(
                None
                if strategy_supported
                else (
                    "Record the authoritative reasoning statements "
                    "that support the selected strategy."
                )
            ),
        )

        checks.append(strategy_check)

        if not strategy_supported:
            finding = self._finding(
                finding_id="finding-strategy-reasoning-support",
                check=strategy_check,
                title="Strategy lacks reasoning support",
                description=(
                    "The selected strategy cannot be traced backward "
                    "to explicit reasoning support."
                ),
                required_resolution=(
                    "Populate strategy.supported_by_reasoning using "
                    "the authoritative reasoning basis."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        conclusion_connection = bool(
            reasoning_available
            and strategy_supported
            and conclusion is not None
            and self._support_matches_conclusion(
                conclusion=conclusion,
                support_statements=strategy_support,
            )
        )

        if not reasoning_available:
            connection_outcome = (
                VerificationOutcome.NOT_VERIFIABLE
            )
            connection_observation = (
                "The strategy-to-conclusion connection cannot be "
                "verified because the reasoning conclusion is absent."
            )
        elif not strategy_supported:
            connection_outcome = VerificationOutcome.FAILED
            connection_observation = (
                "The strategy-to-conclusion connection is broken "
                "because no explicit strategy support is recorded."
            )
        elif conclusion_connection:
            connection_outcome = VerificationOutcome.PASSED
            connection_observation = (
                "At least one strategy-support statement corresponds "
                "to the authoritative reasoning conclusion."
            )
        else:
            connection_outcome = VerificationOutcome.FAILED
            connection_observation = (
                "The recorded strategy-support statements do not "
                "visibly correspond to the authoritative reasoning "
                "conclusion."
            )

        connection_check = self._check(
            check_id="check-strategy-conclusion-connection",
            standard_id="trace-conclusion-connection",
            observation=connection_observation,
            outcome=connection_outcome,
            severity=(
                VerificationSeverity.INFORMATIONAL
                if conclusion_connection
                else VerificationSeverity.HIGH
            ),
            evidence_references=[
                *(
                    [conclusion]
                    if conclusion
                    else []
                ),
                *strategy_support,
            ],
            affected_object_ids=(
                [strategy.name]
                if strategy is not None
                else []
            ),
            recommendation=(
                None
                if conclusion_connection
                else (
                    "Connect the strategy explicitly to the "
                    "authoritative reasoning conclusion."
                )
            ),
        )

        checks.append(connection_check)

        if (
            connection_outcome
            != VerificationOutcome.PASSED
        ):
            finding = self._finding(
                finding_id="finding-strategy-conclusion-connection",
                check=connection_check,
                title="Strategy-to-conclusion trace is broken",
                description=connection_observation,
                required_resolution=(
                    "Regenerate or revise the strategy-support record "
                    "so it visibly references the authoritative "
                    "reasoning conclusion."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        steps_without_rationale = [
            step.step_id
            for step in subject.steps
            if not step.rationale.strip()
        ]

        step_rationales_present = (
            bool(subject.steps)
            and not steps_without_rationale
        )

        if not subject.steps:
            step_outcome = VerificationOutcome.NOT_APPLICABLE
            step_observation = (
                "The planning subject contains no proposed steps to "
                "trace through strategy rationale."
            )
        elif step_rationales_present:
            step_outcome = VerificationOutcome.PASSED
            step_observation = (
                "Every proposed planning step contains an explicit "
                "rationale."
            )
        else:
            step_outcome = VerificationOutcome.FAILED
            step_observation = (
                "The following steps do not contain traceable "
                f"rationale: {steps_without_rationale}"
            )

        step_check = self._check(
            check_id="check-step-rationale-traceability",
            standard_id="trace-step-rationale",
            observation=step_observation,
            outcome=step_outcome,
            severity=(
                VerificationSeverity.INFORMATIONAL
                if step_outcome
                in {
                    VerificationOutcome.PASSED,
                    VerificationOutcome.NOT_APPLICABLE,
                }
                else VerificationSeverity.HIGH
            ),
            affected_object_ids=steps_without_rationale,
            evidence_references=[
                f"{step.step_id}: {step.rationale}"
                for step in subject.steps
                if step.rationale.strip()
            ],
            recommendation=(
                None
                if step_outcome
                in {
                    VerificationOutcome.PASSED,
                    VerificationOutcome.NOT_APPLICABLE,
                }
                else (
                    "Add an explicit rationale to every planning step."
                )
            ),
        )

        checks.append(step_check)

        if step_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-step-rationale-traceability",
                check=step_check,
                title="Planning steps lack traceable rationale",
                description=step_observation,
                required_resolution=(
                    "Explain why every affected step exists and how "
                    "it advances the selected strategy."
                ),
                blocking=True,
            )
            findings.append(finding)
            conditions.append(
                finding.required_resolution
                or finding.description
            )

        inherited_uncertainty = [
            *reasoning_basis.limitations,
            *reasoning_basis.missing_information,
        ]

        inherited_uncertainty = list(
            dict.fromkeys(
                statement.strip()
                for statement in inherited_uncertainty
                if statement.strip()
            )
        )

        planning_uncertainty = [
            statement.strip()
            for statement in subject.confidence.uncertainty
            if statement.strip()
        ]

        if not inherited_uncertainty:
            uncertainty_outcome = (
                VerificationOutcome.NOT_APPLICABLE
            )
            uncertainty_observation = (
                "The reasoning basis records no limitations or missing "
                "information requiring preservation."
            )
        elif planning_uncertainty:
            uncertainty_outcome = VerificationOutcome.PASSED
            uncertainty_observation = (
                "Reasoning uncertainty remains visible in the "
                "planning-confidence assessment."
            )
        else:
            uncertainty_outcome = VerificationOutcome.FAILED
            uncertainty_observation = (
                "The reasoning basis records limitations or missing "
                "information, but planning confidence exposes no "
                "uncertainty."
            )

        uncertainty_check = self._check(
            check_id="check-reasoning-uncertainty-preservation",
            standard_id="trace-uncertainty-preservation",
            observation=uncertainty_observation,
            outcome=uncertainty_outcome,
            severity=(
                VerificationSeverity.INFORMATIONAL
                if uncertainty_outcome
                in {
                    VerificationOutcome.PASSED,
                    VerificationOutcome.NOT_APPLICABLE,
                }
                else VerificationSeverity.MODERATE
            ),
            evidence_references=[
                *inherited_uncertainty,
                *planning_uncertainty,
            ],
            recommendation=(
                None
                if uncertainty_outcome
                in {
                    VerificationOutcome.PASSED,
                    VerificationOutcome.NOT_APPLICABLE,
                }
                else (
                    "Preserve inherited reasoning limitations and "
                    "missing information in planning uncertainty."
                )
            ),
            uncertainty=inherited_uncertainty,
        )

        checks.append(uncertainty_check)

        if uncertainty_outcome == VerificationOutcome.FAILED:
            finding = self._finding(
                finding_id="finding-reasoning-uncertainty-preservation",
                check=uncertainty_check,
                title="Reasoning uncertainty was not preserved",
                description=uncertainty_observation,
                required_resolution=(
                    "Expose inherited reasoning limitations and "
                    "missing information in the planning-confidence "
                    "uncertainty record."
                ),
                blocking=False,
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
                "Inspected the authoritative reasoning basis.",
                "Inspected strategy reasoning support.",
                "Inspected the strategy-to-conclusion connection.",
                "Inspected planning-step rationales.",
                "Inspected preservation of reasoning uncertainty.",
            ],
            completed=True,
        )
