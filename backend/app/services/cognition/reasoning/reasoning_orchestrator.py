from app.schemas.cognition.reasoning import (
    CoherenceResult,
    CommunicationSummary,
    ConfidenceSummary,
    EvidenceSourceSummary,
    EvidenceSummary,
    ReasoningRequest,
    ReasoningResponse,
    ReasoningSummary,
)

from app.services.constitutional_reasoning_service import (
    ConstitutionalReasoningService,
)

from app.services.cognition.coherence.coherence_engine import (
    CoherenceEngine,
)

from app.services.retrieval_service import RetrievalService

from app.services.cognition.reasoning.reasoning_engine import (
    ReasoningEngine,
)

from app.services.cognition.reasoning.llm_formatter import (
    LLMReasoningFormatter,
)


class ReasoningOrchestrator:
    """
    Coordinates SentinelAI's reasoning workflow.

    The orchestrator owns workflow, not business logic.
    """

    def __init__(self):
        self.identity_service = ConstitutionalReasoningService()
        self.retrieval_service = RetrievalService()
        self.reasoning_engine = ReasoningEngine()
        self.formatter = LLMReasoningFormatter()
        self.coherence_engine = CoherenceEngine()

    def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        identity = self.identity_service.build_constitution_context(
            question=request.question,
            limit=5,
        )
        knowledge = self.retrieval_service.search(
            question=request.question,
            limit=request.limit,
            score_threshold=request.score_threshold,
            module=request.module,
            topic=request.topic,
            organization_id=request.organization_id,
        )
        reasoning_result = self.reasoning_engine.reason(
            question=request.question,
            chunks=knowledge,
            metadata={
                "workspace": request.workspace,
                "module": request.module,
                "topic": request.topic,
                "organization_id": request.organization_id,
            },
        )

        formatted = self.formatter.format(
            result=reasoning_result,
        )

        knowledge_context = "\n".join(
            (
                chunk.payload.get("text", "")
                if hasattr(chunk, "payload")
                else chunk.get("payload", {}).get("text", "")
            )
            for chunk in knowledge
        )

        coherence = self.coherence_engine.evaluate(
            question=request.question,
            identity_context=identity["constitutional_context"],
            knowledge_context=knowledge_context,
        )
                

        communication = CommunicationSummary(
            answer=formatted.answer,
            evidence_explanation=formatted.evidence_explanation,
            confidence_explanation=formatted.confidence_explanation,
            limitations_explanation=formatted.limitations_explanation,
            next_step_explanation=formatted.next_step_explanation,
        )

        evidence_items = [
            *reasoning_result.evidence.supporting,
            *reasoning_result.evidence.conflicting,
            *reasoning_result.evidence.contextual,
            *reasoning_result.evidence.unknown,
        ]

        evidence_sources = [
            EvidenceSourceSummary(
                **item.source.model_dump()
            )
            for item in evidence_items
        ]

        evidence_summary = EvidenceSummary(
            source_count=reasoning_result.evidence.source_count,
            document_count=reasoning_result.evidence.document_count,
            domain_count=reasoning_result.evidence.domain_count,
            sources=evidence_sources,
            gaps=[
                gap.description
                for gap in reasoning_result.evidence.gaps
            ],
        )

        conclusion = reasoning_result.conclusion

        if conclusion is None:
            gap_descriptions = [
                gap.description
                for gap in reasoning_result.evidence.gaps
            ]

            confidence_summary = ConfidenceSummary(
                score=0.0,
                level="low",
                basis=(
                    "The reasoning engine could not produce a "
                    "supported conclusion from the available evidence."
                ),
                factors=[],
                uncertainty=gap_descriptions,
            )

            reasoning_summary = ReasoningSummary(
                conclusion=None,
                evidence_summary=None,
                inference_summary=None,
                confidence=confidence_summary,
                evidence=evidence_summary,
                limitations=gap_descriptions,
                alternatives=[],
                missing_information=gap_descriptions,
                recommended_next_step=(
                    formatted.recommended_next_step
                ),
                reasoning_trace=reasoning_result.reasoning_trace,
                status=reasoning_result.status,
            )

        else:
            confidence_summary = ConfidenceSummary(
                score=conclusion.confidence.score,
                level=conclusion.confidence.level.value,
                basis=conclusion.confidence.basis,
                factors=[
                    factor.model_dump()
                    for factor in conclusion.confidence.factors
                ],
                uncertainty=conclusion.confidence.uncertainty,
            )

            reasoning_summary = ReasoningSummary(
                conclusion=conclusion.statement,
                evidence_summary=conclusion.evidence_summary,
                inference_summary=conclusion.inference_summary,
                confidence=confidence_summary,
                evidence=evidence_summary,
                limitations=conclusion.limitations,
                alternatives=conclusion.alternatives,
                missing_information=conclusion.missing_information,
                recommended_next_step=(
                    conclusion.recommended_next_step
                ),
                reasoning_trace=reasoning_result.reasoning_trace,
                status=reasoning_result.status,
            )

        coherence_payload = (
            coherence.model_dump()
            if hasattr(coherence, "model_dump")
            else coherence
        )

        coherence_summary = CoherenceResult.model_validate(
            coherence_payload
        )

        constitutional_sources = [
            source["source_file"]
            for source in identity["sources"]
            if source.get("source_file")
        ]

        knowledge_sources = list(
            dict.fromkeys(
                source.filename
                for source in evidence_sources
                if source.filename
            )
        )

        return ReasoningResponse(
            answer=formatted.answer,
            communication=communication,
            reasoning=reasoning_summary,
            coherence=coherence_summary,
            constitutional_sources=constitutional_sources,
            knowledge_sources=knowledge_sources,
            workspace=request.workspace,
            module=request.module,
            topic=request.topic,
            organization_id=request.organization_id,
            mission_id=request.mission_id,
            session_id=request.session_id,
        )
