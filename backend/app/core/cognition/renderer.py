from typing import Any

from app.core.cognition.models import CognitiveRegistry
from app.core.cognition.validator import (
    CognitiveValidationReport,
    validate_cognitive_registry,
)


class CognitiveRegistryValidationError(RuntimeError):
    """
    Raised when an invalid Cognitive Registry is rendered.
    """


def render_cognitive_model(
    registry: CognitiveRegistry,
    report: CognitiveValidationReport,
) -> dict[str, Any]:
    """
    Render SentinelAI's validated cognitive state.

    Renderer responsibilities:

    - Communicate cognitive state.
    - Expose validation results.
    - Preserve the supplied registry.

    Renderer non-responsibilities:

    - Building cognitive state
    - Repairing invalid objects
    - Extracting knowledge
    - Performing reasoning
    - Persisting cognition
    """

    if report.status == "invalid":
        raise CognitiveRegistryValidationError(
            "Cognitive Registry is invalid and cannot be rendered."
        )

    return {
        "summary": {
            "observations": len(registry.observations),
            "evidence": len(registry.evidence),
            "concepts": len(registry.concepts),
            "principles": len(registry.principles),
            "relationships": len(registry.relationships),
            "understandings": len(registry.understandings),
            "learning_events": len(registry.learning_events),
        },
        "validation": report.to_dict(),
        "observations": [
            observation.to_dict()
            for observation in registry.observations
        ],
        "evidence": [
            evidence.to_dict()
            for evidence in registry.evidence
        ],
        "concepts": [
            concept.to_dict()
            for concept in registry.concepts
        ],
        "principles": [
            principle.to_dict()
            for principle in registry.principles
        ],
        "relationships": [
            relationship.to_dict()
            for relationship in registry.relationships
        ],
        "understandings": [
            understanding.to_dict()
            for understanding in registry.understandings
        ],
        "learning_events": [
            event.to_dict()
            for event in registry.learning_events
        ],
    }


def build_and_render_cognitive_model(
    registry: CognitiveRegistry,
) -> dict[str, Any]:
    """
    Validate and render a supplied Cognitive Registry.

    This orchestration helper does not construct or modify cognition.
    """

    report = validate_cognitive_registry(registry)
    return render_cognitive_model(registry, report)
