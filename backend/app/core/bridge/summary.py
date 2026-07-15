from app.core.canon.manifest import build_canon_manifest
from app.core.canon.report import build_canon_report
from app.core.canon.graph import build_canon_graph
from app.core.bridge.health import build_operational_health

def build_bridge_summary():
    """
    Build a high-level operational summary for the Bridge.

    The Bridge Summary translates SentinelAI's internal Canon,
    Graph, and Reflection systems into a single user-facing model.
    """

    manifest = build_canon_manifest()
    report = build_canon_report()
    graph = build_canon_graph()

    return {
    "status": report["status"],

    "canon": {
        "name": manifest["name"],
        "version": manifest["version"],
        "documents": manifest["document_count"],
        "layers": manifest["layer_count"],
        "types": manifest["types"],
        "health": report["status"],
        "warnings": report["warnings"],
    },

    "graph": {
        "name": graph["name"],
        "version": graph["version"],
        "nodes": graph["node_count"],
        "edges": graph["edge_count"],
        "relationships": graph["relationships"],
    },

    "reflection": {
        "status": report["status"],
        "message": (
            f"SentinelAI understands itself through "
            f"{manifest['document_count']} principle documents, "
            f"{manifest['layer_count']} knowledge layers, and "
            f"{graph['edge_count']} active connections."
        ),
        "warnings": report["warnings"],
    },

    "health": build_operational_health(),
}
