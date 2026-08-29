from uuid import uuid4

from app.services.cognition.reasoning.models import (
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
    SynthesizedProposition,
)


class PropositionSynthesizer:
    """
    Synthesizes higher-order propositions from related,
    evidence-grounded premises.

    The synthesizer preserves complete lineage back to
    the premises, evidence, and domains that produced the
    synthesized proposition.

    It does not produce final conclusions.
    """

    def __init__(
        self,
        *,
        semantic_generator,
    ):
        self.semantic_generator = semantic_generator

    def synthesize(
        self,
        *,
        premises: list[Premise],
        relationships: list[PremiseRelationship],
    ) -> list[SynthesizedProposition]:
        """
        Derive synthesized propositions from premises that
        have meaningful semantic relationships.
        """

        if len(premises) < 2:
            return []

        premise_by_id = {
            premise.premise_id: premise
            for premise in premises
        }

        relevant_relationships = [
            relationship
            for relationship in relationships
            if (
                relationship.kind
                not in {
                    PremiseRelationshipKind.INDEPENDENT,
                    PremiseRelationshipKind.UNRESOLVED,
                }
                and relationship.source_premise_id
                in premise_by_id
                and relationship.target_premise_id
                in premise_by_id
            )
        ]

        if not relevant_relationships:
            return []

        participating_ids: list[str] = []

        for relationship in relevant_relationships:
            for premise_id in (
                relationship.source_premise_id,
                relationship.target_premise_id,
            ):
                if premise_id not in participating_ids:
                    participating_ids.append(premise_id)

        participating_premises = [
            premise_by_id[premise_id]
            for premise_id in participating_ids
        ]

        if len(participating_premises) < 2:
            return []

        statement = self.semantic_generator.synthesize(
            premises=participating_premises,
            relationships=relevant_relationships,
        )

        if not statement or not statement.strip():
            return []

        evidence_ids: list[str] = []
        domain_ids: list[str] = []

        for premise in participating_premises:
            for evidence_id in premise.evidence_ids:
                if evidence_id not in evidence_ids:
                    evidence_ids.append(evidence_id)

            for domain_id in premise.domain_ids:
                if domain_id not in domain_ids:
                    domain_ids.append(domain_id)

        proposition = SynthesizedProposition(
            proposition_id=f"proposition-{uuid4()}",
            statement=statement.strip(),
            premise_ids=participating_ids,
            evidence_ids=evidence_ids,
            domain_ids=domain_ids,
            metadata={
                "relationship_kinds": [
                    relationship.kind.value
                    for relationship in relevant_relationships
                ],
            },
        )

        return [proposition]
