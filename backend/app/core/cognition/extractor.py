from collections.abc import Callable
from uuid import uuid4

from app.core.cognition.builder import build_cognitive_registry
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


DomainClassifier = Callable[[str], list[str]]

ConceptExtractor = Callable[
    [str, list[str], str],
    list[Concept],
]

PrincipleExtractor = Callable[
    [str, list[str], str],
    list[Principle],
]

RelationshipExtractor = Callable[
    [list[Concept], list[Principle], str],
    list[Relationship],
]

UnderstandingBuilder = Callable[
    [
        list[Concept],
        list[Principle],
        list[Relationship],
        list[str],
        str,
    ],
    list[Understanding],
]


def learn_from_text(
    *,
    text: str,
    source: str,
    classify_domains: DomainClassifier,
    extract_concepts: ConceptExtractor,
    extract_principles: PrincipleExtractor,
    extract_relationships: RelationshipExtractor,
    build_understandings: UnderstandingBuilder,
) -> CognitiveRegistry:
    """
    Coordinate one deterministic learning cycle from source text.

    Orchestrator responsibilities:

    - Record the source observation.
    - Establish a traceable evidence reference.
    - Coordinate domain classification.
    - Coordinate cognitive discovery.
    - Record the resulting Learning Event.
    - Return the assembled Cognitive Registry update.

    Orchestrator non-responsibilities:

    - Discovering concepts directly
    - Discovering principles directly
    - Inferring relationships directly
    - Performing validation
    - Rendering cognition
    - Persisting cognition
    - Mutating an existing registry
    """

    normalized_text = text.strip()
    normalized_source = source.strip()

    if not normalized_text:
        raise ValueError("Learning text must not be empty.")

    if not normalized_source:
        raise ValueError("Learning source must not be empty.")

    observation_id = f"observation-{uuid4()}"
    evidence_id = f"evidence-{uuid4()}"

    observation = Observation(
        observation_id=observation_id,
        source=normalized_source,
        content=normalized_text,
    )

    domain_ids = classify_domains(normalized_text)

    concepts = extract_concepts(
        normalized_text,
        domain_ids,
        evidence_id,
    )

    principles = extract_principles(
        normalized_text,
        domain_ids,
        evidence_id,
    )

    relationships = extract_relationships(
        concepts,
        principles,
        evidence_id,
    )

    understandings = build_understandings(
        concepts,
        principles,
        relationships,
        domain_ids,
        evidence_id,
    )

    supported_ids = [
        *(concept.concept_id for concept in concepts),
        *(principle.principle_id for principle in principles),
        *(relationship.relationship_id for relationship in relationships),
        *(
            understanding.understanding_id
            for understanding in understandings
        ),
    ]

    evidence = Evidence(
        evidence_id=evidence_id,
        title=f"Learning source: {normalized_source}",
        source=normalized_source,
        description=(
            "Traceable source evidence used during one cognitive "
            "learning cycle."
        ),
        supports=supported_ids,
        metadata={
            "observation_id": observation_id,
        },
    )

    learning_event = LearningEvent(
        source=normalized_source,
        domain_ids=domain_ids,
        observations_added=[observation.observation_id],
        evidence_added=[evidence.evidence_id],
        concepts_added=[
            concept.concept_id
            for concept in concepts
        ],
        principles_added=[
            principle.principle_id
            for principle in principles
        ],
        relationships_added=[
            relationship.relationship_id
            for relationship in relationships
        ],
        understandings_added=[
            understanding.understanding_id
            for understanding in understandings
        ],
        summary=(
            f"Sentinel completed one learning cycle from "
            f"'{normalized_source}'."
        ),
        metadata={
            "concept_count": len(concepts),
            "principle_count": len(principles),
            "relationship_count": len(relationships),
            "understanding_count": len(understandings),
        },
    )

    return build_cognitive_registry(
        observations=[observation],
        evidence=[evidence],
        concepts=concepts,
        principles=principles,
        relationships=relationships,
        understandings=understandings,
        learning_events=[learning_event],
    )
