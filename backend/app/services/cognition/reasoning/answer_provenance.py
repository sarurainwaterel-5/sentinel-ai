"""Pure, offline provenance registry. No provider imports or content generation."""
import hashlib
import json
from dataclasses import dataclass
from app.services.cognition.reasoning.answer_models import EvidenceReference
from app.services.cognition.reasoning.models import EvidenceSource


@dataclass(frozen=True)
class ProvenanceRegistry:
    evidence: tuple[EvidenceReference, ...]
    rejection_reasons: tuple[str, ...]

    def excerpt(self, evidence_id: str, start: int, end: int) -> str:
        matches = [e for e in self.evidence if e.evidence_id == evidence_id]
        if len(matches) != 1 or type(start) is not int or type(end) is not int:
            raise ValueError("Unresolved excerpt reference.")
        text = matches[0].text
        if not 0 <= start < end <= len(text):
            raise ValueError("Excerpt bounds are invalid.")
        return text[start:end]


def build_registry(*, sources: list[EvidenceSource], snapshot_id: str,
                   organization_id: str, collection: str,
                   catalog: dict[str, dict], module: str | None = None,
                   topic: str | None = None) -> ProvenanceRegistry:
    """Catalog is a trusted caller-supplied snapshot, never generator metadata.

    Missing or inconsistent locators are excluded with visible bounded reasons.
    Identity ignores similarity and arbitrary metadata; duplicate conflicting
    content invalidates the entire registry rather than selecting one version.
    """
    if not snapshot_id.strip() or not organization_id.strip() or not collection.strip():
        raise ValueError("Explicit scope and snapshot are required.")
    if len(sources) > 25:
        raise ValueError("Registry exceeds retrieval bound.")
    records = {}
    reasons = []
    for source in sources:
        row = catalog.get(source.document_id)
        if not source.document_id or source.chunk_index is None or source.chunk_index < 0 or not source.text.strip():
            reasons.append("incomplete_locator")
            continue
        if not row or row.get("organization_id") != organization_id or row.get("collection") != collection:
            reasons.append("catalog_scope_mismatch")
            continue
        if source.organization_id != organization_id or source.collection != collection:
            reasons.append("source_scope_mismatch")
            continue
        if source.status != "indexed" or row.get("status") != "indexed":
            reasons.append("source_not_indexed")
            continue
        if source.module != row.get("module") or source.topic != row.get("topic"):
            reasons.append("catalog_metadata_mismatch")
            continue
        if source.file_hash != row.get("file_hash"):
            reasons.append("file_hash_mismatch")
            continue
        if (module and source.module != module) or (topic and source.topic != topic):
            reasons.append("retrieval_scope_mismatch")
            continue
        identity = (organization_id, collection, source.document_id, source.chunk_index)
        text_hash = hashlib.sha256(source.text.encode()).hexdigest()
        evidence_id = "evidence-" + hashlib.sha256(json.dumps(identity, separators=(",", ":")).encode()).hexdigest()
        record = EvidenceReference(evidence_id=evidence_id, snapshot_id=snapshot_id,
            document_id=source.document_id, organization_id=organization_id, collection=collection,
            chunk_index=source.chunk_index, text=source.text, text_sha256=text_hash,
            filename=source.filename, file_hash=source.file_hash, module=source.module,
            topic=source.topic, status=source.status)
        if identity in records and records[identity] != record:
            return ProvenanceRegistry((), ("ambiguous_source_identity",))
        records[identity] = record
    return ProvenanceRegistry(tuple(records[key] for key in sorted(records)), tuple(dict.fromkeys(reasons)))
