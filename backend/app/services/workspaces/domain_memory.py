"""Observe organization-scoped document counts without changing domain maturity."""
from datetime import datetime, timezone
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from app.models.document import Document


def observe_domain_memory(db: Session, organization_id: str = "default") -> dict:
    rows = db.execute(
        select(Document.module, Document.status, func.count(Document.id), func.sum(Document.chunk_count))
        .where(Document.organization_id == organization_id)
        .group_by(Document.module, Document.status)
    ).all()
    domains = {}
    for module, status, count, chunks in rows:
        stats = domains.setdefault(module or "unassigned", {"indexed_documents": 0, "archived_documents": 0, "other_documents": 0, "indexed_chunks": 0})
        if status == "indexed":
            stats["indexed_documents"] += count
            stats["indexed_chunks"] += chunks or 0
        elif status == "archived":
            stats["archived_documents"] += count
        else:
            stats["other_documents"] += count
    return {"organization_id": organization_id, "observed_at": datetime.now(timezone.utc).isoformat(), "domains": domains,
            "basis": "Document catalog counts. Indexed chunks are catalog records, not a live vector-integrity or semantic-accuracy assessment."}
