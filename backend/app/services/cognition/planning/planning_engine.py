"""
SentinelAI Evidence-Aware Planning Engine.

The planning engine coordinates Sentinel's planning pipeline.

It does not retrieve evidence.
It does not perform reasoning.
It does not call an LLM.
It does not execute actions.

Instead it orchestrates:

Strategy Selection

↓

Step Decomposition

↓

Risk Analysis

↓

Planning Confidence

↓

Structured Plan
"""

from __future__ import annotations

from app.services.cognition.planning.models import (
    PlanningComplexity,
    PlanningConfidence,
    PlanningConfidenceLevel,
    PlanningContext,
    PlanningObjective,
    PlanningReasoningBasis,
    PlanningResult,
    PlanningStatus,
)
from app.services.cognition.planning.planning_confidence_engine import (
    PlanningConfidenceEngine,
)
from app.services.cognition.planning.risk_analyzer import (
    RiskAnalyzer,
)
from app.services.cognition.planning.step_decomposer import (
    StepDecomposer,
)
from app.services.cognition.planning.strategy_engine import (
    StrategyEngine,
)


class PlanningEngine:
    """
    Sentinel's planning coordinator.

    This class coordinates planning while delegating every specialized
    cognitive responsibility to dedicated planning services.
    """

    def __init__(self):
        self.strategy = StrategyEngine()
        self.steps = StepDecomposer()
        self.risk = RiskAnalyzer()
        self.confidence = PlanningConfidenceEngine()

    @staticmethod
    def _reasoning_basis(
        context: PlanningContext,
    ) -> PlanningReasoningBasis:
        """
        Convert the authoritative ReasoningResult into a planning-safe
        reasoning foundation.
        """

        reasoning = context.reasoning_result
        conclusion = reasoning.conclusion

        if conclusion is None:
            return PlanningReasoningBasis(
                question=reasoning.question,
                conclusion=None,
                confidence_score=0.0,
                confidence_level="low",
                reasoning_status=reasoning.status,
                evidence_source_count=(
                    reasoning.evidence.source_count
                ),
                document_count=(
                    reasoning.evidence.document_count
                ),
                domain_count=(
                    reasoning.evidence.domain_count
                ),
                limitations=[
                    gap.description
                    for gap in reasoning.evidence.gaps
                ],
                missing_information=[
                    gap.description
                    for gap in reasoning.evidence.gaps
                ],
            )

        return PlanningReasoningBasis(
            question=reasoning.question,
            conclusion=conclusion.statement,
            confidence_score=(
                conclusion.confidence.score
            ),
            confidence_level=(
                conclusion.confidence.level.value
            ),
            reasoning_status=reasoning.status,
            evidence_source_count=(
                reasoning.evidence.source_count
            ),
            document_count=(
                reasoning.evidence.document_count
            ),
            domain_count=(
                reasoning.evidence.domain_count
            ),
            limitations=conclusion.limitations,
            missing_information=(
                conclusion.missing_information
            ),
        )

    @staticmethod
    def _objective(
        context: PlanningContext,
    ) -> PlanningObjective:
        """
        Build the internal objective contract.

        Sprint 15 preserves the user-supplied objective directly and
        avoids inventing scope or success conditions.
        """

        return PlanningObjective(
            statement=context.objective,
            desired_outcome=context.objective,
            scope=None,
            success_conditions=[],
            constraints=context.constraints,
        )

    @staticmethod
    def _complexity(
        *,
        step_count: int,
        dependency_count: int,
        risk_count: int,
        assumption_count: int,
    ) -> PlanningComplexity:
        """
        Estimate planning complexity from visible plan structure.

        Complexity represents cognitive and operational structure,
        not duration.
        """

        structural_load = (
            step_count
            + dependency_count
            + risk_count
            + assumption_count
        )

        if structural_load >= 18:
            return PlanningComplexity.VERY_HIGH

        if structural_load >= 11:
            return PlanningComplexity.HIGH

        if structural_load >= 6:
            return PlanningComplexity.MEDIUM

        return PlanningComplexity.LOW

    @staticmethod
    def _success_criteria(
        context: PlanningContext,
    ) -> list[str]:
        """
        Preserve observable completion conditions without inventing
        domain-specific facts.
        """

        return [
            "The stated objective has been evaluated against the "
            "resulting state.",
            "Every approved planning step has satisfied its completion "
            "criteria.",
            "Unresolved high-impact conditions have been resolved or "
            "explicitly accepted.",
            "The final outcome has been reviewed by a human authority.",
        ]

    @staticmethod
    def _insufficient_confidence() -> PlanningConfidence:
        """
        Return the deterministic planning-confidence result used when
        reasoning cannot support planning.
        """

        return PlanningConfidence(
            score=0.0,
            level=PlanningConfidenceLevel.LOW,
            basis=(
                "Planning confidence is zero because no supported "
                "reasoning conclusion is available."
            ),
            factors=[],
            uncertainty=[
                "A supported reasoning conclusion is required before "
                "Sentinel can construct a plan.",
            ],
        )

    def plan(
        self,
        *,
        context: PlanningContext,
        metadata: dict | None = None,
    ) -> PlanningResult:
        """
        Produce one complete planning operation.

        The resulting object is fully inspectable and contains no hidden
        reasoning process or execution state.
        """

        trace: list[str] = []

        reasoning_basis = self._reasoning_basis(
            context
        )

        objective = self._objective(
            context
        )

        trace.append(
            "Interpreted the planning objective."
        )

        if (
            context.reasoning_result.status != "complete"
            or context.reasoning_result.conclusion is None
        ):
            trace.append(
                "No supported reasoning conclusion was available."
            )

            return PlanningResult(
                objective=objective,
                reasoning_basis=reasoning_basis,
                strategy=None,
                steps=[],
                dependencies=[],
                assumptions=[],
                constraints=context.constraints,
                risks=[],
                success_criteria=[],
                estimated_complexity=(
                    PlanningComplexity.LOW
                ),
                confidence=(
                    self._insufficient_confidence()
                ),
                planning_trace=trace,
                status=(
                    PlanningStatus.INSUFFICIENT_REASONING
                ),
                metadata={
                    **context.metadata,
                    **(metadata or {}),
                },
            )

        candidate_strategies = (
            self.strategy.generate(context)
        )

        trace.append(
            "Generated and ranked candidate strategies."
        )

        if not candidate_strategies:
            trace.append(
                "No supported strategy could be selected."
            )

            return PlanningResult(
                objective=objective,
                reasoning_basis=reasoning_basis,
                strategy=None,
                steps=[],
                dependencies=[],
                assumptions=[],
                constraints=context.constraints,
                risks=[],
                success_criteria=[],
                estimated_complexity=(
                    PlanningComplexity.LOW
                ),
                confidence=(
                    self._insufficient_confidence()
                ),
                planning_trace=trace,
                status=PlanningStatus.BLOCKED,
                metadata={
                    **context.metadata,
                    **(metadata or {}),
                },
            )

        selected_strategy = candidate_strategies[0]

        trace.append(
            "Selected the strongest supported strategy."
        )

        steps = self.steps.decompose(
            context=context,
            strategy=selected_strategy,
        )

        trace.append(
            "Decomposed the strategy into ordered steps."
        )

        risk_analysis = self.risk.analyze(
            context=context,
            strategy=selected_strategy,
            steps=steps,
        )

        trace.extend(
            risk_analysis.analysis_trace
        )

        planning_confidence = (
            self.confidence.assess(
                context=context,
                strategy=selected_strategy,
                steps=steps,
                risk_analysis=risk_analysis,
            )
        )

        trace.append(
            "Calculated planning confidence."
        )

        success_criteria = (
            self._success_criteria(context)
        )

        complexity = self._complexity(
            step_count=len(steps),
            dependency_count=len(
                risk_analysis.dependencies
            ),
            risk_count=len(
                risk_analysis.risks
            ),
            assumption_count=len(
                risk_analysis.assumptions
            ),
        )

        status = PlanningStatus.COMPLETE

        if (
            not steps
            or planning_confidence.score < 0.25
        ):
            status = PlanningStatus.BLOCKED
        elif (
            selected_strategy.name
            == "Clarification-first strategy"
        ):
            status = (
                PlanningStatus.REQUIRES_CLARIFICATION
            )

        trace.append(
            "Produced the structured planning result."
        )

        return PlanningResult(
            objective=objective,
            reasoning_basis=reasoning_basis,
            strategy=selected_strategy,
            steps=steps,
            dependencies=(
                risk_analysis.dependencies
            ),
            assumptions=(
                risk_analysis.assumptions
            ),
            constraints=context.constraints,
            risks=risk_analysis.risks,
            success_criteria=success_criteria,
            estimated_complexity=complexity,
            confidence=planning_confidence,
            planning_trace=trace,
            status=status,
            metadata={
                **context.metadata,
                **(metadata or {}),
                "candidate_strategies": [
                    strategy.model_dump()
                    for strategy in candidate_strategies
                ],
                "unresolved_conditions": (
                    risk_analysis.unresolved_conditions
                ),
            },
        )
