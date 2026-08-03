"""
Deterministic risk analysis for SentinelAI planning.

The risk analyzer inspects a PlanningContext, selected strategy, and
proposed steps to identify:

- dependencies,
- assumptions,
- risks,
- unresolved planning conditions,
- mitigations,
- contingencies.

Sprint 15 begins conservatively:

- explicit constraints become visible prerequisites,
- supplied assumptions remain explicit and unverified,
- reasoning limitations remain visible as planning exposure,
- dependencies and risks reference real planning-step identifiers,
- duplicate observations are removed deterministically,
- no planning-confidence score is calculated,
- no actions are executed.

This service does not select strategies, generate steps, calculate final
planning confidence, or produce the final PlanningResult.
"""

from __future__ import annotations

import re
from typing import Iterable

from app.services.cognition.planning.models import (
    PlanningAssumption,
    PlanningContext,
    PlanningDependency,
    PlanningRisk,
    PlanningRiskAnalysis,
    PlanningStep,
    PlanningStrategy,
    RiskLevel,
)


class RiskAnalyzer:
    """
    Produce an inspectable structural risk analysis for a proposed plan.

    The analyzer is intentionally deterministic and domain-neutral.
    Domain-specific risk policies may be introduced later without changing
    the PlanningRiskAnalysis contract.
    """

    def __init__(
        self,
        *,
        maximum_dependencies: int = 12,
        maximum_assumptions: int = 12,
        maximum_risks: int = 16,
        text_limit: int = 420,
    ):
        self.maximum_dependencies = maximum_dependencies
        self.maximum_assumptions = maximum_assumptions
        self.maximum_risks = maximum_risks
        self.text_limit = text_limit

    @staticmethod
    def _normalize_whitespace(
        value: str,
    ) -> str:
        """
        Collapse repeated whitespace without changing meaning.
        """

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    def _bounded_text(
        self,
        value: str,
    ) -> str:
        """
        Return bounded text without introducing new factual claims.
        """

        cleaned = self._normalize_whitespace(
            str(value)
        )

        if len(cleaned) <= self.text_limit:
            return cleaned

        shortened = cleaned[
            : self.text_limit
        ].rsplit(
            " ",
            1,
        )[0]

        return f"{shortened}…"

    @staticmethod
    def _slug(
        value: str,
    ) -> str:
        """
        Convert text into a stable identifier fragment.
        """

        normalized = re.sub(
            r"[^a-z0-9]+",
            "-",
            value.casefold(),
        ).strip("-")

        return normalized or "condition"

    @classmethod
    def _identifier(
        cls,
        *,
        prefix: str,
        index: int,
        value: str,
    ) -> str:
        """
        Build a stable, human-readable planning identifier.
        """

        return (
            f"{prefix}-{index}-"
            f"{cls._slug(value)[:48]}"
        )

    @staticmethod
    def _unique_text(
        values: Iterable[str],
    ) -> list[str]:
        """
        Deduplicate text case-insensitively while preserving order.
        """

        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            cleaned = str(value).strip()

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            result.append(cleaned)

        return result

    @staticmethod
    def _step_ids(
        steps: list[PlanningStep],
    ) -> list[str]:
        """
        Return planning-step identifiers in sequence order.
        """

        ordered = sorted(
            steps,
            key=lambda step: step.sequence,
        )

        return [
            step.step_id
            for step in ordered
        ]

    @staticmethod
    def _implementation_step_ids(
        steps: list[PlanningStep],
    ) -> list[str]:
        """
        Return steps most likely to advance or change the target state.

        Verification and clarification steps remain excluded when more
        action-oriented steps are available.
        """

        action_ids = [
            step.step_id
            for step in steps
            if not any(
                token in step.title.casefold()
                for token in (
                    "confirm",
                    "validate",
                    "verify",
                    "identify",
                    "reassess",
                    "authorize",
                )
            )
        ]

        if action_ids:
            return action_ids

        return RiskAnalyzer._step_ids(
            steps
        )

    @staticmethod
    def _final_step_ids(
        steps: list[PlanningStep],
    ) -> list[str]:
        """
        Return the final proposed step when one exists.
        """

        if not steps:
            return []

        final_step = max(
            steps,
            key=lambda step: step.sequence,
        )

        return [
            final_step.step_id,
        ]

    @staticmethod
    def _reasoning_uncertainty(
        context: PlanningContext,
    ) -> list[str]:
        """
        Preserve uncertainty from the authoritative reasoning result.
        """

        conclusion = (
            context.reasoning_result.conclusion
        )

        if conclusion is None:
            return []

        return RiskAnalyzer._unique_text(
            [
                *conclusion.limitations,
                *conclusion.missing_information,
                *conclusion.confidence.uncertainty,
            ]
        )

    def _build_dependencies(
        self,
        *,
        context: PlanningContext,
        steps: list[PlanningStep],
    ) -> list[PlanningDependency]:
        """
        Convert explicit planning constraints into visible prerequisites.

        A constraint is not assumed to be satisfied. It becomes a condition
        that should be verified before implementation-oriented steps.
        """

        affected_steps = (
            self._implementation_step_ids(
                steps
            )
        )

        dependencies: list[
            PlanningDependency
        ] = []

        for index, constraint in enumerate(
            self._unique_text(
                context.constraints
            ),
            start=1,
        ):
            dependencies.append(
                PlanningDependency(
                    dependency_id=self._identifier(
                        prefix="dependency",
                        index=index,
                        value=constraint,
                    ),
                    description=self._bounded_text(
                        (
                            "Verify that the following planning "
                            f"constraint can be satisfied: {constraint}"
                        )
                    ),
                    required_before_step_ids=(
                        affected_steps
                    ),
                    verification_method=(
                        "Review the constraint with the accountable "
                        "human owner and record whether it is satisfied."
                    ),
                    satisfied=False,
                )
            )

        return dependencies[
            : self.maximum_dependencies
        ]

    def _build_assumptions(
        self,
        *,
        context: PlanningContext,
    ) -> list[PlanningAssumption]:
        """
        Preserve user-supplied assumptions as explicit planning objects.
        """

        assumptions: list[
            PlanningAssumption
        ] = []

        for assumption in self._unique_text(
            context.supplied_assumptions
        ):
            assumptions.append(
                PlanningAssumption(
                    statement=self._bounded_text(
                        assumption
                    ),
                    justification=(
                        "This condition was supplied to the planner "
                        "but was not independently verified by the "
                        "planning subsystem."
                    ),
                    source="planning_request",
                    verified=False,
                    risk_if_false=self._bounded_text(
                        (
                            "If this assumption is false, the selected "
                            "strategy or one or more proposed steps may "
                            "become invalid, unsafe, or incomplete."
                        )
                    ),
                )
            )

        return assumptions[
            : self.maximum_assumptions
        ]

    def _reasoning_risks(
        self,
        *,
        context: PlanningContext,
        steps: list[PlanningStep],
        starting_index: int,
    ) -> list[PlanningRisk]:
        """
        Convert reasoning uncertainty into explicit planning risks.
        """

        affected_steps = (
            self._implementation_step_ids(
                steps
            )
        )

        risks: list[PlanningRisk] = []

        for offset, uncertainty in enumerate(
            self._reasoning_uncertainty(
                context
            ),
            start=starting_index,
        ):
            risks.append(
                PlanningRisk(
                    risk_id=self._identifier(
                        prefix="risk",
                        index=offset,
                        value=uncertainty,
                    ),
                    description=self._bounded_text(
                        uncertainty
                    ),
                    likelihood=RiskLevel.MODERATE,
                    impact=RiskLevel.HIGH,
                    affected_step_ids=(
                        affected_steps
                    ),
                    mitigation=(
                        "Resolve or explicitly accept this uncertainty "
                        "before authorizing affected steps."
                    ),
                    contingency=(
                        "Pause the plan and return to reasoning or "
                        "clarification if the uncertainty materially "
                        "changes the planning basis."
                    ),
                )
            )

        return risks

    def _assumption_risks(
        self,
        *,
        assumptions: list[PlanningAssumption],
        steps: list[PlanningStep],
        starting_index: int,
    ) -> list[PlanningRisk]:
        """
        Create risks for unverified assumptions.
        """

        affected_steps = (
            self._implementation_step_ids(
                steps
            )
        )

        risks: list[PlanningRisk] = []

        for offset, assumption in enumerate(
            assumptions,
            start=starting_index,
        ):
            description = (
                "The plan depends on an unverified "
                f"assumption: {assumption.statement}"
            )

            risks.append(
                PlanningRisk(
                    risk_id=self._identifier(
                        prefix="risk",
                        index=offset,
                        value=assumption.statement,
                    ),
                    description=self._bounded_text(
                        description
                    ),
                    likelihood=RiskLevel.MODERATE,
                    impact=RiskLevel.HIGH,
                    affected_step_ids=(
                        affected_steps
                    ),
                    mitigation=(
                        "Verify the assumption before authorizing "
                        "affected steps."
                    ),
                    contingency=(
                        "Revise the strategy and affected steps if the "
                        "assumption proves false."
                    ),
                )
            )

        return risks

    def _constraint_risks(
        self,
        *,
        context: PlanningContext,
        steps: list[PlanningStep],
        starting_index: int,
    ) -> list[PlanningRisk]:
        """
        Represent the risk that explicit constraints cannot be satisfied.
        """

        affected_steps = (
            self._implementation_step_ids(
                steps
            )
        )

        risks: list[PlanningRisk] = []

        for offset, constraint in enumerate(
            self._unique_text(
                context.constraints
            ),
            start=starting_index,
        ):
            risks.append(
                PlanningRisk(
                    risk_id=self._identifier(
                        prefix="risk",
                        index=offset,
                        value=constraint,
                    ),
                    description=self._bounded_text(
                        (
                            "The plan may fail or require revision if "
                            "this constraint cannot be satisfied: "
                            f"{constraint}"
                        )
                    ),
                    likelihood=RiskLevel.MODERATE,
                    impact=RiskLevel.HIGH,
                    affected_step_ids=(
                        affected_steps
                    ),
                    mitigation=(
                        "Verify the constraint before authorizing "
                        "implementation-oriented steps."
                    ),
                    contingency=(
                        "Select an alternative strategy or revise the "
                        "plan if the constraint cannot be honored."
                    ),
                )
            )

        return risks

    def _structural_risks(
        self,
        *,
        strategy: PlanningStrategy,
        steps: list[PlanningStep],
        starting_index: int,
    ) -> list[PlanningRisk]:
        """
        Identify bounded risks implied by the plan structure itself.
        """

        risks: list[PlanningRisk] = []
        next_index = starting_index

        if not steps:
            risks.append(
                PlanningRisk(
                    risk_id=self._identifier(
                        prefix="risk",
                        index=next_index,
                        value="no proposed steps",
                    ),
                    description=(
                        "The selected strategy has no proposed steps."
                    ),
                    likelihood=RiskLevel.HIGH,
                    impact=RiskLevel.CRITICAL,
                    affected_step_ids=[],
                    mitigation=(
                        "Decompose the selected strategy into ordered, "
                        "inspectable steps before approval."
                    ),
                    contingency=(
                        "Block planning completion until valid steps "
                        "exist."
                    ),
                )
            )
            return risks

        if any(
            not step.completion_criteria
            for step in steps
        ):
            affected = [
                step.step_id
                for step in steps
                if not step.completion_criteria
            ]

            risks.append(
                PlanningRisk(
                    risk_id=self._identifier(
                        prefix="risk",
                        index=next_index,
                        value="missing completion criteria",
                    ),
                    description=(
                        "One or more proposed steps lack observable "
                        "completion criteria."
                    ),
                    likelihood=RiskLevel.MODERATE,
                    impact=RiskLevel.HIGH,
                    affected_step_ids=affected,
                    mitigation=(
                        "Define measurable completion criteria for "
                        "every affected step."
                    ),
                    contingency=(
                        "Do not approve affected steps until completion "
                        "can be verified."
                    ),
                )
            )

            next_index += 1

        if not all(
            step.requires_human_approval
            for step in steps
        ):
            affected = [
                step.step_id
                for step in steps
                if not step.requires_human_approval
            ]

            risks.append(
                PlanningRisk(
                    risk_id=self._identifier(
                        prefix="risk",
                        index=next_index,
                        value="missing human approval",
                    ),
                    description=(
                        "One or more Sprint 15 steps are not explicitly "
                        "gated by human approval."
                    ),
                    likelihood=RiskLevel.MODERATE,
                    impact=RiskLevel.CRITICAL,
                    affected_step_ids=affected,
                    mitigation=(
                        "Require explicit human approval before any "
                        "proposed step can advance toward execution."
                    ),
                    contingency=(
                        "Block the plan if approval governance cannot "
                        "be established."
                    ),
                )
            )

            next_index += 1

        if (
            "clarification" not in strategy.name.casefold()
            and len(steps) == 1
        ):
            risks.append(
                PlanningRisk(
                    risk_id=self._identifier(
                        prefix="risk",
                        index=next_index,
                        value="single step plan",
                    ),
                    description=(
                        "The strategy has been reduced to one broad "
                        "step and may not be sufficiently decomposed."
                    ),
                    likelihood=RiskLevel.MODERATE,
                    impact=RiskLevel.MODERATE,
                    affected_step_ids=self._step_ids(
                        steps
                    ),
                    mitigation=(
                        "Decompose the strategy into preparation, "
                        "action, and verification stages."
                    ),
                    contingency=(
                        "Return the plan to step decomposition before "
                        "approval."
                    ),
                )
            )

        return risks

    @classmethod
    def _deduplicate_risks(
        cls,
        risks: list[PlanningRisk],
    ) -> list[PlanningRisk]:
        """
        Remove semantically duplicate risks while preserving order.
        """

        deduplicated: list[PlanningRisk] = []
        seen: set[str] = set()

        for risk in risks:
            identity = (
                cls._normalize_whitespace(
                    risk.description
                ).casefold()
            )

            if identity in seen:
                continue

            seen.add(identity)
            deduplicated.append(risk)

        return deduplicated

    def _unresolved_conditions(
        self,
        *,
        dependencies: list[PlanningDependency],
        assumptions: list[PlanningAssumption],
        reasoning_uncertainty: list[str],
        risks: list[PlanningRisk],
    ) -> list[str]:
        """
        Build a concise list of conditions still requiring resolution.
        """

        conditions = [
            dependency.description
            for dependency in dependencies
            if not dependency.satisfied
        ]

        conditions.extend(
            (
                "Verify the planning assumption: "
                f"{assumption.statement}"
            )
            for assumption in assumptions
            if not assumption.verified
        )

        conditions.extend(
            reasoning_uncertainty
        )

        conditions.extend(
            risk.description
            for risk in risks
            if risk.impact in {
                RiskLevel.HIGH,
                RiskLevel.CRITICAL,
            }
        )

        return self._unique_text(
            conditions
        )

    def analyze(
        self,
        *,
        context: PlanningContext,
        strategy: PlanningStrategy,
        steps: list[PlanningStep],
    ) -> PlanningRiskAnalysis:
        """
        Produce deterministic risk analysis for one proposed plan.

        The result identifies planning exposure but deliberately does not
        calculate planning confidence.
        """

        trace = [
            "Inspected explicit planning constraints.",
        ]

        dependencies = self._build_dependencies(
            context=context,
            steps=steps,
        )

        trace.append(
            "Converted planning constraints into visible prerequisites."
        )

        assumptions = self._build_assumptions(
            context=context,
        )

        trace.append(
            "Preserved supplied assumptions as unverified conditions."
        )

        risks: list[PlanningRisk] = []

        risks.extend(
            self._reasoning_risks(
                context=context,
                steps=steps,
                starting_index=1,
            )
        )

        next_index = len(risks) + 1

        risks.extend(
            self._assumption_risks(
                assumptions=assumptions,
                steps=steps,
                starting_index=next_index,
            )
        )

        next_index = len(risks) + 1

        risks.extend(
            self._constraint_risks(
                context=context,
                steps=steps,
                starting_index=next_index,
            )
        )

        next_index = len(risks) + 1

        risks.extend(
            self._structural_risks(
                strategy=strategy,
                steps=steps,
                starting_index=next_index,
            )
        )

        risks = self._deduplicate_risks(
            risks
        )[
            : self.maximum_risks
        ]

        trace.append(
            "Identified reasoning, assumption, constraint, and "
            "structural planning risks."
        )

        reasoning_uncertainty = (
            self._reasoning_uncertainty(
                context
            )
        )

        unresolved_conditions = (
            self._unresolved_conditions(
                dependencies=dependencies,
                assumptions=assumptions,
                reasoning_uncertainty=(
                    reasoning_uncertainty
                ),
                risks=risks,
            )
        )

        trace.append(
            "Collected unresolved conditions requiring verification "
            "or explicit acceptance."
        )

        return PlanningRiskAnalysis(
            dependencies=dependencies,
            assumptions=assumptions,
            risks=risks,
            unresolved_conditions=(
                unresolved_conditions
            ),
            analysis_trace=trace,
        )
