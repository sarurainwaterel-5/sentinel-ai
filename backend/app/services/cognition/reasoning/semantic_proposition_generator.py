"""
Semantic proposition generation contract.

Semantic generators produce untrusted candidate propositions.

They do not determine whether their own output is evidence-grounded
and they do not construct trusted SynthesizedProposition artifacts.
"""

from typing import Protocol

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
