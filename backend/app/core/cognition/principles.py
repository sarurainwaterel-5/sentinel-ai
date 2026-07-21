from uuid import uuid4

from app.core.cognition.models import Principle


def extract_principles(
    text: str,
    domain_ids: list[str],
    evidence_id: str,
) -> list[Principle]:
    """
    Discover enduring principles from text.

    This implementation performs deterministic sentence matching.

    Future implementations may use semantic extraction while preserving
    this interface.
    """

    principles: list[Principle] = []

    catalog = {
        "every trade begins with uncertainty":
            "Every trade begins with uncertainty.",

        "risk management preserves longevity":
            "Risk management preserves longevity.",

        "probability matters":
            "Probability guides disciplined decision making.",
    }

    normalized = text.lower()

    for pattern, statement in catalog.items():

        if pattern in normalized:

            principles.append(
                Principle(
                    principle_id=f"principle-{uuid4()}",
                    name=statement,
                    statement=statement,
                    domain_ids=domain_ids,
                    evidence_ids=[evidence_id],
                )
            )

    return principles

# TODO (Sprint 8.x):
# Replace deterministic catalog with Domain Registry lookups.
#
# Cognition remains domain-agnostic.
# Operational Domains define concepts and principles.
