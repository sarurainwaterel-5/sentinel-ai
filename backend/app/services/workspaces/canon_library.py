"""Read registered principle documents without permitting edits or arbitrary files."""
from pathlib import Path
from datetime import datetime, timezone
from app.core.canon.discovery import CANON_ROOT
from app.core.canon.classifier import classify_document
from app.core.canon.extractor import extract_title

MAX_DOCUMENT_BYTES = 1_000_000


def library_documents(root: Path = CANON_ROOT) -> list[dict]:
    root = root.resolve()
    documents = []
    for path in sorted(root.rglob("*.md")):
        resolved = path.resolve()
        if not resolved.is_relative_to(root) or not resolved.is_file():
            continue
        metadata = classify_document(path)
        title = path.stem
        if resolved.stat().st_size <= MAX_DOCUMENT_BYTES:
            title = extract_title(resolved.read_text(encoding="utf-8"), path.stem)
        documents.append({"path": path.relative_to(root).as_posix(), "name": path.name, "title": title,
                          "layer": metadata["layer"], "type": metadata["type"]})
    return documents


def read_library_document(path: str, root: Path = CANON_ROOT) -> dict:
    root = root.resolve()
    relative = Path(path)
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".md":
        raise ValueError("Invalid principle document path")
    resolved = (root / relative).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError("Invalid principle document path")
    registered = {document["path"]: document for document in library_documents(root)}
    if path not in registered:
        raise FileNotFoundError("Principle document not found")
    if resolved.stat().st_size > MAX_DOCUMENT_BYTES:
        raise ValueError("Principle document exceeds the reader size limit")
    return {**registered[path], "content": resolved.read_text(encoding="utf-8"), "read_only": True}


def observe_library() -> dict:
    return {"observed_at": datetime.now(timezone.utc).isoformat(), "documents": library_documents(), "read_only": True}
