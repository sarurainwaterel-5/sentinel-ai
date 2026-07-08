from app.core.canon.manifest import build_canon_manifest
from app.core.canon.nodes import make_node
from app.core.canon.edges import make_layer_edge, make_type_edge


def build_canon_graph():
    """
    Build a deterministic graph of SentinelAI's Canon.

    This first version creates:
    - document nodes
    - layer nodes
    - type nodes
    - belongs_to edges
    - classified_as edges
    """

    manifest = build_canon_manifest()

    document_nodes = [
        make_node(document)
        for document in manifest["documents"]
    ]

    layer_nodes = [
        {
            "id": f"layer:{layer}",
            "title": layer.title(),
            "layer": "system",
            "type": "layer",
        }
        for layer in manifest["layers"].keys()
    ]

    type_nodes = [
        {
            "id": f"type:{doc_type}",
            "title": doc_type.replace("_", " ").title(),
            "layer": "system",
            "type": "document_type",
        }
        for doc_type in manifest["types"].keys()
    ]

    edges = []

    for node in document_nodes:
        edges.append(make_layer_edge(node))
        edges.append(make_type_edge(node))

    return {
        "name": "SentinelAI Canon Graph",
        "version": "1.0",
        "node_count": len(document_nodes) + len(layer_nodes) + len(type_nodes),
        "edge_count": len(edges),
        "nodes": document_nodes + layer_nodes + type_nodes,
        "edges": edges,
    }
