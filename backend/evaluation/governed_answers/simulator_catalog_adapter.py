"""Read-only synthetic snapshot bridge; no storage, retrieval or authority proof.

Snapshots and trusted external digests are supplied explicitly. Replacing a
snapshot models an observed fixture change, not a transactional publish barrier.
File bytes and ordered UTF-8 chunk bytes are independent synthetic fixtures;
matching their hashes does not prove that an index contains those chunks.
"""
import hashlib
import json

from pydantic import Field

from .lifecycle_simulator import LifecycleSimulator, digest
from .scope_catalog_contracts import (
    AuthoritySnapshot, CatalogSnapshot, DocumentVersion, EvidenceChunk,
    EvidenceScope, Name, ScriptedIdentity, _Record,
)


class DocumentByteFixture(_Record):
    document_id: Name
    scope: EvidenceScope
    file_bytes: bytes = Field(min_length=1, max_length=1048576)
    chunks: tuple[bytes, ...] = Field(min_length=1, max_length=32)


class _AuthorityReader:
    execution_source = "unit_test"

    def __init__(self, adapter):
        self._adapter = adapter

    def read(self, *, identity):
        self._adapter._current()
        if type(identity) is not ScriptedIdentity or identity.principal_id != self._adapter._authority.principal_id:
            raise ValueError("identity_denied")
        return AuthoritySnapshot.model_validate_json(self._adapter._authority.model_dump_json(), strict=True)


class _CatalogReader:
    execution_source = "unit_test"

    def __init__(self, adapter):
        self._adapter = adapter

    def read(self, *, scope):
        state = self._adapter._current()
        scope = self._adapter._scope(scope)
        revision = next((row["revision"] for row in state["scopes"] if row["scope"] == scope.model_dump()), None)
        if revision is None:
            raise ValueError("scope_unavailable")
        documents = tuple(DocumentVersion(document_id=row["document_id"], scope=scope,
            state=row["state"], lifecycle_epoch=row["lifecycle_epoch"],
            content_epoch=row["content_epoch"], index_epoch=row["index_epoch"],
            file_sha256=row["manifest"]["file_sha256"],
            chunk_hashes=tuple(chunk["sha256"] for chunk in row["manifest"]["chunks"]))
            for row in state["documents"] if row["scope"] == scope.model_dump())
        return CatalogSnapshot(scope=scope, revision=revision, documents=documents)


class SimulatorCatalogAdapter:
    """Serial fixture readers with explicit, externally anchored replacements.

    All catalog rows, including tombstones and pending versions, are retained.
    Replacements must extend the exact accepted journal prefix (or be identical).
    Invalid replacement poisons this instance; readers never serve its old state.
    Authority is a separately supplied synthetic grant, never inferred from rows.
    """
    execution_source = "unit_test"

    def __init__(self, *, state, expected_state_sha256, authority, byte_fixtures):
        self._state_json = None
        self._anchor = None
        self._blocked = False
        try:
            if type(authority) is not AuthoritySnapshot or type(byte_fixtures) is not tuple or len(byte_fixtures) > 16:
                raise ValueError()
            self._authority = AuthoritySnapshot.model_validate_json(authority.model_dump_json(), strict=True)
            fixtures = {}
            total = 0
            for fixture in byte_fixtures:
                if type(fixture) is not DocumentByteFixture:
                    raise ValueError()
                # Python validation preserves bytes; JSON serialization is not a
                # byte encoding protocol and must not normalize fixture content.
                fixture = DocumentByteFixture.model_validate(fixture.model_dump(), strict=True)
                if fixture.document_id in fixtures or any(type(chunk) is not bytes or not 1 <= len(chunk) <= 65536 for chunk in fixture.chunks):
                    raise ValueError()
                total += len(fixture.file_bytes) + sum(map(len, fixture.chunks))
                if total > 2097152:
                    raise ValueError()
                fixtures[fixture.document_id] = fixture
            self._fixtures = fixtures
            self._authority_sha256 = digest(self._authority.model_dump(mode="json"))
            self._fixtures_sha256 = digest([
                {"document_id": key, "scope": fixture.scope.model_dump(mode="json"),
                 "file_sha256": hashlib.sha256(fixture.file_bytes).hexdigest(),
                 "file_byte_length": len(fixture.file_bytes),
                 "chunks": [{"chunk_index": index, "sha256": hashlib.sha256(chunk).hexdigest(),
                             "byte_length": len(chunk)} for index, chunk in enumerate(fixture.chunks)]}
                for key, fixture in sorted(fixtures.items())])
            self.replace_snapshot(state=state, expected_state_sha256=expected_state_sha256)
            documents = {row["document_id"]: row for row in self._current()["documents"]}
            if any(key not in documents or fixture.scope.model_dump() != documents[key]["scope"] for key, fixture in fixtures.items()):
                raise ValueError()
            self.authority_reader = _AuthorityReader(self)
            self.catalog_reader = _CatalogReader(self)
        except Exception:
            self._state_json = None
            raise ValueError("adapter_inputs_invalid") from None

    def replace_snapshot(self, *, state, expected_state_sha256):
        previous = json.loads(self._state_json) if self._state_json is not None else None
        self._state_json = None
        self._anchor = None
        try:
            if self._blocked:
                raise ValueError()
            snapshot = LifecycleSimulator(state=state, expected_state_sha256=expected_state_sha256).snapshot()
            if snapshot is None:
                raise ValueError()
            if previous is not None and (len(snapshot["journal"]) < len(previous["journal"])
                    or snapshot["journal"][:len(previous["journal"])] != previous["journal"]):
                raise ValueError()
            self._state_json = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
            self._anchor = expected_state_sha256
            self._validated_sha256 = digest(snapshot)
        except Exception:
            self._state_json = None
            self._blocked = True
            raise ValueError("snapshot_invalid") from None

    def _current(self):
        if self._state_json is None:
            raise ValueError("snapshot_unavailable")
        # Full journal replay happens on every explicit installation. The
        # accepted canonical string has no caller-owned mutable references;
        # each read returns a fresh copy and checks its complete binding.
        try:
            snapshot = json.loads(self._state_json)
            if digest(snapshot) != self._validated_sha256 or snapshot["state_sha256"] != self._anchor:
                raise ValueError()
            return snapshot
        except Exception:
            self._state_json = None
            self._blocked = True
            raise ValueError("snapshot_invalid") from None

    def _scope(self, scope):
        if type(scope) is not EvidenceScope:
            raise ValueError("scope_invalid")
        scope = EvidenceScope.model_validate_json(scope.model_dump_json(), strict=True)
        if scope not in self._authority.grants:
            raise ValueError("scope_denied")
        return scope

    def evidence(self, *, scope, document_ids):
        try:
            state = self._current()
            scope = self._scope(scope)
            if type(document_ids) is not tuple or not 1 <= len(document_ids) <= 25 or any(type(key) is not str for key in document_ids) or len(set(document_ids)) != len(document_ids):
                raise ValueError()
            documents = {row["document_id"]: row for row in state["documents"]}
            evidence = []
            for key in document_ids:
                row, fixture = documents[key], self._fixtures[key]
                manifest = row["manifest"]
                if (row["scope"] != scope.model_dump() or fixture.scope != scope
                        or row["state"] != "indexed" or row["tombstoned"] or not row["fixture_eligible"]
                        or row["content_epoch"] != row["index_epoch"]
                        or hashlib.sha256(fixture.file_bytes).hexdigest() != manifest["file_sha256"]
                        or len(fixture.chunks) != manifest["chunk_count"]):
                    raise ValueError()
                for chunk, expected in zip(fixture.chunks, manifest["chunks"]):
                    if len(chunk) != expected["byte_length"] or hashlib.sha256(chunk).hexdigest() != expected["sha256"]:
                        raise ValueError()
                    text = chunk.decode("utf-8", errors="strict")
                    evidence.append(EvidenceChunk(document_id=key, scope=scope,
                        chunk_index=expected["chunk_index"], text=text,
                        file_sha256=manifest["file_sha256"], lifecycle_epoch=row["lifecycle_epoch"],
                        content_epoch=row["content_epoch"], index_epoch=row["index_epoch"]))
                    if len(evidence) > 25:
                        raise ValueError()
            return tuple(evidence)
        except Exception:
            raise ValueError("evidence_unavailable") from None

    def report(self):
        try:
            state = self._current()
        except Exception:
            state = None
        report = {"schema_version": "21-M-simulator-catalog-adapter-v1",
            "status": "valid_fixture" if state is not None else "blocked",
            "state_sha256": state["state_sha256"] if state else None,
            "authority_sha256": self._authority_sha256, "fixtures_sha256": self._fixtures_sha256,
            "execution_source": "unit_test", "index_verified": False,
            "authenticated_scope_verified": False, "semantic_grounding_verified": False,
            "production_enabled": False, "release_authorized": False,
            "proposition_to_inference": "closed"}
        report["input_sha256"] = digest({key: report[key] for key in ("state_sha256", "authority_sha256", "fixtures_sha256")})
        report["report_sha256"] = digest(report)
        return report
