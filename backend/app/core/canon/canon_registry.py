from app.core.canon.canon_model import CanonManifest, CanonSource


def get_canon_manifest() -> CanonManifest:
    return CanonManifest(
        sources=[
            CanonSource(
                name="Identity",
                path="docs/IDENTITY.md",
                layer="identity",
                description="Defines who SentinelAI is."
            ),
            CanonSource(
                name="Evolution",
                path="docs/EVOLUTION.md",
                layer="history",
                description="Preserves the story of how SentinelAI evolved."
            ),
            CanonSource(
                name="Cognitive Model",
                path="docs/COGNITIVE_MODEL.md",
                layer="cognition",
                description="Defines how SentinelAI learns, recalls, reasons, reflects, and responds."
            ),
            CanonSource(
                name="Philosophy",
                path="docs/philosophy",
                layer="philosophy",
                description="Defines why SentinelAI exists and what principles guide it."
            ),
            CanonSource(
                name="Architecture",
                path="docs/architecture",
                layer="architecture",
                description="Defines how SentinelAI is structured and why major decisions were made."
            ),
            CanonSource(
                name="Design",
                path="docs/design",
                layer="experience",
                description="Defines how SentinelAI should feel to humans."
            ),
            CanonSource(
                name="Engineering",
                path="docs/engineering",
                layer="engineering",
                description="Defines how builders contribute to SentinelAI."
            ),
            CanonSource(
                name="Sprint History",
                path="docs/sprints",
                layer="evolution",
                description="Records the historical evolution of SentinelAI."
            ),
        ]
    )
