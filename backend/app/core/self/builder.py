from pathlib import Path
from typing import Any

from app.core.self.discover import PROJECT_ROOT, discover_self_registry
from app.core.self.registry import SelfRegistry


VISION_DOCUMENT = PROJECT_ROOT / "docs" / "philosophy" / "VISION.md"
LANGUAGE_DOCUMENT = PROJECT_ROOT / "docs" / "design" / "SENTINEL_LANGUAGE.md"
TRIANGLE_DOCUMENT = PROJECT_ROOT / "docs" / "philosophy" / "SENTINEL_TRIANGLE.md"


def relative_source(path: Path) -> str:
    """
    Return a project-relative evidence path.
    """

    return str(path.relative_to(PROJECT_ROOT))


def build_identity(registry: SelfRegistry) -> None:
    """
    Add identity claims only when supporting project evidence exists.

    Builder organizes verified facts. It does not invent identity,
    services, capabilities, or operational claims.
    """

    registry.identity.name = "SentinelAI"

    if VISION_DOCUMENT.exists():
        registry.identity.category = "Intelligence Operating System"
        registry.identity.purpose = (
            "Create understanding from evidence across complex domains."
        )

        registry.add_evidence(
            evidence_type="identity_document",
            source=relative_source(VISION_DOCUMENT),
            description=(
                "Supports SentinelAI's declared identity, purpose, and "
                "long-term direction."
            ),
            metadata={
                "claims": [
                    "identity.category",
                    "identity.purpose",
                ]
            },
        )

    if LANGUAGE_DOCUMENT.exists():
        registry.identity.mission = (
            "Communicate clearly so operators can understand complex systems."
        )

        registry.add_evidence(
            evidence_type="design_document",
            source=relative_source(LANGUAGE_DOCUMENT),
            description=(
                "Supports SentinelAI's communication mission and "
                "operator-facing language."
            ),
            metadata={"claims": ["identity.mission"]},
        )

    if TRIANGLE_DOCUMENT.exists():
        registry.identity.principles = [
            {
                "name": "Protect the architecture",
                "status": "established",
            },
            {
                "name": "Refine the language",
                "status": "established",
            },
            {
                "name": "Honor the philosophy",
                "status": "established",
            },
            {
                "name": "Ground claims in evidence",
                "status": "established",
            },
        ]

        registry.add_evidence(
            evidence_type="philosophy_document",
            source=relative_source(TRIANGLE_DOCUMENT),
            description=(
                "Supports the principles used to evaluate SentinelAI's "
                "architecture, language, philosophy, and evidence."
            ),
            metadata={"claims": ["identity.principles"]},
        )


def build_knowledge_layers(registry: SelfRegistry) -> None:
    """
    Derive knowledge-layer counts from discovered Canon documents.
    """

    layer_counts: dict[str, int] = {}

    for document in registry.knowledge.documents:
        layer = document.get("layer", "unclassified")
        layer_counts[layer] = layer_counts.get(layer, 0) + 1

    registry.structure.knowledge_layers = [
        {
            "name": layer,
            "document_count": count,
        }
        for layer, count in sorted(layer_counts.items())
    ]


def build_self_registry() -> SelfRegistry:
    """
    Build SentinelAI's evidence-backed self-registry.

    Discovery observes reality.
    Builder organizes those observations into the Sentinel ontology.
    """

    registry = discover_self_registry()

    build_identity(registry)
    build_knowledge_layers(registry)

    return registry


def build_self_model() -> dict[str, Any]:
    """
    Return the serializable self-model used by validation,
    rendering, APIs, and future reasoning.
    """

    registry = build_self_registry()
    model = registry.to_dict()

    model["summary"] = {
        "workspace_count": len(registry.structure.workspaces),
        "route_count": len(registry.structure.routes),
        "knowledge_layer_count": len(
            registry.structure.knowledge_layers
        ),
        "document_count": len(registry.knowledge.documents),
        "relationship_count": len(
            registry.knowledge.relationships
        ),
        "evidence_count": len(registry.evidence),
    }

    return model
