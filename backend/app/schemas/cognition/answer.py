"""Request contract only; no Sprint 21 endpoint is registered."""
from pydantic import ConfigDict
from app.schemas.cognition.reasoning import ReasoningRequest


class GovernedAnswerRequest(ReasoningRequest):
    model_config = ConfigDict(extra="forbid", strict=True)
    # Organization filtering is not authorization. Future composition must
    # resolve this field against the authenticated operator's server scope.
