"""Independent, provider-neutral semantic assessment; all responses are untrusted."""

from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


SemanticRejectionCode = Literal[
    "unsupported_fact", "certainty_inflation", "causal_overreach",
    "negation_reversal", "fabricated_precision", "conflict_suppression",
    "unsupported_qualification", "insufficient_support",
]


class SemanticPremiseText(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    premise_id: str
    statement: str


class SemanticRelationshipText(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    source_premise_id: str
    target_premise_id: str
    kind: Literal["supports", "complements", "conflicts"]
    basis: str


class SemanticAdmissibilityRequest(BaseModel):
    """Source text and assessed semantics only; no generator/provider metadata."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    statement: str
    qualifications: tuple[str, ...]
    premises: tuple[SemanticPremiseText, ...]
    relationships: tuple[SemanticRelationshipText, ...]


class SemanticJudgeVerdict(BaseModel):
    """Required explicit checks, not confidence or private reasoning."""
    model_config = ConfigDict(extra="forbid", frozen=True)
    admissible: bool
    unsupported_fact: bool
    certainty_inflation: bool
    causal_overreach: bool
    negation_reversal: bool
    fabricated_precision: bool
    conflict_suppression: bool
    unsupported_qualification: bool
    insufficient_support: bool
    rejection_reasons: tuple[SemanticRejectionCode, ...]


class SemanticAdmissibilityResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    content: str = Field(min_length=1, max_length=8192)


class SemanticAdmissibilityFailure(Exception):
    def __init__(self, reason: Literal["unavailable", "refused", "malformed_response"]):
        if reason not in {"unavailable", "refused", "malformed_response"}:
            raise ValueError("Unknown semantic judge failure reason.")
        self.reason = reason
        super().__init__(reason)


class SemanticAdmissibilityProvider(Protocol):
    """Separately injected assessment capability, never a generation approval."""
    def assess(self, *, request: SemanticAdmissibilityRequest) -> SemanticAdmissibilityResponse:
        ...
