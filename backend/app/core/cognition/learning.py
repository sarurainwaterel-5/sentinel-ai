"""
Learning Recorder

Learning does not create understanding.

Learning records the evolution of understanding.

Understanding answers:

    "What do I understand?"

Learning answers:

    "How did my understanding change?"
"""

from datetime import UTC, datetime

from app.core.cognition.models import (
    CognitiveRegistry,
    LearningEvent,
)


def record_learning(
    *,
    registry: CognitiveRegistry,
    source: str,
    summary: str,
) -> LearningEvent:
    """
    Record one completed learning cycle.

    Recorder responsibilities:

    - Preserve cognitive history.
    - Record changes to understanding.
    - Preserve evidence traceability.

    Recorder non-responsibilities:

    - Discovering cognition
    - Building understanding
    - Validation
    - Rendering
    - Persistence
    """

    return LearningEvent(
        source=source,
        domain_ids=sorted(
            {
                domain
                for understanding in registry.understandings
                for domain in understanding.domain_ids
            }
        ),
        observations_added=[
            observation.observation_id
            for observation in registry.observations
        ],
        evidence_added=[
            evidence.evidence_id
            for evidence in registry.evidence
        ],
        concepts_added=[
            concept.concept_id
            for concept in registry.concepts
        ],
        principles_added=[
            principle.principle_id
            for principle in registry.principles
        ],
        relationships_added=[
            relationship.relationship_id
            for relationship in registry.relationships
        ],
        understandings_added=[
            understanding.understanding_id
            for understanding in registry.understandings
        ],
        summary=summary,
        metadata={
            "recorded_at": datetime.now(UTC).isoformat(),
            "observation_count": len(registry.observations),
            "evidence_count": len(registry.evidence),
            "concept_count": len(registry.concepts),
            "principle_count": len(registry.principles),
            "relationship_count": len(registry.relationships),
            "understanding_count": len(registry.understandings),
        },
    )
