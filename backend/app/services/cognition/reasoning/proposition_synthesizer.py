"""Governed promotion of untrusted candidate propositions."""

from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from pydantic import ValidationError

from app.services.cognition.reasoning.models import (
    CandidateProposition,
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
    SynthesizedProposition,
)
from app.services.cognition.reasoning.proposition_grounding_validator import (
    PropositionGroundingValidator,
    PropositionGroundingValidationResult,
)
from app.services.cognition.reasoning.semantic_proposition_generator import (
    SemanticPropositionGenerator,
)
from app.services.cognition.reasoning.semantic_generation_provider import (
    SemanticGenerationFailure,
)


class PropositionSynthesisOutcome(BaseModel):
    """Inspectable high-level outcome; contains no private model reasoning."""

    model_config = ConfigDict(frozen=True)

    propositions: list[SynthesizedProposition] = Field(default_factory=list)
    rejection_reasons: tuple[str, ...] = ()
    validation: PropositionGroundingValidationResult | None = None


class PropositionSynthesizer:
    """Coordinates candidate generation, validation, and trusted promotion."""

    def __init__(
        self,
        *,
        semantic_generator: SemanticPropositionGenerator,
    ):
        self.semantic_generator = semantic_generator
        self.grounding_validator = PropositionGroundingValidator()

    def synthesize(
        self,
        *,
        premises: list[Premise],
        relationships: list[PremiseRelationship],
    ) -> list[SynthesizedProposition]:
        return self.synthesize_with_validation(
            premises=premises, relationships=relationships
        ).propositions

    def synthesize_with_validation(
        self,
        *,
        premises: list[Premise],
        relationships: list[PremiseRelationship],
    ) -> PropositionSynthesisOutcome:
        if len(premises) < 2:
            return PropositionSynthesisOutcome(rejection_reasons=("insufficient_premises",))

        premise_ids = {premise.premise_id for premise in premises}
        eligible = [
            relationship for relationship in relationships
            if relationship.kind not in {
                PremiseRelationshipKind.INDEPENDENT,
                PremiseRelationshipKind.UNRESOLVED,
            }
            and relationship.source_premise_id in premise_ids
            and relationship.target_premise_id in premise_ids
        ]
        if not eligible:
            return PropositionSynthesisOutcome(rejection_reasons=("no_eligible_relationships",))

        # Validate against all assessed relationships to catch omitted conflicts.
        participating_ids = set()
        for relationship in eligible:
            participating_ids.update((relationship.source_premise_id,
                                      relationship.target_premise_id))
        participating = [p for p in premises if p.premise_id in participating_ids]

        try:
            candidate = self.semantic_generator.generate(
                premises=participating, relationships=eligible
            )
        except SemanticGenerationFailure as error:
            return PropositionSynthesisOutcome(
                rejection_reasons=(f"provider_{error.reason}",)
            )
        except ValidationError:
            return PropositionSynthesisOutcome(
                rejection_reasons=("malformed_generation",)
            )
        except Exception:
            return PropositionSynthesisOutcome(rejection_reasons=("generator_failure",))

        if not isinstance(candidate, CandidateProposition):
            return PropositionSynthesisOutcome(rejection_reasons=("invalid_candidate",))

        validation = self.grounding_validator.validate(
            candidate=candidate, premises=participating, relationships=relationships
        )
        if not validation.structurally_valid:
            return PropositionSynthesisOutcome(
                rejection_reasons=validation.rejection_reasons,
                validation=validation,
            )

        proposition = SynthesizedProposition(
            proposition_id=f"proposition-{uuid4()}",
            statement=candidate.statement.strip(),
            premise_ids=list(validation.premise_ids),
            evidence_ids=list(validation.evidence_ids),
            domain_ids=list(validation.domain_ids),
            metadata={
                "semantic_grounding_verified": validation.semantic_grounding_verified,
                "relationship_kinds": [
                    relation.kind.value for relation in validation.relationships
                ],
            },
        )
        return PropositionSynthesisOutcome(
            propositions=[proposition], validation=validation
        )
