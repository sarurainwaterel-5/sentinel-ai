"""Bounded synthetic lifecycle/outbox journal; no worker, storage or runtime I/O.

All changes are explicit expected-state operations. Restart replays the complete
supplied journal and compares every derived row to its externally bound snapshot.
Fixture eligibility is not index verification or permission to publish.
"""
import hashlib
import json
from collections import Counter
from typing import Literal

from pydantic import Field, model_validator

from .backfill_planner import Id, Scope, _bounded_material, manifest_sha256
from .scope_catalog_contracts import Hash, _Record

POLICY = {"version": "21-L-lifecycle-simulator-v1", "max_documents": 16,
    "max_events": 64, "max_steps": 256, "max_chunks": 32, "max_dispatches": 2,
    "max_snapshot_bytes": 524288, "dispatch": "single-flight-explicit-replay-only",
    "restore": "anchored-full-journal-replay", "scope_moves": "unsupported-deny",
    "replay_requires": "explicit-synthetic-abandoned-dispatch-transition"}


def _json(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def policy_sha256():
    return digest(POLICY)


class ChunkDigest(_Record):
    chunk_index: int = Field(ge=0, le=31)
    sha256: Hash
    byte_length: int = Field(ge=1, le=65536)


class Manifest(_Record):
    file_sha256: Hash
    chunk_count: int = Field(ge=1, le=32)
    chunks: tuple[ChunkDigest, ...] = Field(min_length=1, max_length=32)

    @model_validator(mode="after")
    def complete_ordered(self):
        if self.chunk_count != len(self.chunks) or [c.chunk_index for c in self.chunks] != list(range(self.chunk_count)):
            raise ValueError("Complete ordered manifest required.")
        return self


class Versions(_Record):
    lifecycle_epoch: int = Field(ge=1, le=2**63-1)
    content_epoch: int = Field(ge=1, le=2**63-1)
    index_epoch: int = Field(ge=0, le=2**63-1)


class Document(Versions):
    document_id: Id
    scope: Scope
    state: Literal["pending", "indexed", "archiving", "archived", "restoring", "failed", "tombstoned"]
    tombstoned: bool
    fixture_eligible: bool
    manifest: Manifest
    current_event_id: Id


class Receipt(_Record):
    event_id: Id
    document_id: Id
    scope: Scope
    lifecycle_epoch: int = Field(ge=1, le=2**63-1)
    content_epoch: int = Field(ge=1, le=2**63-1)
    index_epoch: int = Field(ge=0, le=2**63-1)
    manifest_sha256: Hash
    request_sha256: Hash
    outcome: Literal["success", "failure", "uncertain"]
    execution_source: Literal["unit_test"] = "unit_test"


class Event(_Record):
    event_id: Id
    command_id: Id
    document_id: Id
    scope: Scope
    kind: Literal["index", "cleanup"]
    command: Literal["create", "replace", "reindex", "archive", "restore", "delete"]
    lifecycle_epoch: int = Field(ge=1, le=2**63-1)
    content_epoch: int = Field(ge=1, le=2**63-1)
    expected_index_epoch: int = Field(ge=0, le=2**63-1)
    target_index_epoch: int = Field(ge=0, le=2**63-1)
    scope_revision: int = Field(ge=1, le=2**63-1)
    manifest_sha256: Hash
    request_sha256: Hash
    status: Literal["pending", "dispatched", "replay_ready", "acknowledged", "completed", "failed", "superseded"]
    dispatches: int = Field(ge=0, le=2)
    receipt: Receipt | None


class ScopeRevision(_Record):
    scope: Scope
    revision: int = Field(ge=1, le=2**63-1)


class Operation(_Record):
    expected_state_sha256: Hash


class Command(Operation):
    operation: Literal["create", "replace", "reindex", "archive", "restore", "delete"]
    command_id: Id
    event_id: Id
    document_id: Id
    scope: Scope
    expected_document_sha256: Hash | None
    expected_scope_revision: int = Field(ge=0, le=2**63-1)
    manifest: Manifest | None = None


class Dispatch(Operation):
    operation: Literal["dispatch"]
    event_id: Id
    expected_event_sha256: Hash
    replay: bool = False


class Acknowledge(Operation):
    operation: Literal["acknowledge"]
    event_id: Id
    expected_event_sha256: Hash
    receipt: Receipt


class Reconcile(Operation):
    operation: Literal["reconcile"]
    event_id: Id
    expected_event_sha256: Hash


class Recover(Operation):
    operation: Literal["recover"]
    event_id: Id
    expected_event_sha256: Hash
    prior_dispatch_stopped: bool

    @model_validator(mode="after")
    def stopped(self):
        if self.prior_dispatch_stopped is not True:
            raise ValueError("Explicit synthetic stopped dispatch required.")
        return self


class Snapshot(_Record):
    schema_version: Literal["21-L-state-v1"]
    policy_sha256: Hash
    documents: tuple[Document, ...] = Field(max_length=16)
    events: tuple[Event, ...] = Field(max_length=64)
    scopes: tuple[ScopeRevision, ...] = Field(max_length=16)
    journal: tuple[dict, ...] = Field(max_length=256)
    state_sha256: Hash
    execution_source: Literal["unit_test"] = "unit_test"
    index_verified: Literal[False] = False
    production_enabled: Literal[False] = False
    release_authorized: Literal[False] = False
    semantic_grounding_verified: Literal[False] = False
    authenticated_scope_verified: Literal[False] = False
    proposition_to_inference: Literal["closed"] = "closed"


class Denied(Exception):
    pass


def _seal(documents, events, scopes, journal):
    state = {"schema_version": "21-L-state-v1", "policy_sha256": policy_sha256(),
        "documents": sorted(documents, key=lambda d: d["document_id"]),
        "events": sorted(events, key=lambda e: e["event_id"]),
        "scopes": sorted(scopes, key=lambda s: _json(s["scope"])), "journal": journal,
        "execution_source": "unit_test", "index_verified": False, "production_enabled": False,
        "release_authorized": False, "semantic_grounding_verified": False,
        "authenticated_scope_verified": False, "proposition_to_inference": "closed"}
    state["state_sha256"] = digest(state)
    return state


def empty_state():
    """Explicit synthetic genesis, not fallback for missing/invalid state."""
    return _seal([], [], [], [])


def _bounded(value):
    _bounded_material(value, [0, 0])
    if len(_json(value).encode()) > 524288:
        raise Denied("state_or_operation_limit_exceeded")


def _parse(raw):
    _bounded(raw)
    if type(raw) is not dict:
        raise Denied("operation_malformed")
    kind = raw.get("operation")
    model = {"dispatch": Dispatch, "acknowledge": Acknowledge, "reconcile": Reconcile, "recover": Recover}.get(kind)
    if model is None:
        model = Command
    return model.model_validate_json(_json(raw), strict=True)


def _manifest(doc):
    return manifest_sha256(document_id=doc["document_id"], scope=doc["scope"],
        file_sha256=doc["manifest"]["file_sha256"], content_epoch=doc["content_epoch"],
        chunks=doc["manifest"]["chunks"])


def _request(event):
    return {key: value for key, value in event.items()
        if key not in {"status", "dispatches", "receipt", "request_sha256"}}


def _current(event, doc):
    return (doc["current_event_id"] == event["event_id"] and doc["scope"] == event["scope"]
        and all(doc[key] == event[key] for key in ("lifecycle_epoch", "content_epoch"))
        and doc["index_epoch"] == event["expected_index_epoch"] and _manifest(doc) == event["manifest_sha256"])


def _transition(state, op):
    data = op.model_dump(mode="json")
    documents = {d["document_id"]: json.loads(_json(d)) for d in state["documents"]}
    events = {e["event_id"]: json.loads(_json(e)) for e in state["events"]}
    scopes = {_json(s["scope"]): json.loads(_json(s)) for s in state["scopes"]}
    journal = list(state["journal"])
    if isinstance(op, Command):
        previous = next((a for a in journal if a.get("command_id") == op.command_id), None)
        if previous is not None:
            if previous == data:
                return state, "idempotent"
            raise Denied("conflicting_command_id")
    elif isinstance(op, Acknowledge) and op.event_id in events and events[op.event_id]["receipt"] is not None:
        if events[op.event_id]["receipt"] == data["receipt"]:
            return state, "idempotent"
        raise Denied("conflicting_acknowledgement")
    elif isinstance(op, Reconcile) and data in journal:
        return state, "idempotent"
    if state["state_sha256"] != op.expected_state_sha256:
        raise Denied("stale_expected_state")
    if len(journal) >= 256:
        raise Denied("step_limit_exceeded")

    if isinstance(op, Command):
        doc = documents.get(op.document_id)
        scope_key = _json(data["scope"])
        revision = scopes.get(scope_key, {}).get("revision", 0)
        if revision != op.expected_scope_revision or (digest(doc) if doc else None) != op.expected_document_sha256:
            raise Denied("stale_expected_document_or_scope")
        if op.event_id in events:
            raise Denied("duplicate_event_id")
        if len(events) >= 64:
            raise Denied("event_limit_exceeded")
        if op.operation == "create":
            if doc is not None:
                raise Denied("identity_already_exists")
            if len(documents) >= 16 or op.manifest is None:
                raise Denied("create_limit_or_manifest_invalid")
            doc = {"document_id": op.document_id, "scope": data["scope"], "lifecycle_epoch": 1,
                "content_epoch": 1, "index_epoch": 0, "tombstoned": False,
                "manifest": data["manifest"]}
        else:
            if doc is None or doc["scope"] != data["scope"]:
                raise Denied("document_or_scope_mismatch")
            if doc["tombstoned"]:
                raise Denied("tombstone_identity_retained")
            allowed = {"replace": {"pending", "indexed", "restoring", "failed"},
                "reindex": {"pending", "indexed", "restoring", "failed"},
                "archive": {"pending", "indexed", "restoring", "failed"},
                "restore": {"archived"}, "delete": {"pending", "indexed", "restoring", "failed", "archiving", "archived"}}
            if doc["state"] not in allowed[op.operation]:
                raise Denied("invalid_lifecycle_transition")
            if (op.operation == "replace") != (op.manifest is not None):
                raise Denied("unexpected_or_missing_manifest")
            doc["lifecycle_epoch"] += 1
            if op.operation == "replace":
                doc["content_epoch"] += 1
                doc["manifest"] = data["manifest"]
        doc.update(state={"archive": "archiving", "restore": "restoring", "delete": "tombstoned"}.get(op.operation, "pending"),
            tombstoned=op.operation == "delete", fixture_eligible=False, current_event_id=op.event_id)
        revision += 1
        scopes[scope_key] = {"scope": data["scope"], "revision": revision}
        event = {"event_id": op.event_id, "command_id": op.command_id, "document_id": op.document_id,
            "scope": data["scope"], "kind": "cleanup" if op.operation in {"archive", "delete"} else "index",
            "command": op.operation, "lifecycle_epoch": doc["lifecycle_epoch"], "content_epoch": doc["content_epoch"],
            "expected_index_epoch": doc["index_epoch"], "target_index_epoch": doc["index_epoch"] if op.operation in {"archive", "delete"} else doc["content_epoch"],
            "scope_revision": revision, "manifest_sha256": _manifest(doc),
            "status": "pending", "dispatches": 0, "receipt": None}
        event["request_sha256"] = digest(_request(event))
        documents[op.document_id], events[op.event_id] = doc, event
    else:
        event = events.get(op.event_id)
        if event is None or digest(event) != op.expected_event_sha256:
            raise Denied("event_missing_or_stale")
        doc = documents[event["document_id"]]
        current = _current(event, doc)
        if isinstance(op, Recover):
            if not current or event["status"] != "dispatched" or event["dispatches"] >= 2:
                raise Denied("recovery_not_allowed")
            event["status"] = "replay_ready"
        elif isinstance(op, Dispatch):
            if not current:
                raise Denied("event_superseded")
            if op.replay:
                if event["status"] != "replay_ready" or event["dispatches"] >= 2:
                    raise Denied("replay_not_allowed")
            elif event["status"] != "pending":
                raise Denied("explicit_replay_required")
            if any(e["event_id"] != op.event_id and e["status"] in {"dispatched", "replay_ready", "acknowledged"} for e in events.values()):
                raise Denied("concurrent_dispatch_forbidden")
            event.update(status="dispatched", dispatches=event["dispatches"]+1)
        elif isinstance(op, Acknowledge):
            if not current or event["status"] != "dispatched":
                raise Denied("acknowledgement_stale_or_not_dispatched")
            receipt = data["receipt"]
            expected = {"event_id": event["event_id"], "document_id": event["document_id"], "scope": event["scope"],
                "lifecycle_epoch": event["lifecycle_epoch"], "content_epoch": event["content_epoch"],
                "index_epoch": event["target_index_epoch"], "manifest_sha256": event["manifest_sha256"],
                "request_sha256": event["request_sha256"], "outcome": receipt["outcome"], "execution_source": "unit_test"}
            if receipt != expected:
                raise Denied("acknowledgement_unbound")
            event.update(status="acknowledged", receipt=receipt)
        else:
            if event["status"] in {"completed", "failed", "superseded"}:
                raise Denied("event_already_terminal")
            if not current:
                event["status"] = "superseded"
            elif event["status"] != "acknowledged":
                raise Denied("acknowledgement_required")
            else:
                success = event["receipt"]["outcome"] == "success"
                event["status"] = "completed" if success else "failed"
                if event["kind"] == "index":
                    doc.update(fixture_eligible=success, state="indexed" if success else "failed")
                    if success:
                        doc["index_epoch"] = event["target_index_epoch"]
                elif success and not doc["tombstoned"]:
                    doc["state"] = "archived"
                scope_key = _json(doc["scope"])
                scopes[scope_key]["revision"] += 1
    result = _seal(list(documents.values()), list(events.values()), list(scopes.values()), journal+[data])
    Snapshot.model_validate_json(_json(result), strict=True)
    _bounded(result)
    return result, "applied"


def _validate_state(raw, expected):
    _bounded(raw)
    parsed = Snapshot.model_validate_json(_json(raw), strict=True).model_dump(mode="json")
    if parsed["state_sha256"] != expected or parsed["policy_sha256"] != policy_sha256():
        raise Denied("state_binding_mismatch")
    without_hash = {key: value for key, value in parsed.items() if key != "state_sha256"}
    if digest(without_hash) != expected:
        raise Denied("state_binding_mismatch")
    rebuilt = empty_state()
    for operation in parsed["journal"]:
        rebuilt, status = _transition(rebuilt, _parse(operation))
        if status != "applied":
            raise Denied("journal_contains_nonmutation")
    if rebuilt != parsed:
        raise Denied("state_journal_inconsistent")
    return rebuilt


class LifecycleSimulator:
    """Serial explicit transitions; every snapshot must be externally anchored.

    No persistent checkpoint is read/written. A caller supplies snapshots on
    restart. Checksums detect substitution only against a trusted expected digest;
    they cannot authenticate a wholly rewritten journal and replacement anchor.
    """
    def __init__(self, *, state, expected_state_sha256):
        self._state_json = None
        self._reason = None
        try:
            self._state_json = _json(_validate_state(state, expected_state_sha256))
        except Denied as error:
            self._reason = str(error)
        except Exception:
            self._reason = "initial_state_malformed_or_limit_exceeded"

    def snapshot(self):
        return json.loads(self._state_json) if self._state_json else None

    def report(self, *, status=None, reason=None):
        state = self.snapshot()
        result = {"schema_version": "21-L-simulator-report-v1", "status": status or ("valid_fixture" if state else "blocked"),
            "reason": reason or self._reason, "state_sha256": state["state_sha256"] if state else None,
            "policy_sha256": policy_sha256(), "execution_source": "unit_test", "index_verified": False,
            "production_enabled": False, "release_authorized": False, "semantic_grounding_verified": False,
            "authenticated_scope_verified": False, "proposition_to_inference": "closed",
            "fixture_eligible_document_ids": [d["document_id"] for d in state["documents"] if d["fixture_eligible"]] if state else [],
            "event_counts": dict(sorted(Counter(e["status"] for e in state["events"]).items())) if state else {},
            "steps": len(state["journal"]) if state else 0}
        result["report_sha256"] = digest(result)
        return result

    def apply(self, operation):
        if self._state_json is None:
            return self.report(status="blocked")
        try:
            result, status = _transition(self.snapshot(), _parse(operation))
            serialized = _json(result)  # commit simulated catalog/outbox/journal together
            self._state_json = serialized
            return self.report(status=status)
        except Denied as error:
            return self.report(status="rejected", reason=str(error))
        except Exception:
            return self.report(status="rejected", reason="operation_malformed_or_limit_exceeded")
