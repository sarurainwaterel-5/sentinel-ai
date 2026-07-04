from fastapi import APIRouter

from app.schemas.cognition.reasoning import ReasoningRequest, ReasoningResponse
from app.services.cognition.reasoning.reasoning_orchestrator import ReasoningOrchestrator

router = APIRouter(
    prefix="/cognition",
    tags=["Cognition"]
)


@router.post("/reason", response_model=ReasoningResponse)
def reason(request: ReasoningRequest):
    orchestrator = ReasoningOrchestrator()
    return orchestrator.reason(request)
