import re
from pathlib import Path
from typing import Any

from app.core.canon.graph import build_canon_graph
from app.core.canon.manifest import build_canon_manifest
from app.core.self.registry import SelfRegistry


BACKEND_ROOT = Path(__file__).resolve().parents[3]
PROJECT_ROOT = Path(__file__).resolve().parents[4]
FRONTEND_APP = PROJECT_ROOT / "frontend" / "src" / "App.jsx"

WORKSPACE_PATTERN = re.compile(
    r"^\s*([a-zA-Z][a-zA-Z0-9_]*)\s*:\s*<([A-Za-z][A-Za-z0-9]*)",
    re.MULTILINE,
)

WORKSPACE_LABELS = {
    "bridge": "The Bridge",
    "identity": "Identity",
    "teach": "Teach",
    "recall": "Recall",
    "reason": "Reason",
    "intelligence": "Intelligence",
    "governance": "Governance",
    "systems": "Systems",
}


def discover_routes() -> list[dict[str, Any]]:
    """
    Discover routes registered on the running FastAPI application.

    FastAPI's route registry is treated as runtime ground truth.
    """

    from app.main import app

    routes = []

    for route in app.routes:
        path = getattr(route, "path", None)
        methods = sorted(getattr(route, "methods", []) or [])

        if not path or path in {"/openapi.json", "/docs", "/docs/oauth2-redirect", "/redoc"}:
            continue

        routes.append(
            {
                "path": path,
                "methods": methods,
                "name": getattr(route, "name", ""),
            }
        )

    return sorted(
        routes,
        key=lambda route: (route["path"], route["methods"]),
    )


def discover_workspaces() -> list[dict[str, Any]]:
    """
    Discover frontend workspaces from the App.jsx workspace registry.
    """

    if not FRONTEND_APP.exists():
        return []

    content = FRONTEND_APP.read_text(encoding="utf-8")
    workspaces = []

    for workspace_id, component in WORKSPACE_PATTERN.findall(content):
        workspaces.append(
            {
                "id": workspace_id,
                "name": WORKSPACE_LABELS.get(
                    workspace_id,
                    workspace_id.replace("_", " ").title(),
                ),
                "component": component,
                "source": str(FRONTEND_APP.relative_to(PROJECT_ROOT)),
            }
        )

    return workspaces


def discover_knowledge() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """
    Discover Canon documents and graph relationships from existing builders.
    """

    manifest = build_canon_manifest()
    graph = build_canon_graph()

    documents = manifest.get("documents", [])
    relationships = graph.get("edges", [])

    return documents, relationships


def discover_self_registry() -> SelfRegistry:
    """
    Populate SentinelAI's self-registry from observable system evidence.

    This function records discovered facts only. It does not infer services,
    capabilities, identity claims, or unsupported responsibilities.
    """

    registry = SelfRegistry()

    registry.structure.routes = discover_routes()
    registry.structure.workspaces = discover_workspaces()

    documents, relationships = discover_knowledge()
    registry.knowledge.documents = documents
    registry.knowledge.relationships = relationships

    registry.add_evidence(
        evidence_type="runtime_registry",
        source="app.main:app",
        description="FastAPI runtime registry used to discover public routes.",
        metadata={"route_count": len(registry.structure.routes)},
    )

    registry.add_evidence(
        evidence_type="source_file",
        source=str(FRONTEND_APP.relative_to(PROJECT_ROOT)),
        description="Frontend workspace registry used to discover operator workspaces.",
        metadata={"workspace_count": len(registry.structure.workspaces)},
    )

    registry.add_evidence(
        evidence_type="generated_manifest",
        source="app.core.canon.manifest.build_canon_manifest",
        description="Canon manifest used to discover known documents.",
        metadata={"document_count": len(registry.knowledge.documents)},
    )

    registry.add_evidence(
        evidence_type="generated_graph",
        source="app.core.canon.graph.build_canon_graph",
        description="Canon graph used to discover explicit knowledge relationships.",
        metadata={"relationship_count": len(registry.knowledge.relationships)},
    )

    return registry
