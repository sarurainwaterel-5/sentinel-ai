"""
Public API route for SentinelAI cognitive planning.
"""

from fastapi import APIRouter

from app.schemas.cognition.planning import (
    PlanningRequest,
    PlanningResponse,
)
from app.services.cognition.planning.planning_orchestrator import (
    PlanningOrchestrator,
)


router = APIRouter(
    prefix="/cognition",
    tags=["Cognition"],
)


@router.post(
    "/plan",
    response_model=PlanningResponse,
)
def plan(
    request: PlanningRequest,
) -> PlanningResponse:
    """
    Produce one evidence-aware, non-executing cognitive plan.
    """

    orchestrator = PlanningOrchestrator()

    return orchestrator.plan(request)
