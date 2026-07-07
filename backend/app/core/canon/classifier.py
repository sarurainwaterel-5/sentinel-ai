from pathlib import Path


ROOT_FILE_TYPES = {
    "IDENTITY.md": "identity",
    "EVOLUTION.md": "evolution",
    "COGNITIVE_MODEL.md": "cognitive_model",
    "README.md": "index",
}


def classify_layer(path: Path) -> str:
    parts = path.parts

    if path.name == "README.md" and path.parent.name == "docs":
        return "canon"

    if "philosophy" in parts:
        return "philosophy"

    if "architecture" in parts:
        return "architecture"

    if "engineering" in parts:
        return "engineering"

    if "design" in parts:
        return "design"

    if "sprints" in parts:
        return "history"

    if path.name == "IDENTITY.md":
        return "identity"

    if path.name == "COGNITIVE_MODEL.md":
        return "cognition"

    if path.name == "EVOLUTION.md":
        return "history"

    return "general"


def classify_type(path: Path) -> str:
    name = path.name

    if name in ROOT_FILE_TYPES:
        return ROOT_FILE_TYPES[name]

    if name.startswith("ADR-"):
        return "architecture_decision"

    if name.startswith("Sprint-"):
        return "sprint_record"

    if name.endswith("_PRINCIPLES.md") or "PRINCIPLES" in name:
        return "principles"

    if "GUIDE" in name:
        return "guide"

    if "README" in name:
        return "index"

    if "MANIFESTO" in name:
        return "manifesto"

    if "VISION" in name:
        return "vision"

    if "OATH" in name:
        return "oath"

    if "MAP" in name:
        return "map"

    return "document"


def classify_document(path: Path) -> dict:
    return {
        "path": str(path),
        "name": path.name,
        "layer": classify_layer(path),
        "type": classify_type(path),
        "canonical": True,
    }
