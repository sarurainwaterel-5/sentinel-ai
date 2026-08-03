"""
Deterministic step decomposition for SentinelAI planning.

The step decomposer converts a selected PlanningStrategy into an ordered,
inspectable sequence of PlanningStep objects without using an LLM.

Sprint 15 begins conservatively:

- steps remain close to the objective, strategy, and reasoning basis,
- every step has an explicit rationale,
- every step has observable completion criteria,
- sequences begin at 1 and remain contiguous,
- no dependencies or risks are invented,
- no actions are executed.

This service does not select a strategy, analyze risks, or produce the
final PlanningResult.
"""

from __future__ import annotations

import re

from app.services.cognition.planning.models import (
    PlanningContext,
    PlanningStep,
    PlanningStepStatus,
    PlanningStrategy,
)


class StepDecomposer:
    """
    Convert one selected strategy into ordered planning steps.

    The decomposer is intentionally deterministic and domain-neutral.
    Domain-specific step libraries may be introduced later without
    changing the PlanningStep contract.
    """

    def __init__(
        self,
        *,
        maximum_steps: int = 8,
        text_limit: int = 420,
    ):
        self.maximum_steps = maximum_steps
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

        cleaned = self._normalize_whitespace(value)

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
    def _planning_is_supported(
        context: PlanningContext,
        strategy: PlanningStrategy | None,
    ) -> bool:
        """
        Confirm that step decomposition has sufficient inputs.

        No strategy or unsupported reasoning produces no steps.
        """

        if strategy is None:
            return False

        reasoning = context.reasoning_result

        if reasoning.status != "complete":
            return False

        if reasoning.conclusion is None:
            return False

        if not context.objective.strip():
            return False

        return True

    @staticmethod
    def _step_id(
        sequence: int,
        label: str,
    ) -> str:
        """
        Build a stable human-readable step identifier.
        """

        normalized_label = re.sub(
            r"[^a-z0-9]+",
            "-",
            label.casefold(),
        ).strip("-")

        return (
            f"step-{sequence}-"
            f"{normalized_label or 'planning-action'}"
        )

    @staticmethod
    def _requires_approval(
        sequence: int,
        total_steps: int,
    ) -> bool:
        """
        Preserve human control over the proposed plan.

        Every Sprint 15 step remains approval-gated. The parameters are
        retained because later policy layers may vary approval by stage.
        """

        del sequence
        del total_steps

        return True

    def _build_step(
        self,
        *,
        sequence: int,
        title: str,
        description: str,
        rationale: str,
        completion_criteria: list[str],
        total_steps: int,
    ) -> PlanningStep:
        """
        Construct one normalized planning step.
        """

        return PlanningStep(
            step_id=self._step_id(
                sequence,
                title,
            ),
            sequence=sequence,
            title=self._bounded_text(title),
            description=self._bounded_text(
                description
            ),
            rationale=self._bounded_text(
                rationale
            ),
            dependency_ids=[],
            risk_ids=[],
            completion_criteria=[
                self._bounded_text(item)
                for item in completion_criteria
                if self._normalize_whitespace(item)
            ],
            requires_human_approval=(
                self._requires_approval(
                    sequence,
                    total_steps,
                )
            ),
            status=(
                PlanningStepStatus.REQUIRES_APPROVAL
            ),
        )

    @staticmethod
    def _objective_statement(
        context: PlanningContext,
    ) -> str:
        """
        Return the normalized planning objective.
        """

        return context.objective.strip()

    @staticmethod
    def _reasoning_statement(
        context: PlanningContext,
    ) -> str:
        """
        Return the supported reasoning conclusion.
        """

        conclusion = context.reasoning_result.conclusion

        if conclusion is None:
            return ""

        return conclusion.statement.strip()

    def _direct_step_specs(
        self,
        context: PlanningContext,
        strategy: PlanningStrategy,
    ) -> list[dict]:
        """
        Create step specifications for a direct sequential strategy.
        """

        objective = self._objective_statement(
            context
        )

        reasoning = self._reasoning_statement(
            context
        )

        return [
            {
                "title": "Confirm planning conditions",
                "description": (
                    "Review the objective, supplied constraints, and "
                    "reasoning basis before beginning the proposed work."
                ),
                "rationale": (
                    "A direct strategy remains reliable only when its "
                    "starting conditions are understood and accepted."
                ),
                "completion_criteria": [
                    "The objective is confirmed.",
                    "Known constraints are recorded.",
                    "The reasoning basis is available for review.",
                ],
            },
            {
                "title": "Prepare the proposed action",
                "description": (
                    f"Prepare the resources, approvals, and conditions "
                    f"needed to advance the objective: {objective}"
                ),
                "rationale": (
                    "Preparation reduces avoidable interruption before "
                    "the central action begins."
                ),
                "completion_criteria": [
                    "Required preparation is documented.",
                    "Human approval is available.",
                    "Known prerequisites have been reviewed.",
                ],
            },
            {
                "title": "Advance the objective",
                "description": (
                    f"Carry out the approved central action represented "
                    f"by the selected strategy: {strategy.name}."
                ),
                "rationale": (
                    f"The supported reasoning indicates: {reasoning}"
                ),
                "completion_criteria": [
                    "The approved action has been performed.",
                    "No unresolved blocking condition remains.",
                ],
            },
            {
                "title": "Verify the outcome",
                "description": (
                    "Compare the resulting state with the objective and "
                    "record whether the intended outcome was achieved."
                ),
                "rationale": (
                    "A plan is incomplete until its outcome can be "
                    "observed and evaluated."
                ),
                "completion_criteria": [
                    "The resulting state has been inspected.",
                    "Success conditions have been evaluated.",
                    "Any deviation has been documented.",
                ],
            },
        ]

    def _phased_step_specs(
        self,
        context: PlanningContext,
        strategy: PlanningStrategy,
    ) -> list[dict]:
        """
        Create step specifications for phased verification-led work.
        """

        objective = self._objective_statement(
            context
        )

        return [
            {
                "title": "Define phase boundaries",
                "description": (
                    "Divide the objective into bounded phases with a "
                    "verification point between each transition."
                ),
                "rationale": (
                    "The selected strategy limits exposure by preventing "
                    "unverified progress across multiple stages."
                ),
                "completion_criteria": [
                    "Each phase has a defined purpose.",
                    "Each transition has a verification condition.",
                ],
            },
            {
                "title": "Validate starting conditions",
                "description": (
                    "Review constraints, assumptions, required approvals, "
                    "and the reasoning basis before the first phase."
                ),
                "rationale": (
                    "Phased execution depends on knowing whether the "
                    "initial planning conditions are acceptable."
                ),
                "completion_criteria": [
                    "Known constraints have been reviewed.",
                    "Supplied assumptions have been identified.",
                    "Human approval is available.",
                ],
            },
            {
                "title": "Perform the first bounded phase",
                "description": (
                    f"Advance one limited portion of the objective using "
                    f"the {strategy.name.casefold()}."
                ),
                "rationale": (
                    "A bounded first phase provides evidence about the "
                    "plan before broader commitment."
                ),
                "completion_criteria": [
                    "The first phase is complete.",
                    "The phase remained within its defined boundary.",
                ],
            },
            {
                "title": "Verify and decide whether to continue",
                "description": (
                    "Evaluate the first phase against its completion "
                    "criteria before authorizing further progress."
                ),
                "rationale": (
                    "Verification prevents the plan from continuing when "
                    "reality differs from the expected conditions."
                ),
                "completion_criteria": [
                    "Phase results have been reviewed.",
                    "Continuation is explicitly approved or deferred.",
                ],
            },
            {
                "title": "Complete remaining approved phases",
                "description": (
                    f"Continue through the remaining bounded phases until "
                    f"the objective is reached: {objective}"
                ),
                "rationale": (
                    "Progress remains controlled through repeated "
                    "verification rather than one irreversible transition."
                ),
                "completion_criteria": [
                    "All approved phases are complete.",
                    "Every phase transition was verified.",
                ],
            },
            {
                "title": "Validate the final state",
                "description": (
                    "Compare the completed work with the objective and "
                    "record whether the intended outcome was achieved."
                ),
                "rationale": (
                    "Final validation establishes whether the complete "
                    "plan succeeded."
                ),
                "completion_criteria": [
                    "The final state has been inspected.",
                    "Success criteria have been evaluated.",
                    "Remaining deviations are documented.",
                ],
            },
        ]

    def _clarification_step_specs(
        self,
        context: PlanningContext,
        strategy: PlanningStrategy,
    ) -> list[dict]:
        """
        Create step specifications for clarification-first planning.
        """

        del strategy

        uncertainty = []

        conclusion = context.reasoning_result.conclusion

        if conclusion is not None:
            uncertainty = [
                *conclusion.limitations,
                *conclusion.missing_information,
                *conclusion.confidence.uncertainty,
            ]

        uncertainty_description = (
            "; ".join(
                dict.fromkeys(
                    item.strip()
                    for item in uncertainty
                    if item.strip()
                )
            )
            or "Important planning unknowns remain unresolved."
        )

        return [
            {
                "title": "Identify blocking unknowns",
                "description": (
                    "Record the assumptions, missing information, and "
                    "uncertainties that could materially change the plan."
                ),
                "rationale": (
                    "Detailed implementation should not proceed while "
                    "high-impact unknowns remain hidden."
                ),
                "completion_criteria": [
                    "Blocking unknowns have been listed.",
                    "Each unknown has an accountable verification method.",
                ],
            },
            {
                "title": "Resolve the highest-impact uncertainty",
                "description": (
                    "Collect or verify the information required to address "
                    f"the most important uncertainty: "
                    f"{uncertainty_description}"
                ),
                "rationale": (
                    "Resolving the highest-impact unknown first provides "
                    "the greatest improvement in planning quality."
                ),
                "completion_criteria": [
                    "The highest-impact uncertainty is verified or "
                    "explicitly accepted.",
                    "The reasoning basis is updated when necessary.",
                ],
            },
            {
                "title": "Reassess strategy suitability",
                "description": (
                    "Reevaluate whether the current strategy remains the "
                    "strongest option after clarification."
                ),
                "rationale": (
                    "New information may alter the safest or most "
                    "effective course of action."
                ),
                "completion_criteria": [
                    "Strategy suitability has been reevaluated.",
                    "The selected strategy is confirmed or replaced.",
                ],
            },
            {
                "title": "Authorize detailed planning",
                "description": (
                    "Proceed to detailed step decomposition only after the "
                    "remaining uncertainty is acceptable."
                ),
                "rationale": (
                    "Clarification-first planning exists to prevent false "
                    "precision when the planning basis is incomplete."
                ),
                "completion_criteria": [
                    "Remaining uncertainty is visible.",
                    "Human approval to continue has been recorded.",
                ],
            },
        ]

    def _step_specs(
        self,
        context: PlanningContext,
        strategy: PlanningStrategy,
    ) -> list[dict]:
        """
        Select the deterministic decomposition pattern for the strategy.
        """

        strategy_name = strategy.name.casefold()

        if "clarification" in strategy_name:
            return self._clarification_step_specs(
                context,
                strategy,
            )

        if (
            "phased" in strategy_name
            or "verification-led" in strategy_name
        ):
            return self._phased_step_specs(
                context,
                strategy,
            )

        return self._direct_step_specs(
            context,
            strategy,
        )

    def decompose(
        self,
        *,
        context: PlanningContext,
        strategy: PlanningStrategy | None,
    ) -> list[PlanningStep]:
        """
        Produce ordered steps for one selected strategy.

        Unsupported reasoning or a missing strategy returns an empty list
        rather than fabricating a course of action.
        """

        if not self._planning_is_supported(
            context,
            strategy,
        ):
            return []

        assert strategy is not None

        specifications = self._step_specs(
            context,
            strategy,
        )[
            : self.maximum_steps
        ]

        total_steps = len(specifications)

        return [
            self._build_step(
                sequence=index,
                title=specification["title"],
                description=(
                    specification["description"]
                ),
                rationale=(
                    specification["rationale"]
                ),
                completion_criteria=(
                    specification[
                        "completion_criteria"
                    ]
                ),
                total_steps=total_steps,
            )
            for index, specification in enumerate(
                specifications,
                start=1,
            )
        ]
