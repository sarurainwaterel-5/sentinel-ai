"""
SentinelAI cognitive planning orchestration.

The orchestrator coordinates the complete public planning workflow.

It does not:

- retrieve evidence itself,
- perform reasoning,
- select strategies,
- generate steps,
- analyze risks,
- calculate planning confidence,
- format natural-language communication,
- execute proposed actions.

It owns workflow and public-response assembly.
"""

from __future__ import annotations

from app.schemas.cognition.planning import (
    PlanningCoherenceResult,
    PlanningCommunicationSummary,
    PlanningConfidenceSummary,
    PlanningDependencySummary,
    PlanningReasoningBasisSummary,
    PlanningRequest,
    PlanningResponse,
    PlanningRiskSummary,
    PlanningStepSummary,
    PlanningSummary,
)
from app.services.cognition.coherence.coherence_engine import (
    CoherenceEngine,
)
from app.services.cognition.planning.models import (
    PlanningContext,
)
from app.services.cognition.planning.planning_engine import (
    PlanningEngine,
)
from app.services.cognition.planning.planning_formatter import (
    PlanningFormatter,
)
from app.services.cognition.reasoning.reasoning_engine import (
    ReasoningEngine,
)
from app.services.constitutional_reasoning_service import (
    ConstitutionalReasoningService,
)
from app.services.retrieval_service import (
    RetrievalService,
)


class PlanningOrchestrator:
    """
    Coordinate SentinelAI's evidence-aware planning workflow.

    The orchestrator owns sequencing and API mapping.

    Every cognitive responsibility remains delegated to its specialist
    service.
    """

    def __init__(self):
        self.identity_service = (
            ConstitutionalReasoningService()
        )
        self.retrieval_service = RetrievalService()
        self.reasoning_engine = ReasoningEngine()
        self.planning_engine = PlanningEngine()
        self.formatter = PlanningFormatter()
        self.coherence_engine = CoherenceEngine()

    @staticmethod
    def _chunk_text(chunk) -> str:
        """
        Extract retrieval text without coupling orchestration to one
        retrieval-result representation.
        """

        if hasattr(chunk, "payload"):
            payload = chunk.payload or {}
        else:
            payload = chunk.get(
                "payload",
                {},
            )

        return str(
            payload.get("text") or ""
        ).strip()

    @staticmethod
    def _knowledge_sources(
        reasoning_result,
    ) -> list[str]:
        """
        Return unique filenames from evidence used by reasoning.
        """

        evidence_items = [
            *reasoning_result.evidence.supporting,
            *reasoning_result.evidence.conflicting,
            *reasoning_result.evidence.contextual,
            *reasoning_result.evidence.unknown,
        ]

        return list(
            dict.fromkeys(
                item.source.filename
                for item in evidence_items
                if item.source.filename
            )
        )

    @staticmethod
    def _constitutional_sources(
        identity: dict,
    ) -> list[str]:
        """
        Return unique constitutional source paths.
        """

        return list(
            dict.fromkeys(
                source["source_file"]
                for source in identity.get(
                    "sources",
                    [],
                )
                if source.get("source_file")
            )
        )

    @staticmethod
    def _reasoning_basis_summary(
        planning_result,
    ) -> PlanningReasoningBasisSummary:
        """
        Translate the internal planning reasoning basis into its public
        consumer-facing contract.
        """

        basis = planning_result.reasoning_basis

        return PlanningReasoningBasisSummary(
            question=basis.question,
            conclusion=basis.conclusion,
            confidence_score=(
                basis.confidence_score
            ),
            confidence_level=(
                basis.confidence_level
            ),
            reasoning_status=(
                basis.reasoning_status
            ),
            evidence_source_count=(
                basis.evidence_source_count
            ),
            document_count=(
                basis.document_count
            ),
            limitations=basis.limitations,
        )

    @staticmethod
    def _confidence_summary(
        planning_result,
    ) -> PlanningConfidenceSummary:
        """
        Translate authoritative planning confidence into the public
        confidence representation.
        """

        confidence = planning_result.confidence

        return PlanningConfidenceSummary(
            score=confidence.score,
            level=confidence.level.value,
            basis=confidence.basis,
            factors=[
                factor.model_dump()
                for factor in confidence.factors
            ],
            uncertainty=confidence.uncertainty,
        )

    @staticmethod
    def _step_summaries(
        planning_result,
    ) -> list[PlanningStepSummary]:
        """
        Translate internal planning steps into stable public summaries.
        """

        return [
            PlanningStepSummary(
                step_id=step.step_id,
                sequence=step.sequence,
                title=step.title,
                description=step.description,
                rationale=step.rationale,
                dependency_ids=(
                    step.dependency_ids
                ),
                risk_ids=step.risk_ids,
                completion_criteria=(
                    step.completion_criteria
                ),
                requires_human_approval=(
                    step.requires_human_approval
                ),
            )
            for step in planning_result.steps
        ]

    @staticmethod
    def _dependency_summaries(
        planning_result,
    ) -> list[PlanningDependencySummary]:
        """
        Translate internal dependencies into stable public summaries.
        """

        return [
            PlanningDependencySummary(
                dependency_id=(
                    dependency.dependency_id
                ),
                description=(
                    dependency.description
                ),
                required_before_step_ids=(
                    dependency.required_before_step_ids
                ),
                satisfied=dependency.satisfied,
                verification_method=(
                    dependency.verification_method
                ),
            )
            for dependency in (
                planning_result.dependencies
            )
        ]

    @staticmethod
    def _risk_summaries(
        planning_result,
    ) -> list[PlanningRiskSummary]:
        """
        Translate internal planning risks into stable public summaries.
        """

        return [
            PlanningRiskSummary(
                risk_id=risk.risk_id,
                description=risk.description,
                likelihood=risk.likelihood.value,
                impact=risk.impact.value,
                mitigation=risk.mitigation,
                affected_step_ids=(
                    risk.affected_step_ids
                ),
            )
            for risk in planning_result.risks
        ]

    def plan(
        self,
        request: PlanningRequest,
    ) -> PlanningResponse:
        """
        Execute one complete evidence-aware planning operation.
        """

        identity = (
            self.identity_service
            .build_constitution_context(
                question=request.objective,
                limit=5,
            )
        )

        knowledge = self.retrieval_service.search(
            question=request.objective,
            limit=request.limit,
            score_threshold=(
                request.score_threshold
            ),
            module=request.module,
            topic=request.topic,
            organization_id=(
                request.organization_id
            ),
        )

        reasoning_result = (
            self.reasoning_engine.reason(
                question=request.objective,
                chunks=knowledge,
                metadata={
                    "workspace": request.workspace,
                    "module": request.module,
                    "topic": request.topic,
                    "organization_id": (
                        request.organization_id
                    ),
                    "mission_id": request.mission_id,
                    "session_id": request.session_id,
                    "cognitive_operation": (
                        "planning_reasoning_basis"
                    ),
                },
            )
        )

        planning_context = PlanningContext(
            objective=request.objective,
            reasoning_result=reasoning_result,
            constraints=request.constraints,
            supplied_assumptions=[],
            workspace=request.workspace,
            module=request.module,
            topic=request.topic,
            organization_id=(
                request.organization_id
            ),
            mission_id=request.mission_id,
            session_id=request.session_id,
            metadata={
                "cognitive_operation": "planning",
            },
        )

        planning_result = (
            self.planning_engine.plan(
                context=planning_context,
                metadata={
                    "workspace": request.workspace,
                    "module": request.module,
                    "topic": request.topic,
                    "organization_id": (
                        request.organization_id
                    ),
                    "mission_id": (
                        request.mission_id
                    ),
                    "session_id": (
                        request.session_id
                    ),
                },
            )
        )

        formatted = self.formatter.format(
            planning_result
        )

        knowledge_context = "\n".join(
            text
            for text in (
                self._chunk_text(chunk)
                for chunk in knowledge
            )
            if text
        )

        coherence = (
            self.coherence_engine.evaluate(
                question=request.objective,
                identity_context=(
                    identity[
                        "constitutional_context"
                    ]
                ),
                knowledge_context=(
                    knowledge_context
                ),
            )
        )

        communication = (
            PlanningCommunicationSummary(
                answer=formatted.answer,
                strategy_explanation=(
                    formatted.strategy_explanation
                ),
                steps_explanation=(
                    formatted.steps_explanation
                ),
                risk_explanation=(
                    formatted.risk_explanation
                ),
                success_explanation=(
                    formatted.success_explanation
                ),
            )
        )

        strategy = planning_result.strategy

        planning_summary = PlanningSummary(
            objective=(
                planning_result.objective.statement
            ),
            reasoning_basis=(
                self._reasoning_basis_summary(
                    planning_result
                )
            ),
            strategy=(
                strategy.name
                if strategy is not None
                else None
            ),
            strategy_rationale=(
                strategy.rationale
                if strategy is not None
                else None
            ),
            steps=self._step_summaries(
                planning_result
            ),
            dependencies=(
                self._dependency_summaries(
                    planning_result
                )
            ),
            assumptions=[
                assumption.statement
                for assumption in (
                    planning_result.assumptions
                )
            ],
            constraints=(
                planning_result.constraints
            ),
            risks=self._risk_summaries(
                planning_result
            ),
            success_criteria=(
                planning_result.success_criteria
            ),
            estimated_complexity=(
                planning_result
                .estimated_complexity
                .value
            ),
            confidence=(
                self._confidence_summary(
                    planning_result
                )
            ),
            planning_trace=(
                planning_result.planning_trace
            ),
            status=(
                planning_result.status.value
            ),
        )

        coherence_payload = (
            coherence.model_dump()
            if hasattr(
                coherence,
                "model_dump",
            )
            else coherence
        )

        coherence_summary = (
            PlanningCoherenceResult
            .model_validate(
                coherence_payload
            )
        )

        return PlanningResponse(
            answer=formatted.answer,
            communication=communication,
            planning=planning_summary,
            coherence=coherence_summary,
            constitutional_sources=(
                self._constitutional_sources(
                    identity
                )
            ),
            knowledge_sources=(
                self._knowledge_sources(
                    reasoning_result
                )
            ),
            workspace=request.workspace,
            module=request.module,
            topic=request.topic,
            organization_id=(
                request.organization_id
            ),
            mission_id=request.mission_id,
            session_id=request.session_id,
        )
