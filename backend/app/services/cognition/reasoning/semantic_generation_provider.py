"""Provider-neutral raw generation boundary for future proposition generators.

The response is untrusted model output, not a CandidateProposition or a
grounding decision. This module deliberately has no model SDK or credentials.
"""

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field

from app.services.cognition.reasoning.models import Premise, PremiseRelationship


class SemanticGenerationResponse(BaseModel):
    """Opaque untrusted text with optional observational provider metadata."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    content: str = Field(min_length=1)
    provider_metadata: dict[str, str] = Field(default_factory=dict)


class SemanticGenerationFailure(Exception):
    """Bounded failure reason without provider-specific exceptions or payloads."""

    def __init__(
        self,
        reason: Literal["unavailable", "refused", "malformed_response"],
    ) -> None:
        if reason not in {"unavailable", "refused", "malformed_response"}:
            raise ValueError("Unknown semantic generation failure reason.")
        self.reason = reason
        super().__init__(reason)


class SemanticGenerationProvider(Protocol):
    """Capability needed by a future SemanticPropositionGenerator.

    Implementations translate trusted inputs into model requests and return
    untrusted text. Failures raise SemanticGenerationFailure; they never
    return a fabricated response or candidate.
    """

    def generate(
        self,
        *,
        premises: list[Premise],
        relationships: list[PremiseRelationship],
    ) -> SemanticGenerationResponse:
        ...
