from collections import Counter

from app.core.canon.discovery import discover_documents
from app.core.canon.classifier import classify_document


def build_canon_manifest():
    """
    Build a structured manifest of SentinelAI's Canon.
    """

    discovered_documents = discover_documents()
    classified_documents = [
        classify_document(document)
        for document in discovered_documents
    ]

    layers = Counter(
        document["layer"]
        for document in classified_documents
    )

    types = Counter(
        document["type"]
        for document in classified_documents
    )

    return {
        "name": "SentinelAI Canon",
        "version": "1.0",
        "status": "healthy",
        "document_count": len(classified_documents),
        "layer_count": len(layers),
        "layers": dict(sorted(layers.items())),
        "types": dict(sorted(types.items())),
        "documents": classified_documents,
    }
