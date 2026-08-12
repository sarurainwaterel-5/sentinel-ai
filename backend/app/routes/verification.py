"""
Public API route for SentinelAI cognitive verification.

This route owns only the HTTP boundary.

It delegates the complete verification workflow to
VerificationOrchestrator.
"""

from fastapi import APIRouter

from app.schemas.cognition.verification import (
    VerificationRequest,
    VerificationResponse,
)

from app.services.cognition.verification.verification_orchestrator import (
    VerificationOrchestrator,
)


router = APIRouter(
    prefix="/verification",
    tags=["Verification"],
)

orchestrator = VerificationOrchestrator()


@router.post(
    "",
    response_model=VerificationResponse,
)
def verify(
    request: VerificationRequest,
) -> VerificationResponse:
    """
    Execute one complete SentinelAI verification operation.
    """

    return orchestrator.verify(
        request
    )
