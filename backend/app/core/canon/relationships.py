def make_edge(source: str, target: str, relationship: str) -> dict:
    """
    Create a graph relationship.
    """

    return {
        "source": source,
        "target": target,
        "relationship": relationship,
    }
