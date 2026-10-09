from pathlib import Path

from app.core.canon.manifest import build_canon_manifest


REQUIRED_LAYERS = {
    "canon",
    "identity",
    "philosophy",
    "architecture",
    "engineering",
    "design",
    "history",
    "cognition",
}


def build_canon_report():
    """
    Evaluate the health of the SentinelAI Canon.
    """

    manifest = build_canon_manifest()

    layers = set(manifest["layers"].keys())

    missing_layers = sorted(REQUIRED_LAYERS - layers)

    warnings = []

    if missing_layers:
        warnings.append(
            f"Missing required layers: {', '.join(missing_layers)}"
        )

    if manifest["document_count"] == 0:
        warnings.append("No canonical documents discovered.")

    empty_documents = [document["name"] for document in manifest["documents"]
                       if not Path(document["path"]).read_text(encoding="utf-8").strip()]
    if empty_documents:
        warnings.append(f"{len(empty_documents)} principle documents contain no instructions.")

    status = "healthy"

    if warnings:
        status = "warning"

    return {
        "status": status,
        "document_count": manifest["document_count"],
        "layer_count": manifest["layer_count"],
        "layers": manifest["layers"],
        "types": manifest["types"],
        "warnings": warnings,
        "empty_documents": empty_documents,
    }
