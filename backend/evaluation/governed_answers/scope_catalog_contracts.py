"""Offline authority/catalog capture and recheck contracts; no runtime wiring.

Identity and stores are explicitly scripted capabilities. These contracts do not
authenticate HTTP, mutate stores, retrieve vectors or authorize publication.
"""
import hashlib
import json
import math
import time
from dataclasses import dataclass, field
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Hash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
Name = Annotated[str, Field(min_length=1, max_length=200)]


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @model_validator(mode="after")
    def explicit_names(self):
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, str) and (not value.strip() or value in {"*", "all"}):
                raise ValueError("Explicit values are required.")
        return self


class EvidenceScope(_Record):
    organization_id: Name
    collection: Name
    module: Name
    topic: Name


class ScriptedIdentity(_Record):
    principal_id: Name
    execution_source: Literal["unit_test"] = "unit_test"


class AuthoritySnapshot(_Record):
    principal_id: Name
    permission_epoch: int = Field(ge=0)
    grants: tuple[EvidenceScope, ...] = Field(max_length=100)
    execution_source: Literal["unit_test"] = "unit_test"

    @model_validator(mode="after")
    def unique_grants(self):
        if len(self.grants) != len(set(g.model_dump_json() for g in self.grants)):
            raise ValueError("Duplicate grants.")
        return self


class DocumentVersion(_Record):
    document_id: Name
    scope: EvidenceScope
    state: Literal["pending", "indexed", "archiving", "archived", "restoring", "failed", "deleting", "tombstoned"]
    lifecycle_epoch: int = Field(ge=0)
    content_epoch: int = Field(ge=0)
    index_epoch: int = Field(ge=0)
    file_sha256: Hash
    chunk_hashes: tuple[Hash, ...] = Field(max_length=10000)


class CatalogSnapshot(_Record):
    scope: EvidenceScope
    revision: int = Field(ge=0)
    documents: tuple[DocumentVersion, ...] = Field(max_length=10000)
    execution_source: Literal["unit_test"] = "unit_test"

    @model_validator(mode="after")
    def unique_scoped_documents(self):
        if any(d.scope != self.scope for d in self.documents):
            raise ValueError("Catalog is outside requested scope.")
        if len(self.documents) != len({d.document_id for d in self.documents}):
            raise ValueError("Duplicate document identity.")
        return self


class EvidenceChunk(_Record):
    document_id: Name
    scope: EvidenceScope
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=100000)
    file_sha256: Hash
    lifecycle_epoch: int = Field(ge=0)
    content_epoch: int = Field(ge=0)
    index_epoch: int = Field(ge=0)


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _read(reader, model, **kwargs):
    if getattr(reader, "execution_source", None) != "unit_test":
        raise ValueError("Scripted reader required.")
    result = reader.read(**kwargs)
    if type(result) is not model:
        raise ValueError("Wrong snapshot type.")
    return model.model_validate_json(result.model_dump_json(), strict=True)


@dataclass(frozen=True)
class BoundContext:
    context_json: str
    context_sha256: str


@dataclass(frozen=True)
class EligibilityCheck:
    eligible_fixture: bool
    reason: str | None
    context: BoundContext | None = None
    execution_source: str = field(default="unit_test", init=False)
    authenticated_scope_verified: bool = field(default=False, init=False)
    release_authorized: bool = field(default=False, init=False)
    production_enabled: bool = field(default=False, init=False)
    proposition_to_inference: str = field(default="closed", init=False)


class OfflineEligibilityGuard:
    """Single-use request session. Denial is terminal; a bound handle is local.

    Double reads detect observed torn snapshots, not distributed linearizability.
    A successful checkpoint is not a publish barrier or production authorization.
    """
    def __init__(self, *, authority_reader, catalog_reader, timeout_seconds=3.0, clock=time.monotonic):
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 120:
            raise ValueError("Bounded finite timeout required.")
        self.authority_reader, self.catalog_reader = authority_reader, catalog_reader
        self.clock, self.timeout = clock, timeout_seconds
        self.started = self.last = self._now()
        self.bound = None
        self.terminal = None

    def _now(self):
        now = self.clock()
        if isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now) or now < 0 or (hasattr(self, "last") and now < self.last):
            raise ValueError("Invalid monotonic clock.")
        self.last = now
        return now

    def _deny(self, reason):
        self.terminal = self.terminal or reason
        return EligibilityCheck(False, self.terminal)

    def _deadline(self):
        return self._now() - self.started >= self.timeout

    def _snapshots(self, identity, scope):
        authority = _read(self.authority_reader, AuthoritySnapshot, identity=identity)
        if authority.principal_id != identity.principal_id or scope not in authority.grants:
            raise ValueError("Authority denied.")
        catalog = _read(self.catalog_reader, CatalogSnapshot, scope=scope)
        if catalog.scope != scope:
            raise ValueError("Wrong catalog scope.")
        if authority != _read(self.authority_reader, AuthoritySnapshot, identity=identity) or catalog != _read(self.catalog_reader, CatalogSnapshot, scope=scope):
            raise ValueError("Snapshot changed during capture.")
        return authority, catalog

    def capture(self, *, identity, scope, request_id, question, evidence):
        if self.terminal:
            return self._deny(self.terminal)
        if self.bound is not None:
            return self._deny("context_already_captured")
        try:
            if self._deadline():
                return self._deny("request_expired")
            if type(identity) is not ScriptedIdentity or type(scope) is not EvidenceScope:
                return self._deny("identity_or_scope_invalid")
            identity = ScriptedIdentity.model_validate_json(identity.model_dump_json(), strict=True)
            scope = EvidenceScope.model_validate_json(scope.model_dump_json(), strict=True)
            if not isinstance(request_id, str) or not request_id.strip() or len(request_id) > 200 or not isinstance(question, str) or not question.strip() or len(question) > 10000:
                return self._deny("request_invalid")
            authority, catalog = self._snapshots(identity, scope)
            if type(evidence) is not tuple or not 1 <= len(evidence) <= 25:
                return self._deny("evidence_budget_or_coverage_invalid")
            chunks = []
            documents = {d.document_id: d for d in catalog.documents}
            seen = set()
            for item in evidence:
                if type(item) is not EvidenceChunk:
                    return self._deny("evidence_invalid")
                chunk = EvidenceChunk.model_validate_json(item.model_dump_json(), strict=True)
                doc = documents.get(chunk.document_id)
                locator = (chunk.document_id, chunk.chunk_index)
                if locator in seen or chunk.scope != scope or doc is None:
                    return self._deny("evidence_scope_or_locator_invalid")
                seen.add(locator)
                if (doc.state != "indexed" or not doc.chunk_hashes or doc.content_epoch != doc.index_epoch
                        or any(getattr(doc, key) != getattr(chunk, key) for key in ("file_sha256", "lifecycle_epoch", "content_epoch", "index_epoch"))
                        or chunk.chunk_index >= len(doc.chunk_hashes) or hashlib.sha256(chunk.text.encode()).hexdigest() != doc.chunk_hashes[chunk.chunk_index]):
                    return self._deny("evidence_ineligible_or_stale")
                chunks.append(chunk.model_dump(mode="json"))
            data = {"schema_version": "scope-catalog-offline-v1", "request_id": request_id,
                "question": question, "identity": identity.model_dump(mode="json"), "scope": scope.model_dump(mode="json"),
                "authority": authority.model_dump(mode="json"), "catalog": catalog.model_dump(mode="json"), "evidence": chunks}
            if self._deadline():
                return self._deny("request_expired")
            serialized = _json(data)
            self.bound = BoundContext(serialized, hashlib.sha256(serialized.encode()).hexdigest())
            self._binding = (self.bound.context_json, self.bound.context_sha256)
            return EligibilityCheck(True, None, self.bound)
        except Exception:
            return self._deny("authority_catalog_or_context_unavailable")

    def recheck(self, context):
        if self.terminal:
            return self._deny(self.terminal)
        if context is not self.bound or self.bound is None:
            return self._deny("context_unbound")
        try:
            if (context.context_json, context.context_sha256) != self._binding:
                return self._deny("context_unbound")
            if self._deadline():
                return self._deny("request_expired")
            data = json.loads(context.context_json)
            identity = ScriptedIdentity.model_validate_json(_json(data["identity"]), strict=True)
            scope = EvidenceScope.model_validate_json(_json(data["scope"]), strict=True)
            authority, catalog = self._snapshots(identity, scope)
            if authority.model_dump(mode="json") != data["authority"] or catalog.model_dump(mode="json") != data["catalog"]:
                return self._deny("authority_or_catalog_changed")
            if self._deadline():
                return self._deny("request_expired")
            return EligibilityCheck(True, None, context)
        except Exception:
            return self._deny("authority_catalog_or_context_unavailable")
