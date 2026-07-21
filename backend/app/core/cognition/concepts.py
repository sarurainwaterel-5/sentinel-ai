from uuid import uuid4

from app.core.cognition.models import Concept


def extract_concepts(
    text: str,
    domain_ids: list[str],
    evidence_id: str,
) -> list[Concept]:
    """
    Discover reusable concepts from text.

    This initial implementation uses deterministic keyword matching.

    Future implementations may replace discovery with semantic or
    language-model-assisted extraction without changing the interface.
    """

    normalized = text.lower()

    concept_catalog = {
        "fair value gap": (
            "Fair Value Gap",
            "An imbalance created by displacement.",
        ),
        "displacement": (
            "Displacement",
            "Strong directional movement revealing institutional intent.",
        ),
        "risk management": (
            "Risk Management",
            "Disciplined control of trading risk.",
        ),
        "uncertainty": (
            "Market Uncertainty",
            "Market outcomes cannot be known with certainty.",
        ),
        "probability": (
            "Probability",
            "Likelihood of an outcome based upon available evidence.",
        ),
    }

    concepts: list[Concept] = []

    for keyword, (name, description) in concept_catalog.items():
        if keyword in normalized:
            concepts.append(
                Concept(
                    concept_id=f"concept-{uuid4()}",
                    name=name,
                    description=description,
                    domain_ids=domain_ids,
                    evidence_ids=[evidence_id],
                )
            )

    return concepts

# TODO (Sprint 8.x):
# Replace deterministic catalog with Domain Registry lookups.
#
# Cognition remains domain-agnostic.
# Operational Domains define concepts and principles.
