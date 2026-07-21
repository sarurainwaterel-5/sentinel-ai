"""
Understanding Builder

Understanding is not extracted.

Understanding is built from concepts, principles, relationships,
domains, and evidence.

This module organizes cognition.

It does not discover it.
"""

from uuid import uuid4

from app.core.cognition.models import (
    Concept,
    Principle,
    Relationship,
    Understanding,
)


def build_understandings(
    concepts: list[Concept],
    principles: list[Principle],
    relationships: list[Relationship],
    domain_ids: list[str],
    evidence_id: str,
) -> list[Understanding]:
    """
    Build organized understanding from discovered cognitive objects.

    Builder responsibilities:

    - Organize concepts, principles, and relationships.
    - Produce explainable understanding.
    - Preserve traceability to domains and evidence.

    Builder non-responsibilities:

    - Discovering concepts
    - Discovering principles
    - Discovering relationships
    - Validating cognition
    - Rendering cognition
    - Persisting cognition
    """

    if not concepts and not principles and not relationships:
        return []

    concept_names = {
        concept.name.lower(): concept
        for concept in concepts
    }

    principle_statements = {
        principle.statement.lower(): principle
        for principle in principles
    }

    risk_management = concept_names.get("risk management")
    market_uncertainty = concept_names.get("market uncertainty")
    probability = concept_names.get("probability")

    probability_principle = principle_statements.get(
        "every trade begins with uncertainty."
    )

    longevity_principle = principle_statements.get(
        "risk management preserves longevity."
    )

    disciplined_probability_principle = principle_statements.get(
        "probability guides disciplined decision making."
    )

    understandings: list[Understanding] = []

    if (
        risk_management
        and market_uncertainty
        and probability_principle
    ):
        related_relationship_ids = [
            relationship.relationship_id
            for relationship in relationships
            if relationship.source_id
            in {
                risk_management.concept_id,
                probability_principle.principle_id,
            }
            or relationship.target_id
            in {
                market_uncertainty.concept_id,
                risk_management.concept_id,
            }
        ]

        understandings.append(
            Understanding(
                understanding_id=f"understanding-{uuid4()}",
                title="Trading requires disciplined uncertainty management",
                explanation=(
                    "Trading outcomes cannot be known with certainty. "
                    "Risk management organizes exposure so decisions can "
                    "remain disciplined under uncertainty."
                ),
                domain_ids=domain_ids,
                concept_ids=[
                    risk_management.concept_id,
                    market_uncertainty.concept_id,
                ],
                principle_ids=[
                    probability_principle.principle_id,
                ],
                relationship_ids=related_relationship_ids,
                evidence_ids=[evidence_id],
                confidence=0.85,
                metadata={
                    "builder": "deterministic",
                    "understanding_type": "risk_and_uncertainty",
                },
            )
        )

    if probability and disciplined_probability_principle:
        related_relationship_ids = [
            relationship.relationship_id
            for relationship in relationships
            if relationship.source_id
            == disciplined_probability_principle.principle_id
            or relationship.target_id == probability.concept_id
        ]

        understandings.append(
            Understanding(
                understanding_id=f"understanding-{uuid4()}",
                title="Trading decisions are probabilistic",
                explanation=(
                    "Disciplined trading decisions weigh available evidence "
                    "and express conclusions as probabilities rather than "
                    "certainty."
                ),
                domain_ids=domain_ids,
                concept_ids=[probability.concept_id],
                principle_ids=[
                    disciplined_probability_principle.principle_id,
                ],
                relationship_ids=related_relationship_ids,
                evidence_ids=[evidence_id],
                confidence=0.85,
                metadata={
                    "builder": "deterministic",
                    "understanding_type": "probabilistic_reasoning",
                },
            )
        )

    if risk_management and longevity_principle:
        related_relationship_ids = [
            relationship.relationship_id
            for relationship in relationships
            if relationship.source_id
            == longevity_principle.principle_id
            or relationship.target_id == risk_management.concept_id
        ]

        understandings.append(
            Understanding(
                understanding_id=f"understanding-{uuid4()}",
                title="Risk management preserves participation",
                explanation=(
                    "Risk management protects capital and preserves the "
                    "operator's ability to participate in future market "
                    "opportunities."
                ),
                domain_ids=domain_ids,
                concept_ids=[risk_management.concept_id],
                principle_ids=[longevity_principle.principle_id],
                relationship_ids=related_relationship_ids,
                evidence_ids=[evidence_id],
                confidence=0.9,
                metadata={
                    "builder": "deterministic",
                    "understanding_type": "capital_preservation",
                },
            )
        )

    return understandings
