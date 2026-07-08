
def make_layer_edge(node: dict) -> dict:
    """
    Connect a document node to its Canon layer.
    """

    return {
        "source": node["id"],
        "target": f"layer:{node['layer']}",
        "relationship": "belongs_to",
    }


def make_type_edge(node: dict) -> dict:
    """
    Connect a document node to its document type.
    """

    return {
        "source": node["id"],
        "target": f"type:{node['type']}",
        "relationship": "classified_as",
    }
