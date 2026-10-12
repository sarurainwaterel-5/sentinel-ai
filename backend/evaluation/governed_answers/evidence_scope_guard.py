"""Scripted evidence-scope/version checks; no production authentication or storage.

Readers and coordinator are supplied by offline tests. No retrieval, provider,
database, credentials, clients or runtime routes are imported or constructed.
"""
import hashlib
import json
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.services.cognition.reasoning.answer_models import AnswerScope
from app.services.cognition.reasoning.answer_orchestrator import OfflineAnswerCoordinator
from app.services.cognition.reasoning.answer_provenance import build_registry
from app.services.cognition.reasoning.models import EvidenceSource
from .presentation_guard import guard_fixture


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class _FixtureRecord(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class OperatorScopeFixture(_FixtureRecord):
    operator_id: str = Field(min_length=1, max_length=200)
    organization_id: str = Field(min_length=1, max_length=200)
    collection: str = Field(min_length=1, max_length=200)
    allowed_modules: tuple[str, ...] = Field(min_length=1, max_length=25)
    allowed_topics: tuple[str, ...] = Field(min_length=1, max_length=25)
    scope_epoch: int = Field(ge=0)
    execution_source: Literal["unit_test"] = "unit_test"

    @model_validator(mode="after")
    def explicit_scope(self):
        values = (self.operator_id, self.organization_id, self.collection,
                  *self.allowed_modules, *self.allowed_topics)
        if any(not value.strip() or value in {"*", "all"} for value in values):
            raise ValueError("Explicit fixture authority scope is required.")
        if len(set(self.allowed_modules)) != len(self.allowed_modules) or len(set(self.allowed_topics)) != len(self.allowed_topics):
            raise ValueError("Duplicate permissions are invalid.")
        return self


class CatalogDocumentFixture(_FixtureRecord):
    document_id: str = Field(min_length=1, max_length=200)
    organization_id: str = Field(min_length=1, max_length=200)
    collection: str = Field(min_length=1, max_length=200)
    module: str = Field(min_length=1, max_length=200)
    topic: str = Field(min_length=1, max_length=200)
    status: Literal["indexed", "archived", "pending", "error"]
    file_hash: str = Field(pattern=r"^[a-f0-9]{64}$")
    version_epoch: int = Field(ge=0)
    chunk_hashes: tuple[str, ...] = Field(min_length=1)

    @field_validator("chunk_hashes")
    @classmethod
    def hashes(cls, values):
        if any(len(value) != 64 or any(c not in "0123456789abcdef" for c in value) for value in values):
            raise ValueError("Exact chunk hashes are required.")
        return values

    @model_validator(mode="after")
    def no_blank_scope(self):
        if any(not value.strip() for value in (self.document_id, self.organization_id, self.collection, self.module, self.topic)):
            raise ValueError("Document identity/scope must not be blank.")
        return self


class CatalogSnapshotFixture(_FixtureRecord):
    revision: int = Field(ge=0)
    documents: tuple[CatalogDocumentFixture, ...]
    execution_source: Literal["unit_test"] = "unit_test"

    @model_validator(mode="after")
    def unique_documents(self):
        ids = [document.document_id for document in self.documents]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate catalog identities are invalid.")
        return self


@dataclass(frozen=True)
class ScopedFixturePresentation:
    report_json: str
    preview_allowed: bool
    rejection_reasons: tuple[str, ...]
    execution_source: str = field(default="unit_test", init=False)
    empirical_acceptance: bool = field(default=False, init=False)
    production_enabled: bool = field(default=False, init=False)
    release_authorized: bool = field(default=False, init=False)

    def to_component_report(self):
        return json.loads(self.report_json)


def _read(reader, model):
    if reader is None or getattr(reader, "execution_source", None) != "unit_test":
        raise ValueError("An explicitly scripted reader is required.")
    value = reader.read()
    if type(value) is not model:
        raise ValueError("Unexpected snapshot type.")
    return model.model_validate(value.model_dump(warnings="error"), strict=True)


def evaluate_scoped_fixture(*, question, scope, collection, sources, relationships,
                            authority_reader, catalog_reader, coordinator,
                            relevance_assessor=None):
    """Require explicit scripted authority and unchanged catalog around display.

    Global monotonic catalog revisions and document/scope epochs catch ABA changes
    in fixtures. This is not a real database transaction or live race guarantee.
    """
    context_digest = None
    catalog_revision = None

    def blocked(reason):
        payload = {"execution_source": "unit_test", "empirical_acceptance": False,
                   "public_response": None, "fixture_claim": None, "fixture_text": None,
                   "evidence_scope_guard": metadata(False, (reason,))}
        return ScopedFixturePresentation(_canonical(payload), False, (reason,))

    def metadata(passed, reasons=()):
        return {"schema_version": "21-E-evidence-scope-fixture-v1",
                "fixture_scope_checked": passed, "context_sha256": context_digest,
                "catalog_revision": catalog_revision, "rejection_reasons": list(reasons),
                "production_authenticated_scope_verified": False,
                "production_enabled": False, "release_authorized": False,
                "semantic_grounding_verified": False, "proposition_to_inference": "closed"}

    try:
        requested = AnswerScope.model_validate(scope.model_dump(warnings="error"), strict=True)
        if not isinstance(question, str) or not question.strip() or not requested.module or not requested.topic:
            return blocked("explicit_fixture_scope_required")
        authority = _read(authority_reader, OperatorScopeFixture)
    except Exception:
        return blocked("fixture_authority_unavailable_or_malformed")
    if (requested.organization_id != authority.organization_id or collection != authority.collection
            or requested.module not in authority.allowed_modules or requested.topic not in authority.allowed_topics):
        return blocked("fixture_scope_not_authorized")
    try:
        snapshot = _read(catalog_reader, CatalogSnapshotFixture)
        catalog_revision = snapshot.revision
    except Exception:
        return blocked("fixture_catalog_unavailable_or_malformed")
    try:
        if not isinstance(sources, (list, tuple)) or not sources or len(sources) > requested.limit:
            return blocked("fixture_source_budget_or_coverage_invalid")
        captured = [EvidenceSource.model_validate(source.model_dump(warnings="error"), strict=True) for source in sources]
        documents = {document.document_id: document for document in snapshot.documents}
        seen = set()
        for source in captured:
            document = documents.get(source.document_id)
            identity = (source.document_id, source.chunk_index)
            if identity in seen:
                return blocked("fixture_duplicate_source_locator")
            seen.add(identity)
            if document is None:
                return blocked("fixture_source_missing_from_catalog")
            if (document.organization_id != authority.organization_id or document.collection != collection
                    or document.module != requested.module or document.topic != requested.topic):
                return blocked("fixture_catalog_scope_mismatch")
            if (source.organization_id != authority.organization_id or source.collection != collection
                    or source.module != document.module or source.topic != document.topic):
                return blocked("fixture_source_scope_mismatch")
            if document.status != "indexed" or source.status != "indexed":
                return blocked("fixture_source_not_eligible")
            if source.file_hash != document.file_hash:
                return blocked("fixture_file_version_mismatch")
            if type(source.chunk_index) is not int or not 0 <= source.chunk_index < len(document.chunk_hashes):
                return blocked("fixture_chunk_locator_invalid")
            if not source.text.strip() or hashlib.sha256(source.text.encode()).hexdigest() != document.chunk_hashes[source.chunk_index]:
                return blocked("fixture_chunk_snapshot_mismatch")
        catalog = {d.document_id: {"organization_id": d.organization_id, "collection": d.collection,
                   "module": d.module, "topic": d.topic, "status": d.status, "file_hash": d.file_hash}
                   for d in snapshot.documents}
        context = {"question": question, "scope": requested.model_dump(), "collection": collection,
                   "authority": authority.model_dump(), "catalog": snapshot.model_dump(),
                   "sources": [source.model_dump() for source in captured]}
        context_digest = hashlib.sha256(_canonical(context).encode()).hexdigest()
        snapshot_id = "scoped-fixture-" + context_digest
        registry = build_registry(sources=captured, catalog=catalog, snapshot_id=snapshot_id,
                                  organization_id=authority.organization_id, collection=collection,
                                  module=requested.module, topic=requested.topic)
        if registry.rejection_reasons or len(registry.evidence) != len(captured):
            return blocked("fixture_incomplete_provenance")
        if type(coordinator) is not OfflineAnswerCoordinator:
            return blocked("fixture_coordinator_invalid")
        evaluation = coordinator.evaluate_fixture(question=question, sources=captured, catalog=catalog,
                        scope=requested, collection=collection, snapshot_id=snapshot_id,
                        relationships=relationships)
        if evaluation.public_response.scope != requested or evaluation.public_response.evidence != registry.evidence:
            return blocked("fixture_coordinator_snapshot_mismatch")
    except Exception:
        return blocked("fixture_snapshot_or_coordinator_failure")

    def unchanged():
        return (_read(authority_reader, OperatorScopeFixture) == authority
                and _read(catalog_reader, CatalogSnapshotFixture) == snapshot)

    try:
        if not unchanged():
            return blocked("fixture_authority_or_catalog_changed")
    except Exception:
        return blocked("fixture_final_snapshot_unavailable")
    guarded = guard_fixture(evaluation, assessor=relevance_assessor)
    try:
        if not unchanged():
            return blocked("fixture_authority_or_catalog_changed")
    except Exception:
        return blocked("fixture_final_snapshot_unavailable")
    report = guarded.to_component_report()
    report["evidence_scope_guard"] = metadata(True)
    return ScopedFixturePresentation(_canonical(report), guarded.preview_allowed,
                                    guarded.rejection_reasons)
