from collections.abc import Iterable

from app.core.cognition.models import (
    CognitiveRegistry,
    Concept,
    Evidence,
    LearningEvent,
    Observation,
    Principle,
    Relationship,
    Understanding,
)


def build_cognitive_registry(
    *,
    observations: Iterable[Observation] = (),
    evidence: Iterable[Evidence] = (),
    concepts: Iterable[Concept] = (),
    principles: Iterable[Principle] = (),
    relationships: Iterable[Relationship] = (),
    understandings: Iterable[Understanding] = (),
    learning_events: Iterable[LearningEvent] = (),
) -> CognitiveRegistry:
    """
    Construct SentinelAI's current cognitive registry.

    Builder responsibilities:

    - Assemble cognitive objects.
    - Preserve the supplied learning state.
    - Return one coherent cognitive representation.

    Builder non-responsibilities:

    - Validation
    - Extraction
    - Classification
    - Reasoning
    - Persistence
    - Deduplication
    """

    return CognitiveRegistry(
        observations=list(observations),
        evidence=list(evidence),
        concepts=list(concepts),
        principles=list(principles),
        relationships=list(relationships),
        understandings=list(understandings),
        learning_events=list(learning_events),
    )


def build_empty_cognitive_registry() -> CognitiveRegistry:
    """
    Construct an empty but valid cognitive registry.

    An empty registry means SentinelAI has not yet been supplied with
    cognitive objects. It does not imply failure.
    """

    return build_cognitive_registry()

