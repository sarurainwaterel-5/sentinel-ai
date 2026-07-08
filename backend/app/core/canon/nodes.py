from pathlib import Path


def make_node(document: dict) -> dict:
    """
    Convert a classified Canon document into a graph node.
    """

    path = Path(document["path"])

    return {
        "id": path.stem,
        "title": path.stem.replace("-", " "),
        "path": document["path"],
        "layer": document["layer"],
        "type": document["type"],
    }
