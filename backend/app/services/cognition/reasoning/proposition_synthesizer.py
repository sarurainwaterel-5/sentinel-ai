"""Governed promotion of untrusted candidate propositions."""

from uuid import uuid4
from typing import Literal

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
from app.services.cognition.reasoning.statement_admissibility_validator import (
    StatementAdmissibilityResult,
    StatementAdmissibilityValidator,
    FreeFormStatementAdmissibilityValidator,
)


class PropositionSynthesisOutcome(BaseModel):
    """Inspectable high-level outcome; contains no private model reasoning."""

    model_config = ConfigDict(frozen=True)

    propositions: list[SynthesizedProposition] = Field(default_factory=list)
    rejection_reasons: tuple[str, ...] = ()
    validation: PropositionGroundingValidationResult | None = None
    statement_validation: StatementAdmissibilityResult | None = None
    acceptance_mode: Literal["rejected", "structural_only_compatibility", "statement_validated"] = "rejected"


class PropositionSynthesizer:
    """Coordinates candidate generation, validation, and trusted promotion."""

    def __init__(
        self,
        *,
        semantic_generator: SemanticPropositionGenerator,
        statement_validator: StatementAdmissibilityValidator | None = None,
        structural_only_compatibility: bool = False,
    ):
        self.semantic_generator = semantic_generator
        self.grounding_validator = PropositionGroundingValidator()
        self.statement_validator = statement_validator
        self.structural_only_compatibility = structural_only_compatibility
        if statement_validator is not None and structural_only_compatibility:
            raise ValueError("Compatibility mode cannot also claim statement validation.")
        if isinstance(statement_validator, FreeFormStatementAdmissibilityValidator):
            generation_provider = getattr(semantic_generator, "provider", semantic_generator)
            if statement_validator.provider is generation_provider:
                raise ValueError("Generation cannot assess its own candidate.")
            generation_client = getattr(generation_provider, "client", None)
            if generation_client is not None and generation_client is getattr(statement_validator.provider, "client", None):
                raise ValueError("Generation and assessment must use separate clients.")

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
        if self.statement_validator is None and not self.structural_only_compatibility:
            return PropositionSynthesisOutcome(rejection_reasons=("statement_validator_required",))
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
                premises=[p.model_copy(deep=True) for p in participating],
                relationships=[r.model_copy(deep=True) for r in eligible],
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

        try:
            validation = self.grounding_validator.validate(
                candidate=candidate.model_copy(deep=True),
                premises=[p.model_copy(deep=True) for p in participating],
                relationships=[r.model_copy(deep=True) for r in relationships],
            )
            if not isinstance(validation, PropositionGroundingValidationResult):
                raise ValueError("Invalid structural validation result.")
        except Exception:
            return PropositionSynthesisOutcome(rejection_reasons=("grounding_validator_failure",))
        if not validation.structurally_valid:
            return PropositionSynthesisOutcome(
                rejection_reasons=validation.rejection_reasons,
                validation=validation,
            )

        statement_validation = None
        if self.statement_validator is not None:
            try:
                statement_validation = self.statement_validator.validate(
                    candidate=candidate.model_copy(deep=True),
                    premises=[p.model_copy(deep=True) for p in participating],
                    relationships=[r.model_copy(deep=True) for r in eligible],
                )
                if not isinstance(statement_validation, StatementAdmissibilityResult):
                    raise ValueError("Invalid statement validation result.")
                statement_validation = StatementAdmissibilityResult.model_validate(
                    statement_validation.model_dump(), strict=True
                )
                if statement_validation.admissible == bool(statement_validation.rejection_reasons):
                    raise ValueError("Inconsistent statement validation result.")
            except Exception:
                return PropositionSynthesisOutcome(
                    rejection_reasons=("statement_validator_failure",), validation=validation
                )
            if not statement_validation.admissible:
                return PropositionSynthesisOutcome(
                    rejection_reasons=statement_validation.rejection_reasons,
                    validation=validation,
                    statement_validation=statement_validation,
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
        if statement_validation is not None:
            proposition.metadata["statement_admissibility"] = statement_validation.validation_scope
        return PropositionSynthesisOutcome(
            propositions=[proposition], validation=validation,
            statement_validation=statement_validation,
            acceptance_mode="statement_validated" if statement_validation is not None else "structural_only_compatibility",
        )
