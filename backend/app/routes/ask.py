from fastapi import APIRouter
from app.services.reasoning_service import ReasoningService

router = APIRouter()
reasoning = ReasoningService()

@router.get("/ask")
def ask_question(question: str, limit: int = 5, score_threshold: float = 0.45):
    return reasoning.answer_question(
        question=question,
        limit=limit,
        score_threshold=score_threshold
    )
