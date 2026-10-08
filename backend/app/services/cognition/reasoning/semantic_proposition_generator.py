"""
Semantic proposition generation contract.

Semantic generators produce untrusted candidate propositions.

They do not determine whether their own output is evidence-grounded
and they do not construct trusted SynthesizedProposition artifacts.
"""

from typing import Protocol

from app.services.cognition.reasoning.semantic_generation_provider import (
    SemanticGenerationFailure,
    SemanticGenerationProvider,
    SemanticGenerationResponse,
)

from app.services.cognition.reasoning.models import (
    CandidateProposition,
    Premise,
    PremiseRelationship,
)


class SemanticPropositionGenerator(Protocol):
    """
    Capability contract for proposing semantic propositions.

    Implementations generate untrusted candidates that must pass
    Sentinel governance before promotion to trusted propositions.
    """

    def generate(
        self,
        *,
        premises: list[Premise],
        relationships: list[PremiseRelationship],
    ) -> CandidateProposition | None:
        ...


class ProviderSemanticPropositionGenerator:
    """Translate raw provider JSON into an untrusted candidate.

    Providers must return one CandidateProposition JSON object. No prose,
    markdown extraction, repair, or fallback is attempted. Schema errors
    propagate to the synthesizer's malformed_generation outcome; bounded
    provider failures remain distinct. Parsing never certifies grounding.
    """

    def __init__(self, *, provider: SemanticGenerationProvider):
        self.provider = provider

    def generate(
        self,
        *,
        premises: list[Premise],
        relationships: list[PremiseRelationship],
    ) -> CandidateProposition:
        # A provider must not mutate the trusted artifacts later used by
        # Sentinel to reconstruct provenance.
        response = self.provider.generate(
            premises=[premise.model_copy(deep=True) for premise in premises],
            relationships=[relation.model_copy(deep=True) for relation in relationships],
        )
        if not isinstance(response, SemanticGenerationResponse):
            raise SemanticGenerationFailure("malformed_response")

        candidate = CandidateProposition.model_validate_json(
            response.content, strict=True
        )
        # Observational metadata stays in the untrusted candidate namespace.
        # Neither this metadata nor the candidate's references are authoritative.
        candidate.generator_metadata["provider_metadata"] = dict(
            response.provider_metadata
        )
        return candidate
