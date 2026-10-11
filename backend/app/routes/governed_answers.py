"""Sprint 21-D disabled boundary. No cognitive/provider dependencies allowed."""
from uuid import uuid4
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.schemas.cognition.answer import GovernedAnswerRequest
from app.services.cognition.reasoning.answer_models import AnswerScope, AnswerValidation, GovernedAnswer

router = APIRouter(prefix="/cognition", tags=["Governed answers"])
BLOCKERS = ("production_release_disabled", "semantic_benchmark_acceptance_required", "answer_presentation_acceptance_required")


@router.get("/answer/readiness")
async def answer_readiness():
    return {"schema_version": "21.v1", "status": "disabled", "enabled": False,
        "semantic_grounding_verified": False, "proposition_to_inference": "closed",
        "blockers": list(BLOCKERS)}


@router.post("/answer", response_model=GovernedAnswer, responses={503: {"model": GovernedAnswer}})
async def governed_answer(request: GovernedAnswerRequest):
    # The existing installation's authenticated proxy has one local operator.
    # Filtering is not tenant authorization. No arbitrary organization is accepted.
    if request.organization_id != "default":
        raise HTTPException(status_code=403, detail="Organization is outside the local operator scope.")
    response = GovernedAnswer(answer_id=str(uuid4()), request_id=str(uuid4()),
        question=request.question, snapshot_id=str(uuid4()),
        scope=AnswerScope(organization_id="default", module=request.module, topic=request.topic,
            limit=request.limit, score_threshold=request.score_threshold),
        validation=AnswerValidation(rejection_reasons=BLOCKERS),
        uncertainty=("Governed answering is disabled pending release acceptance.",),
        operational_trace=("Production release gate blocked the request before cognitive/provider work.",),
        recommended_next_step="Inspect readiness. Existing Reason is a separate capability, not a fallback.")
    return JSONResponse(status_code=503, content=response.model_dump(mode="json"))
