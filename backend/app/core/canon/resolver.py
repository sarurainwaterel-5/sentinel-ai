from pathlib import Path

from app.core.canon.extractor import extract_document_signals
from app.core.canon.relationships import make_edge


def document_id_from_path(path: Path) -> str:
    """
    Convert a document path into the graph node id used by the Canon graph.
    """

    return path.stem


def infer_relationship(source_path: Path, target: str) -> str:
    """
    Infer a relationship based on the source document and target reference.
    """

    source_name = source_path.name.lower()

    if source_name.startswith("sprint-") and target.startswith("ADR-"):
        return "implements"

    if source_name.startswith("adr-"):
        return "extends"

    if "identity" in source_name:
        return "supports"

    return "references"


def resolve_document_relationships(path: Path) -> list[dict]:
    """
    Resolve relationship edges from extracted document signals.
    """

    source_id = document_id_from_path(path)
    signals = extract_document_signals(path)

    edges = []
 
    source_adr_prefix = "-".join(source_id.split("-")[:2])

    for adr in signals["adr_mentions"]:
        if adr != source_id and adr != source_adr_prefix:
            relationship = infer_relationship(path, adr)
            edges.append(make_edge(source_id, adr, relationship))

    for sprint in signals["sprint_mentions"]:
        if sprint != source_id:
            edges.append(make_edge(source_id, sprint, "mentions_sprint"))

    for link in signals["links"]:
        target = link["target"]

        if target.endswith(".md"):
            target_id = Path(target).stem
            relationship = infer_relationship(path, target_id)
            edges.append(make_edge(source_id, target_id, relationship))

    return edges
