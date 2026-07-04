from app.schemas.cognition.reasoning import ReasoningRequest, ReasoningResponse
from app.services.constitutional_reasoning_service import ConstitutionalReasoningService
from app.services.cognition.coherence.coherence_engine import CoherenceEngine


class ReasoningOrchestrator:
    """
    Coordinates SentinelAI's reasoning workflow.

    The orchestrator owns workflow, not business logic.
    """

    def __init__(self):
        self.identity_service = ConstitutionalReasoningService()
        self.coherence_engine = CoherenceEngine()

    def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        identity = self.identity_service.build_constitution_context(
            question=request.question,
            limit=5,
        )

        coherence = self.coherence_engine.evaluate(
            question=request.question,
            identity_context=identity["constitutional_context"],
            knowledge_context=None,
        )

        return ReasoningResponse(
            answer="Reasoning orchestration skeleton is online. Identity was consulted and coherence was evaluated.",
            workspace=request.workspace,
            constitutional_sources=[
                source["source_file"]
                for source in identity["sources"]
            ],
            knowledge_sources=[],
            confidence=0.5,
            coherence=coherence,
            reflection="Reflection service is not yet implemented.",
        )
