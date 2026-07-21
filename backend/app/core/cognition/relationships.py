from uuid import uuid4

from app.core.cognition.models import (
    Concept,
    Principle,
    Relationship,
)


def extract_relationships(
    concepts: list[Concept],
    principles: list[Principle],
    evidence_id: str,
) -> list[Relationship]:
    """
    Discover deterministic relationships between cognitive objects.

    Relationships organize understanding.

    This initial implementation uses known concept and principle names.
    Future implementations may use domain registries or semantic
    extraction without changing this interface.
    """

    relationships: list[Relationship] = []

    concepts_by_name = {
        concept.name.lower(): concept
        for concept in concepts
    }

    principles_by_statement = {
        principle.statement.lower(): principle
        for principle in principles
    }

    uncertainty = concepts_by_name.get("market uncertainty")
    risk_management = concepts_by_name.get("risk management")
    probability = concepts_by_name.get("probability")

    probability_principle = principles_by_statement.get(
        "every trade begins with uncertainty."
    )

    longevity_principle = principles_by_statement.get(
        "risk management preserves longevity."
    )

    disciplined_probability_principle = principles_by_statement.get(
        "probability guides disciplined decision making."
    )

    if risk_management and uncertainty:
        relationships.append(
            Relationship(
                relationship_id=f"relationship-{uuid4()}",
                source_id=risk_management.concept_id,
                predicate="manages",
                target_id=uncertainty.concept_id,
                evidence_ids=[evidence_id],
            )
        )

    if probability_principle and uncertainty:
        relationships.append(
            Relationship(
                relationship_id=f"relationship-{uuid4()}",
                source_id=probability_principle.principle_id,
                predicate="governs",
                target_id=uncertainty.concept_id,
                evidence_ids=[evidence_id],
            )
        )

    if disciplined_probability_principle and probability:
        relationships.append(
            Relationship(
                relationship_id=f"relationship-{uuid4()}",
                source_id=disciplined_probability_principle.principle_id,
                predicate="governs",
                target_id=probability.concept_id,
                evidence_ids=[evidence_id],
            )
        )

    if longevity_principle and risk_management:
        relationships.append(
            Relationship(
                relationship_id=f"relationship-{uuid4()}",
                source_id=longevity_principle.principle_id,
                predicate="governs",
                target_id=risk_management.concept_id,
                evidence_ids=[evidence_id],
            )
        )

    return relationships

