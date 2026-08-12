"""
SentinelAI cognitive verification orchestration.

The orchestrator coordinates the complete public verification workflow.

It does not:

- retrieve evidence itself,
- perform reasoning,
- construct planning strategies or steps,
- perform specialist verification,
- calculate verification coverage,
- calculate verification confidence,
- format natural-language communication,
- execute actions.

It owns workflow and public-response assembly.
"""

from __future__ import annotations

from app.schemas.cognition.verification import (
    VerificationCheckSummary,
    VerificationCoherenceResult,
    VerificationCommunicationSummary,
    VerificationConfidenceSummary,
    VerificationCoverageSummary,
    VerificationFindingSummary,
    VerificationRequest,
    VerificationResponse,
    VerificationStandardSummary,
    VerificationSummary,
    VerifiedPlanningSubjectSummary,
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

from app.services.cognition.reasoning.reasoning_engine import (
    ReasoningEngine,
)

from app.services.cognition.verification.models import (
    VerificationCategory,
    VerificationContext,
    VerificationScope,
)

from app.services.cognition.verification.verification_engine import (
    VerificationEngine,
)

from app.services.cognition.verification.verification_formatter import (
    LLMVerificationFormatter,
)

from app.services.constitutional_reasoning_service import (
    ConstitutionalReasoningService,
)

from app.services.retrieval_service import (
    RetrievalService,
)


class VerificationOrchestrator:
    """
    Coordinate SentinelAI's evidence-aware verification workflow.

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

        self.verification_engine = VerificationEngine()

        self.formatter = LLMVerificationFormatter()

        self.coherence_engine = CoherenceEngine()

    @staticmethod
    def _chunk_text(
        chunk,
    ) -> str:
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
    def _scope(
        request: VerificationRequest,
    ) -> VerificationScope:
        """
        Translate the public verification scope into its internal enum.
        """

        return VerificationScope(
            request.verification_scope
        )

    @staticmethod
    def _categories(
        request: VerificationRequest,
    ) -> list[VerificationCategory]:
        """
        Translate public category strings into internal enums.

        Pydantic public contracts intentionally remain consumer-friendly.
        Internal cognition uses typed verification categories.
        """

        return [
            VerificationCategory(category)
            for category in (
                request.verification_categories
            )
        ]

    @staticmethod
    def _confidence_summary(
        verification_result,
    ) -> VerificationConfidenceSummary:
        """
        Translate authoritative verification confidence into its public
        representation.
        """

        confidence = (
            verification_result.confidence
        )

        return VerificationConfidenceSummary(
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
    def _coverage_summary(
        verification_result,
    ) -> VerificationCoverageSummary:
        """
        Translate authoritative coverage into its public representation.
        """

        coverage = (
            verification_result.coverage
        )

        return VerificationCoverageSummary(
            requested_categories=[
                category.value
                for category in (
                    coverage.requested_categories
                )
            ],
            completed_categories=[
                category.value
                for category in (
                    coverage.completed_categories
                )
            ],
            skipped_categories=[
                category.value
                for category in (
                    coverage.skipped_categories
                )
            ],
            check_count=coverage.check_count,
            passed_count=coverage.passed_count,
            conditional_count=(
                coverage.conditional_count
            ),
            failed_count=coverage.failed_count,
            unverifiable_count=(
                coverage.unverifiable_count
            ),
            not_applicable_count=(
                coverage.not_applicable_count
            ),
        )

    @staticmethod
    def _standard_summaries(
        verification_result,
    ) -> list[VerificationStandardSummary]:
        """
        Translate internal verification standards into public summaries.
        """

        return [
            VerificationStandardSummary(
                standard_id=standard.standard_id,
                category=standard.category.value,
                title=standard.title,
                description=standard.description,
                required=standard.required,
                source=standard.source,
            )
            for standard in (
                verification_result.standards
            )
        ]

    @staticmethod
    def _check_summaries(
        verification_result,
    ) -> list[VerificationCheckSummary]:
        """
        Translate internal verification checks into public summaries.
        """

        return [
            VerificationCheckSummary(
                check_id=check.check_id,
                category=check.category.value,
                standard_id=check.standard_id,
                observation=check.observation,
                outcome=check.outcome.value,
                severity=check.severity.value,
                evidence_references=(
                    check.evidence_references
                ),
                affected_object_ids=(
                    check.affected_object_ids
                ),
                recommendation=(
                    check.recommendation
                ),
                uncertainty=check.uncertainty,
            )
            for check in (
                verification_result.checks
            )
        ]

    @staticmethod
    def _finding_summaries(
        verification_result,
    ) -> list[VerificationFindingSummary]:
        """
        Translate internal verification findings into public summaries.
        """

        return [
            VerificationFindingSummary(
                finding_id=finding.finding_id,
                category=finding.category.value,
                title=finding.title,
                description=finding.description,
                severity=finding.severity.value,
                affected_object_ids=(
                    finding.affected_object_ids
                ),
                evidence=finding.evidence,
                required_resolution=(
                    finding.required_resolution
                ),
                blocking=finding.blocking,
            )
            for finding in (
                verification_result.findings
            )
        ]

    @staticmethod
    def _subject_summary(
        verification_result,
        planning_result,
    ) -> VerifiedPlanningSubjectSummary:
        """
        Translate the verified PlanningResult into a stable public subject
        summary.
        """

        subject = (
            verification_result.subject
        )

        return VerifiedPlanningSubjectSummary(
            objective=subject.objective,
            strategy=subject.strategy_name,
            planning_status=(
                subject.subject_status
            ),
            planning_confidence_score=(
                subject.subject_confidence_score
            ),
            planning_confidence_level=(
                subject.subject_confidence_level
            ),
            step_count=len(
                planning_result.steps
            ),
            dependency_count=len(
                planning_result.dependencies
            ),
            assumption_count=len(
                planning_result.assumptions
            ),
            risk_count=len(
                planning_result.risks
            ),
            constraint_count=(
                subject.constraint_count
            ),
        )

    def verify(
        self,
        request: VerificationRequest,
    ) -> VerificationResponse:
        """
        Execute one complete evidence-aware verification operation.
        """

        identity = (
            self.identity_service
            .build_constitution_context(
                question=request.objective,
                limit=5,
            )
        )

        knowledge = (
            self.retrieval_service.search(
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
        )

        reasoning_result = (
            self.reasoning_engine.reason(
                question=request.objective,
                chunks=knowledge,
                metadata={
                    "workspace": (
                        request.workspace
                    ),
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
                    "cognitive_operation": (
                        "verification_reasoning_basis"
                    ),
                },
            )
        )

        planning_context = PlanningContext(
            objective=request.objective,
            reasoning_result=(
                reasoning_result
            ),
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
                "cognitive_operation": (
                    "verification_planning_basis"
                ),
            },
        )

        planning_result = (
            self.planning_engine.plan(
                context=planning_context,
                metadata={
                    "workspace": (
                        request.workspace
                    ),
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
                    "cognitive_operation": (
                        "verification_planning_basis"
                    ),
                },
            )
        )

        verification_context = (
            VerificationContext(
                subject=planning_result,
                scope=self._scope(
                    request
                ),
                requested_categories=(
                    self._categories(
                        request
                    )
                ),
                governing_constraints=(
                    request.constraints
                ),
                workspace=request.workspace,
                module=request.module,
                topic=request.topic,
                organization_id=(
                    request.organization_id
                ),
                mission_id=(
                    request.mission_id
                ),
                session_id=(
                    request.session_id
                ),
                metadata={
                    "cognitive_operation": (
                        "verification"
                    ),
                },
            )
        )

        verification_result = (
            self.verification_engine.verify(
                context=verification_context
            )
        )

        formatted = self.formatter.format(
            verification_result
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
            VerificationCommunicationSummary(
                answer=formatted.answer,
                subject_explanation=(
                    formatted.subject_explanation
                ),
                checks_explanation=(
                    formatted.checks_explanation
                ),
                findings_explanation=(
                    formatted.findings_explanation
                ),
                conditions_explanation=(
                    formatted.conditions_explanation
                ),
                confidence_explanation=(
                    formatted.confidence_explanation
                ),
            )
        )

        verification_summary = (
            VerificationSummary(
                subject_type=(
                    verification_result
                    .subject
                    .subject_type
                    .value
                ),
                subject=self._subject_summary(
                    verification_result,
                    planning_result,
                ),
                verification_scope=(
                    verification_result
                    .scope
                    .value
                ),
                standards=(
                    self._standard_summaries(
                        verification_result
                    )
                ),
                checks=(
                    self._check_summaries(
                        verification_result
                    )
                ),
                findings=(
                    self._finding_summaries(
                        verification_result
                    )
                ),
                conditions=(
                    verification_result.conditions
                ),
                coverage=(
                    self._coverage_summary(
                        verification_result
                    )
                ),
                confidence=(
                    self._confidence_summary(
                        verification_result
                    )
                ),
                verification_trace=(
                    verification_result
                    .verification_trace
                ),
                status=(
                    verification_result.status.value
                ),
            )
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
            VerificationCoherenceResult
            .model_validate(
                coherence_payload
            )
        )

        return VerificationResponse(
            answer=formatted.answer,
            communication=communication,
            verification=(
                verification_summary
            ),
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
