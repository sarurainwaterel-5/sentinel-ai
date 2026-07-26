from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.reasoning_service import ReasoningService


router = APIRouter()
reasoning = ReasoningService()


class RecallRequest(BaseModel):
    question: str = Field(min_length=1)
    module: str | None = None
    topic: str | None = None
    organization_id: str = "default"
    limit: int = Field(default=5, ge=1, le=20)
    score_threshold: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
    )


@router.post("/ask")
def ask_question(request: RecallRequest):
    return reasoning.answer_question(
        question=request.question,
        limit=request.limit,
        score_threshold=request.score_threshold,
        module=request.module,
        topic=request.topic,
        organization_id=request.organization_id,
    )
