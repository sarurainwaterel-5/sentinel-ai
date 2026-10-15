"""Deterministic synthetic backfill proposals, never storage/application authority.

Inputs only: dictionaries and in-memory bytes. No filesystem, settings, clients,
ORM, migration, authentication, content extraction or index verification.
"""
import hashlib
import json
import math
import re
from collections import Counter, defaultdict

from pydantic import Field, model_validator
from typing import Annotated, Literal

from .scope_catalog_contracts import EvidenceScope, Hash, _Record

Id = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")]
MAX_RECORDS = 100
MAX_CHUNKS = 2048
MAX_BYTES = 4 * 1024 * 1024


class Scope(EvidenceScope):
    @model_validator(mode="after")
    def exact(self):
        for value in self.model_dump().values():
            if value != value.strip() or value.casefold() == "all" or "*" in value or any(ord(c) < 32 for c in value):
                raise ValueError("Exact scope required.")
        return self


class Epochs(_Record):
    lifecycle_epoch: int = Field(ge=0, le=2**63-1)
    content_epoch: int = Field(ge=0, le=2**63-1)
    index_epoch: int = Field(ge=0, le=2**63-1)
    scope_revision: int = Field(ge=0, le=2**63-1)


class Prior(Epochs):
    scope: Scope
    tombstoned: bool = False
    file_sha256: Hash | None = None
    chunk_hashes: tuple[Hash, ...] | None = Field(default=None, max_length=128)


class IndexEvidence(_Record):
    state: Literal["unverified", "synthetic_complete"]
    lifecycle_epoch: int = Field(ge=0, le=2**63-1)
    content_epoch: int = Field(ge=0, le=2**63-1)
    manifest_sha256: Hash
    execution_source: Literal["unit_test"] = "unit_test"


class Record(Epochs):
    document_id: Id
    scope: Scope
    legacy_status: Literal["indexed", "archived", "pending", "error", "tombstoned"]
    file_sha256: Hash | None
    chunk_count: int = Field(ge=0, le=128)
    chunk_hashes: tuple[Hash, ...] = Field(max_length=128)
    prior: Prior | None = None
    index_evidence: IndexEvidence | None = None


class Mapping(_Record):
    document_id: Id
    scope: Scope
    file_fixture_id: Id


class Chunk(_Record):
    document_id: Id
    chunk_index: int = Field(ge=0, le=127)
    data: bytes | None = Field(default=None, repr=False)


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _policy():
    return {"version": "21-K-synthetic-backfill-v1", "scope": "exact-tuple-no-grants",
        "order": "sort-top-level-collections-preserve-chunk-locators-and-declared-hash-order",
        "identity": "global-id-not-content-digest", "index": "synthetic-only-never-indexed",
        "max_records": MAX_RECORDS, "max_mappings": 200, "max_chunks": MAX_CHUNKS,
        "max_total_bytes": MAX_BYTES, "max_file_bytes": 1048576, "max_chunk_bytes": 65536,
        "max_metadata_bytes": 1048576, "max_report_bytes": 1048576,
        "traversal_node_weight_bytes": 32, "max_nodes": 30000, "max_depth": 12}


def policy_sha256():
    return _sha(_canonical(_policy()).encode())


def _bounded_material(value, budget, depth=0):
    if len(budget) == 2:
        budget.append(0)
    budget[0] += 1
    budget[2] += 32  # bound traversal overhead before materializing JSON
    if budget[0] > 30000 or depth > 12 or budget[2] > 1048576:
        raise ValueError("input_limit_exceeded")
    if type(value) is bytes:
        budget[1] += len(value)
        if len(value) > 1048576 or budget[1] > MAX_BYTES:
            raise ValueError("input_limit_exceeded")
        return {"kind": "bytes", "sha256": _sha(value), "byte_length": len(value)}
    if value is None or type(value) is bool:
        return value
    if type(value) is str and len(value) <= 4096:
        budget[2] += len(value.encode())
        if budget[2] > 1048576:
            raise ValueError("input_limit_exceeded")
        return value
    if type(value) is int and abs(value) <= 2**63-1:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) in (tuple, list):
        if len(value) > MAX_CHUNKS:
            raise ValueError("input_limit_exceeded")
        return {"kind": "array", "value": [_bounded_material(v, budget, depth+1) for v in value]}
    if type(value) is dict:
        if len(value) > MAX_CHUNKS or any(type(k) is not str or len(k) > 200 for k in value):
            raise ValueError("input_malformed")
        budget[2] += sum(len(key.encode()) for key in value)
        if budget[2] > 1048576:
            raise ValueError("input_limit_exceeded")
        return {"kind": "object", "value": {k: _bounded_material(v, budget, depth+1) for k, v in value.items()}}
    raise ValueError("input_malformed")


def manifest_sha256(*, document_id, scope, file_sha256, content_epoch, chunks):
    """Hash already-computed ordered locator/hash/size rows, never real index data."""
    return _sha(_canonical({"document_id": document_id, "scope": scope,
        "file_sha256": file_sha256, "content_epoch": content_epoch, "chunks": chunks}).encode())


def plan_backfill(*, records, mappings, file_fixtures, chunk_fixtures,
                  expected_input_sha256=None, expected_policy_sha256=None):
    """Pure fixed-policy planner. Input collections are tuples of raw dictionaries.

    Malformed records quarantine without echoing validation inputs/errors. Envelope
    defects block the plan. All surviving rows remain pending or tombstoned.
    """
    input_hash = None
    policy_hash = policy_sha256()

    def finish(rows=(), errors=(), input_count=0):
        counts = dict(Counter(row["disposition"] for row in rows))
        report = {"schema_version": "21-K-backfill-plan-v1", "status": "blocked" if errors else "dry_run",
            "input_sha256": input_hash, "policy_sha256": policy_hash,
            "policy_version": _policy()["version"], "input_count": input_count,
            "row_count": len(rows), "counts": {key: counts.get(key, 0) for key in (
                "pending_verification", "quarantined", "retained_tombstone")},
            "errors": list(errors), "rows": sorted(rows, key=lambda row: (row["row_id"], _canonical(row))),
            "execution_source": "unit_test", "dry_run": True, "index_verified": False,
            "production_enabled": False, "release_authorized": False,
            "semantic_grounding_verified": False, "authenticated_scope_verified": False,
            "proposition_to_inference": "closed"}
        report["plan_sha256"] = _sha(_canonical(report).encode())
        if rows and len(_canonical(report).encode()) > 1048576:
            return finish(errors=("report_size_exceeded",), input_count=input_count)
        if rows:
            try:
                _bounded_material(report, [0, 0])
            except (ValueError, RecursionError, UnicodeError):
                return finish(errors=("report_size_exceeded",), input_count=input_count)
        return report

    try:
        if (type(records) is not tuple or len(records) > MAX_RECORDS or type(mappings) is not tuple
                or len(mappings) > 200 or type(chunk_fixtures) is not tuple or len(chunk_fixtures) > MAX_CHUNKS
                or type(file_fixtures) is not dict or len(file_fixtures) > 200):
            return finish(errors=("input_shape_or_limit_invalid",))
        if any(type(key) is not str or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", key) is None
               or (type(value) is not bytes and value is not None) for key, value in file_fixtures.items()):
            return finish(errors=("file_fixtures_malformed",))
        material = _bounded_material({"records": records, "mappings": mappings,
            "file_fixtures": file_fixtures, "chunk_fixtures": chunk_fixtures}, [0, 0])
        for key in ("records", "mappings", "chunk_fixtures"):
            material["value"][key]["value"].sort(key=_canonical)
        serialized = _canonical(material).encode()
        if len(serialized) > 1048576:
            return finish(errors=("input_limit_exceeded",))
        input_hash = _sha(serialized)
    except (ValueError, RecursionError, UnicodeError):
        return finish(errors=("input_malformed_or_limit_exceeded",))
    if expected_policy_sha256 is not None and (type(expected_policy_sha256) is not str or expected_policy_sha256 != policy_hash):
        return finish(errors=("policy_binding_mismatch",), input_count=len(records))
    if expected_input_sha256 is not None and (type(expected_input_sha256) is not str or expected_input_sha256 != input_hash):
        return finish(errors=("input_binding_mismatch",), input_count=len(records))

    # Never silently drop a malformed mapping/locator whose ownership is unclear.
    try:
        parsed_mappings = [Mapping.model_validate(m, strict=True) for m in mappings]
        parsed_chunks = [Chunk.model_validate(c, strict=True) for c in chunk_fixtures]
        if any(c.data is not None and len(c.data) > 65536 for c in parsed_chunks):
            return finish(errors=("chunk_size_exceeded",), input_count=len(records))
    except Exception:
        return finish(errors=("mapping_or_chunk_malformed",), input_count=len(records))
    ids = Counter(r.get("document_id") for r in records if type(r) is dict and type(r.get("document_id")) is str)
    if any(m.document_id not in ids for m in parsed_mappings) or any(c.document_id not in ids for c in parsed_chunks):
        return finish(errors=("orphan_mapping_or_chunk",), input_count=len(records))
    by_mapping, by_chunk = defaultdict(list), defaultdict(list)
    for m in parsed_mappings: by_mapping[m.document_id].append(m)
    for c in parsed_chunks: by_chunk[c.document_id].append(c)
    rows = []
    for raw in records:
        token = _sha(_canonical(_bounded_material(raw, [0, 0])).encode())
        row = {"row_id": token, "document_id": None, "disposition": "quarantined",
               "planned_state": "quarantined", "reasons": [], "index_verified": False}
        try:
            record = Record.model_validate_json(_canonical(raw), strict=True)
        except Exception:
            row["reasons"] = ["record_malformed"]
            rows.append(row)
            continue
        row.update(document_id=record.document_id, scope=record.scope.model_dump(),
            lifecycle_epoch=record.lifecycle_epoch, content_epoch=record.content_epoch,
            index_epoch=record.index_epoch, scope_revision=record.scope_revision,
            tombstone_retained=record.legacy_status == "tombstoned" or bool(record.prior and record.prior.tombstoned))
        reasons = []
        if ids[record.document_id] != 1: reasons.append("duplicate_identity")
        mapped = by_mapping[record.document_id]
        if len(mapped) != 1: reasons.append("mapping_missing_or_conflicting")
        elif mapped[0].scope != record.scope: reasons.append("scope_mapping_mismatch")
        if record.index_epoch > record.content_epoch: reasons.append("index_epoch_ahead")
        if record.prior:
            if record.prior.scope != record.scope: reasons.append("identity_scope_change_requires_transition")
            if any(getattr(record, k) < getattr(record.prior, k) for k in Epochs.model_fields):
                reasons.append("epoch_or_revision_regression")
            if record.prior.tombstoned and record.legacy_status != "tombstoned": reasons.append("tombstone_resurrection")
            if record.legacy_status == "tombstoned" and not record.prior.tombstoned and (
                    record.lifecycle_epoch <= record.prior.lifecycle_epoch or record.scope_revision <= record.prior.scope_revision):
                reasons.append("tombstone_transition_without_epoch_advance")
            if record.prior.index_epoch > record.prior.content_epoch: reasons.append("prior_epochs_invalid")
            if record.legacy_status != "tombstoned" and record.content_epoch == record.prior.content_epoch and (
                    record.prior.file_sha256 is not None and record.prior.file_sha256 != record.file_sha256
                    or record.prior.chunk_hashes is not None and record.prior.chunk_hashes != record.chunk_hashes):
                reasons.append("content_changed_without_epoch_advance")
            if record.content_epoch > record.prior.content_epoch and record.lifecycle_epoch <= record.prior.lifecycle_epoch:
                reasons.append("content_change_without_lifecycle_advance")
            if any(getattr(record, k) > getattr(record.prior, k) for k in ("lifecycle_epoch", "content_epoch", "index_epoch")) and record.scope_revision <= record.prior.scope_revision:
                reasons.append("changed_epoch_without_revision_advance")
        if row["tombstone_retained"]:
            row["planned_state"] = "tombstoned"
        if record.legacy_status == "tombstoned":
            if not reasons:
                row.update(disposition="retained_tombstone", planned_state="tombstoned")
            row["reasons"] = reasons
            rows.append(row)
            continue
        if reasons:
            row["reasons"] = sorted(set(reasons))
            rows.append(row)
            continue
        if record.legacy_status in {"archived", "error"}: reasons.append("legacy_record_not_eligible")
        file_bytes = file_fixtures.get(mapped[0].file_fixture_id) if len(mapped) == 1 else None
        if file_bytes is None: reasons.append("file_bytes_missing")
        else:
            digest = _sha(file_bytes)
            row.update(file_sha256=digest, file_byte_length=len(file_bytes))
            if not file_bytes: reasons.append("file_bytes_empty")
            if record.file_sha256 is None or record.file_sha256 != digest: reasons.append("file_hash_mismatch_or_missing")
        chunks = sorted(by_chunk[record.document_id], key=lambda c: c.chunk_index)
        complete = not (not record.chunk_count or len(record.chunk_hashes) != record.chunk_count
                or [c.chunk_index for c in chunks] != list(range(record.chunk_count)))
        if not complete:
            reasons.append("chunk_manifest_incomplete_or_duplicate")
        computed = []
        for c in chunks if complete else ():
            if c.data is None or not c.data:
                reasons.append("chunk_bytes_missing_or_empty")
                continue
            digest = _sha(c.data)
            computed.append({"chunk_index": c.chunk_index, "sha256": digest, "byte_length": len(c.data)})
            if c.chunk_index >= len(record.chunk_hashes) or record.chunk_hashes[c.chunk_index] != digest:
                reasons.append("chunk_hash_or_order_mismatch")
        manifest = manifest_sha256(document_id=record.document_id, scope=record.scope.model_dump(),
                                   file_sha256=record.file_sha256, content_epoch=record.content_epoch, chunks=computed)
        row.update(chunks=computed, manifest_sha256=manifest)
        index = record.index_evidence
        if index is None or index.state != "synthetic_complete": reasons.append("index_evidence_missing_or_unverified")
        elif (index.content_epoch != record.content_epoch or index.lifecycle_epoch != record.lifecycle_epoch
                or record.index_epoch != record.content_epoch or index.manifest_sha256 != manifest):
            reasons.append("index_evidence_stale_or_unbound")
        row["reasons"] = sorted(set(reasons))
        if not reasons:
            row.update(disposition="pending_verification", planned_state="pending",
                       reasons=["real_index_verification_required"])
        rows.append(row)
    # Equal digests are inspectable content facts, never document deduplication.
    content_counts = Counter(row.get("file_sha256") for row in rows if row.get("file_sha256"))
    for row in rows:
        row["equal_content_record_count"] = content_counts.get(row.get("file_sha256"), 0)
    return finish(rows, input_count=len(records))


def verify_plan(report, **inputs):
    """Recompute supplied-input/policy bindings, not authority or a signature."""
    if type(report) is not dict:
        return False
    try:
        _bounded_material(report, [0, 0])
        if len(_canonical(report).encode()) > 1048576:
            return False
        return _canonical(report) == _canonical(plan_backfill(**inputs))
    except Exception:
        return False
