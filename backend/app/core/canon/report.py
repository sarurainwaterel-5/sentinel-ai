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
    }
