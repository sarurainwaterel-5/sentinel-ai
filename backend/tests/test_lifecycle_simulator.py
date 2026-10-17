"""Deterministic synthetic reconciliation. No real worker/storage/index evidence."""
import copy
import hashlib

import pytest

from evaluation.governed_answers.lifecycle_simulator import (
    LifecycleSimulator, empty_state, digest,
)


SCOPE = dict(organization_id="org", collection="knowledge", module="engineering", topic="policy")


def manifest(seed=b"synthetic"):
    return dict(file_sha256=hashlib.sha256(seed).hexdigest(), chunk_count=2,
        chunks=[dict(chunk_index=i, sha256=hashlib.sha256(seed+bytes([i])).hexdigest(), byte_length=10+i) for i in range(2)])


def simulator(state=None):
    supplied = empty_state() if state is None else state
    return LifecycleSimulator(state=supplied, expected_state_sha256=supplied["state_sha256"])


def document(sim, document_id="doc"):
    return next((d for d in sim.snapshot()["documents"] if d["document_id"] == document_id), None)


def event(sim, event_id):
    return next(e for e in sim.snapshot()["events"] if e["event_id"] == event_id)


def command(sim, operation="create", *, cid="c1", eid="e1", did="doc", scope=None, content=None):
    scope = copy.deepcopy(scope or SCOPE)
    revision = next((s["revision"] for s in sim.snapshot()["scopes"] if s["scope"] == scope), 0)
    doc = document(sim, did)
    return dict(operation=operation, command_id=cid, event_id=eid, document_id=did, scope=scope,
        expected_state_sha256=sim.snapshot()["state_sha256"], expected_document_sha256=digest(doc) if doc else None,
        expected_scope_revision=revision, manifest=content if content is not None else manifest() if operation in {"create", "replace"} else None)


def operation(sim, kind, eid="e1", **extra):
    return dict(operation=kind, event_id=eid, expected_state_sha256=sim.snapshot()["state_sha256"],
        expected_event_sha256=digest(event(sim, eid)), **extra)


def receipt(sim, eid="e1", outcome="success"):
    e = event(sim, eid)
    return dict(event_id=eid, document_id=e["document_id"], scope=copy.deepcopy(e["scope"]),
        lifecycle_epoch=e["lifecycle_epoch"], content_epoch=e["content_epoch"], index_epoch=e["target_index_epoch"],
        manifest_sha256=e["manifest_sha256"], request_sha256=e["request_sha256"], outcome=outcome,
        execution_source="unit_test")


def applied(sim, action):
    report = sim.apply(action)
    assert report["status"] == "applied", report
    closed(report)
    return report


def closed(report):
    for key in ("production_enabled", "release_authorized", "semantic_grounding_verified", "authenticated_scope_verified", "index_verified"):
        assert report[key] is False
    assert report["execution_source"] == "unit_test" and report["proposition_to_inference"] == "closed"


def indexed(sim, eid="e1"):
    applied(sim, operation(sim, "dispatch", eid))
    applied(sim, operation(sim, "acknowledge", eid, receipt=receipt(sim, eid)))
    applied(sim, operation(sim, "reconcile", eid))


def rejected_without_mutation(sim, action):
    before = sim.snapshot()
    report = sim.apply(action)
    closed(report)
    assert report["status"] == "rejected", report
    assert sim.snapshot() == before
    return report


def test_indexing_is_fixture_eligibility_only_and_restart_is_exact():
    sim = simulator()
    applied(sim, command(sim))
    assert not document(sim)["fixture_eligible"] and event(sim, "e1")["status"] == "pending"
    indexed(sim)
    doc = document(sim)
    assert doc["fixture_eligible"] and doc["index_epoch"] == doc["content_epoch"] == 1
    assert sim.snapshot()["scopes"][0]["revision"] == 2
    restored = simulator(sim.snapshot())
    assert restored.snapshot() == sim.snapshot() and restored.report() == sim.report()
    closed(restored.report())


@pytest.mark.parametrize("operation_name", ["archive", "delete"])
def test_catalog_ineligible_before_cleanup_dispatch(operation_name):
    sim = simulator()
    applied(sim, command(sim))
    indexed(sim)
    applied(sim, command(sim, operation_name, cid="c2", eid="e2"))
    assert not document(sim)["fixture_eligible"] and event(sim, "e2")["status"] == "pending"
    assert document(sim)["lifecycle_epoch"] == 2
    indexed(sim, "e2")  # cleanup dispatch, fixture acknowledgement and reconciliation
    assert document(sim)["state"] == ("archived" if operation_name == "archive" else "tombstoned")
    assert not document(sim)["fixture_eligible"]


def test_archive_restore_preserves_content_but_requires_new_lifecycle_receipt():
    sim = simulator()
    applied(sim, command(sim))
    indexed(sim)
    original = copy.deepcopy(document(sim))
    applied(sim, command(sim, "archive", cid="c2", eid="e2"))
    indexed(sim, "e2")
    applied(sim, command(sim, "restore", cid="c3", eid="e3"))
    doc = document(sim)
    assert doc["content_epoch"] == doc["index_epoch"] == 1 and not doc["fixture_eligible"]
    assert doc["lifecycle_epoch"] == 3 and doc["manifest"] == original["manifest"]
    applied(sim, operation(sim, "dispatch", "e3"))
    wrong = receipt(sim, "e3")
    wrong["lifecycle_epoch"] = 1
    rejected_without_mutation(sim, operation(sim, "acknowledge", "e3", receipt=wrong))
    applied(sim, operation(sim, "acknowledge", "e3", receipt=receipt(sim, "e3")))
    applied(sim, operation(sim, "reconcile", "e3"))
    assert document(sim)["fixture_eligible"]


@pytest.mark.parametrize("op", ["create", "replace", "restore", "reindex", "archive", "delete"])
def test_tombstone_prevents_all_identity_reuse_or_resurrection(op):
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, command(sim, "delete", cid="c2", eid="e2"))
    rejected_without_mutation(sim, command(sim, op, cid="c3", eid="e3"))
    assert document(sim)["tombstoned"]
    assert simulator(sim.snapshot()).snapshot() == sim.snapshot()


@pytest.mark.parametrize("op", ["restore", "archive", "replace", "reindex", "delete"])
def test_missing_document_cannot_be_inferred(op):
    sim = simulator()
    rejected_without_mutation(sim, command(sim, op))


def test_same_content_distinct_scoped_identities_not_merged():
    sim = simulator()
    applied(sim, command(sim))
    other = {**SCOPE, "organization_id": "other"}
    applied(sim, command(sim, cid="c2", eid="e2", did="doc2", scope=other))
    assert len(sim.snapshot()["documents"]) == len(sim.snapshot()["scopes"]) == 2
    assert document(sim)["manifest"] == document(sim, "doc2")["manifest"]
    rejected_without_mutation(sim, command(sim, "replace", cid="c3", eid="e3", scope=other))


def test_duplicate_commands_are_noops_but_conflicting_ids_are_denied():
    sim = simulator()
    action = command(sim)
    applied(sim, action)
    before = sim.snapshot()
    assert sim.apply(action)["status"] == "idempotent" and sim.snapshot() == before
    conflicting = copy.deepcopy(action)
    conflicting["manifest"] = manifest(b"other")
    rejected_without_mutation(sim, conflicting)
    rejected_without_mutation(sim, command(sim, cid="c2", eid="e1", did="doc2"))


def test_duplicate_receipt_and_reconciliation_do_not_increment_versions():
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, operation(sim, "dispatch"))
    ack = operation(sim, "acknowledge", receipt=receipt(sim))
    applied(sim, ack)
    before = sim.snapshot()
    assert sim.apply(ack)["status"] == "idempotent" and sim.snapshot() == before
    conflict = operation(sim, "acknowledge", receipt=receipt(sim, outcome="failure"))
    rejected_without_mutation(sim, conflict)
    reconcile = operation(sim, "reconcile")
    applied(sim, reconcile)
    before = sim.snapshot()
    assert sim.apply(reconcile)["status"] == "idempotent" and sim.snapshot() == before


@pytest.mark.parametrize("field", ["lifecycle_epoch", "content_epoch", "index_epoch"])
def test_expected_document_digest_detects_stale_versions(field):
    sim = simulator()
    applied(sim, command(sim))
    action = command(sim, "replace", cid="c2", eid="e2")
    fake = copy.deepcopy(document(sim))
    fake[field] += 1
    action["expected_document_sha256"] = digest(fake)
    rejected_without_mutation(sim, action)


@pytest.mark.parametrize("kind", ["command", "dispatch", "recover", "acknowledge", "reconcile"])
def test_every_mutation_checks_expected_state(kind):
    sim = simulator()
    applied(sim, command(sim))
    if kind == "command": action = command(sim, "replace", cid="c2", eid="e2")
    elif kind == "dispatch": action = operation(sim, "dispatch")
    else:
        applied(sim, operation(sim, "dispatch"))
        if kind == "recover": action = operation(sim, "recover", prior_dispatch_stopped=True)
        elif kind == "acknowledge": action = operation(sim, "acknowledge", receipt=receipt(sim))
        else:
            applied(sim, operation(sim, "acknowledge", receipt=receipt(sim)))
            action = operation(sim, "reconcile")
    action["expected_state_sha256"] = "0"*64
    assert rejected_without_mutation(sim, action)["reason"] == "stale_expected_state"


@pytest.mark.parametrize("mode", ["state", "scope", "event"])
def test_wrong_scope_or_event_version_cannot_mutate(mode):
    sim = simulator()
    applied(sim, command(sim))
    if mode == "scope":
        action = command(sim, "replace", cid="c2", eid="e2")
        action["expected_scope_revision"] += 1
    else:
        action = operation(sim, "dispatch")
        action["expected_event_sha256" if mode == "event" else "expected_state_sha256"] = "0"*64
    rejected_without_mutation(sim, action)


@pytest.mark.parametrize("field", ["event_id", "document_id", "scope", "lifecycle_epoch", "content_epoch", "index_epoch", "manifest_sha256", "request_sha256", "execution_source", "outcome"])
def test_wrong_acknowledgement_binding_never_eligible(field):
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, operation(sim, "dispatch"))
    ack = receipt(sim)
    if field in {"event_id", "document_id"}: ack[field] = "other"
    elif field == "scope": ack[field] = {**SCOPE, "topic": "other"}
    elif field in {"lifecycle_epoch", "content_epoch", "index_epoch"}: ack[field] += 1
    elif field in {"manifest_sha256", "request_sha256"}: ack[field] = "0"*64
    elif field == "execution_source": ack[field] = "actual_api"
    else: ack[field] = "metadata-approved"
    rejected_without_mutation(sim, operation(sim, "acknowledge", receipt=ack))
    assert not document(sim)["fixture_eligible"]


@pytest.mark.parametrize("op", ["create", "replace"])
@pytest.mark.parametrize("mode", ["missing", "duplicate", "gap", "order", "count", "bad_hash", "raw_text"])
def test_manifests_are_complete_ordered_and_hash_only(op, mode):
    sim = simulator()
    if op == "replace": applied(sim, command(sim))
    action = command(sim, op, cid="new", eid="new")
    m = action["manifest"]
    if mode == "missing": action["manifest"] = None
    if mode == "duplicate": m["chunks"][1]["chunk_index"] = 0
    if mode == "gap": m["chunks"][1]["chunk_index"] = 2
    if mode == "order": m["chunks"].reverse()
    if mode == "count": m["chunk_count"] = 3
    if mode == "bad_hash": m["file_sha256"] = "bad"
    if mode == "raw_text": m["contents"] = "do-not-expose-private-content"
    report = rejected_without_mutation(sim, action)
    assert "do-not-expose" not in str(report)


@pytest.mark.parametrize("outcome", ["failure", "uncertain"])
@pytest.mark.parametrize("cleanup", [False, True])
def test_failed_or_uncertain_indexing_and_cleanup_remain_ineligible(outcome, cleanup):
    sim = simulator()
    applied(sim, command(sim))
    eid = "e1"
    if cleanup:
        indexed(sim)
        applied(sim, command(sim, "archive", cid="c2", eid="e2"))
        eid = "e2"
    applied(sim, operation(sim, "dispatch", eid))
    applied(sim, operation(sim, "acknowledge", eid, receipt=receipt(sim, eid, outcome)))
    applied(sim, operation(sim, "reconcile", eid))
    assert event(sim, eid)["status"] == "failed" and not document(sim)["fixture_eligible"]
    assert document(sim)["state"] == ("archiving" if cleanup else "failed")
    rejected_without_mutation(sim, operation(sim, "dispatch", eid, replay=True))


@pytest.mark.parametrize("window", ["before_dispatch", "after_dispatch", "after_acknowledgement", "after_reconciliation"])
def test_restart_crash_windows_require_explicit_bounded_work(window):
    sim = simulator()
    applied(sim, command(sim))
    if window != "before_dispatch": applied(sim, operation(sim, "dispatch"))
    saved_receipt = receipt(sim)
    if window in {"after_acknowledgement", "after_reconciliation"}:
        applied(sim, operation(sim, "acknowledge", receipt=saved_receipt))
    if window == "after_reconciliation": applied(sim, operation(sim, "reconcile"))
    snapshot = sim.snapshot()
    sim = simulator(snapshot)
    assert sim.snapshot() == snapshot  # restart itself schedules nothing
    if window == "before_dispatch": applied(sim, operation(sim, "dispatch"))
    if window == "after_dispatch":
        rejected_without_mutation(sim, operation(sim, "dispatch"))
        rejected_without_mutation(sim, operation(sim, "dispatch", replay=True))
        applied(sim, operation(sim, "recover", prior_dispatch_stopped=True))
        request = event(sim, "e1")["request_sha256"]
        applied(sim, operation(sim, "dispatch", replay=True))
        assert event(sim, "e1")["dispatches"] == 2 and event(sim, "e1")["request_sha256"] == request
        rejected_without_mutation(sim, operation(sim, "dispatch", replay=True))
    if window in {"before_dispatch", "after_dispatch"}:
        applied(sim, operation(sim, "acknowledge", receipt=saved_receipt))
    if window != "after_reconciliation": applied(sim, operation(sim, "reconcile"))
    assert document(sim)["fixture_eligible"]


@pytest.mark.parametrize("next_op", ["replace", "archive", "delete"])
def test_reordered_or_late_completions_are_rejected_and_explicitly_superseded(next_op):
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, operation(sim, "dispatch"))
    stale = receipt(sim)
    applied(sim, command(sim, next_op, cid="c2", eid="e2"))
    rejected_without_mutation(sim, operation(sim, "acknowledge", receipt=stale))
    rejected_without_mutation(sim, operation(sim, "dispatch", "e2"))
    applied(sim, operation(sim, "reconcile", "e1"))
    assert event(sim, "e1")["status"] == "superseded" and not document(sim)["fixture_eligible"]
    indexed(sim, "e2")
    rejected_without_mutation(sim, operation(sim, "acknowledge", "e1", receipt=stale))
    assert document(sim)["fixture_eligible"] is (next_op == "replace")


def test_unreconciled_old_ack_does_not_promote_after_archive():
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, operation(sim, "dispatch"))
    applied(sim, operation(sim, "acknowledge", receipt=receipt(sim)))
    applied(sim, command(sim, "archive", cid="c2", eid="e2"))
    applied(sim, operation(sim, "reconcile", "e1"))
    assert not document(sim)["fixture_eligible"] and event(sim, "e1")["status"] == "superseded"


@pytest.mark.parametrize("mode", ["null", "missing", "duplicate_document", "duplicate_event", "orphan_event", "invalid_epoch", "wrong_scope_revision", "incomplete_manifest", "tampered_receipt", "forged_eligibility", "forged_authority", "duplicate_journal"])
def test_initial_and_restored_snapshots_are_validated_by_complete_replay(mode):
    sim = simulator()
    applied(sim, command(sim))
    indexed(sim)
    raw = sim.snapshot()
    if mode == "null": raw = None
    elif mode == "missing": del raw["journal"]
    elif mode == "duplicate_document": raw["documents"] *= 2
    elif mode == "duplicate_event": raw["events"] *= 2
    elif mode == "orphan_event": raw["events"][0]["document_id"] = "missing"
    elif mode == "invalid_epoch": raw["documents"][0]["index_epoch"] = 99
    elif mode == "wrong_scope_revision": raw["scopes"][0]["revision"] = 99
    elif mode == "incomplete_manifest": raw["documents"][0]["manifest"]["chunks"].pop()
    elif mode == "tampered_receipt": raw["events"][0]["receipt"]["request_sha256"] = "0"*64
    elif mode == "forged_eligibility": raw["documents"][0]["fixture_eligible"] = False
    elif mode == "forged_authority": raw["production_enabled"] = True
    else: raw["journal"].append(copy.deepcopy(raw["journal"][0]))
    if raw is not None:
        raw["state_sha256"] = digest({k: v for k, v in raw.items() if k != "state_sha256"})
    restored = LifecycleSimulator(state=raw, expected_state_sha256=raw["state_sha256"] if raw else "0"*64)
    report = restored.report()
    closed(report)
    assert report["status"] == "blocked" and restored.snapshot() is None
    assert restored.apply({})["status"] == "blocked"


def test_external_snapshot_anchor_detects_substitution():
    initial = empty_state()
    sim = simulator(initial)
    applied(sim, command(sim))
    restored = LifecycleSimulator(state=sim.snapshot(), expected_state_sha256=initial["state_sha256"])
    assert restored.report()["status"] == "blocked"


def test_replay_is_deterministic_and_caller_cannot_mutate_internal_state():
    a, b = simulator(), simulator()
    for sim in (a, b):
        applied(sim, command(sim))
        indexed(sim)
        applied(sim, command(sim, "replace", cid="c2", eid="e2", content=manifest(b"new")))
        indexed(sim, "e2")
    assert a.snapshot() == b.snapshot() and a.report() == b.report()
    leaked = a.snapshot()
    leaked["documents"][0]["fixture_eligible"] = False
    assert document(a)["fixture_eligible"] and document(a)["content_epoch"] == 2


@pytest.mark.parametrize("field", ["release_authorized", "authenticated_scope_verified", "semantic_grounding_verified", "metadata"])
def test_operation_metadata_cannot_certify_any_authority(field):
    sim = simulator()
    action = command(sim)
    action[field] = True
    rejected_without_mutation(sim, action)


@pytest.mark.parametrize("bad", [None, [], {"operation": "fallback"}, {"operation": "create", "raw": "x"*5000}])
def test_malformed_or_oversized_operations_are_bounded(bad):
    sim = simulator()
    report = rejected_without_mutation(sim, bad)
    assert len(str(report)) < 1500


def test_document_limit_is_atomic_and_does_not_partially_insert_event():
    sim = simulator()
    for i in range(16):
        applied(sim, command(sim, cid=f"c{i}", eid=f"e{i}", did=f"doc{i}"))
    rejected_without_mutation(sim, command(sim, cid="c17", eid="e17", did="doc17"))
    assert len(sim.snapshot()["documents"]) == len(sim.snapshot()["events"]) == 16


def test_simulator_does_not_read_files_environment_or_dispatch_services(monkeypatch):
    import builtins
    import os
    import socket
    import subprocess
    from pathlib import Path
    sim = simulator()
    def forbidden(*args, **kwargs): raise AssertionError("No I/O permitted")
    with monkeypatch.context() as patch:
        for obj, name in ((builtins, "open"), (os, "getenv"), (socket, "socket"), (subprocess, "Popen"), (Path, "glob")):
            patch.setattr(obj, name, forbidden)
        applied(sim, command(sim))
        indexed(sim)
        restored = simulator(sim.snapshot())
    assert restored.snapshot() == sim.snapshot()


def test_failure_before_atomic_commit_leaves_both_catalog_and_outbox_unchanged(monkeypatch):
    from evaluation.governed_answers import lifecycle_simulator as module
    sim = simulator()
    action = command(sim)
    def crash(*args, **kwargs): raise RuntimeError("private injected failure")
    with monkeypatch.context() as patch:
        patch.setattr(module, "_seal", crash)
        report = rejected_without_mutation(sim, action)
    assert "private injected" not in str(report)
    assert sim.snapshot()["documents"] == sim.snapshot()["events"] == []
    applied(sim, action)


def test_crash_after_catalog_commit_before_response_can_repeat_identical_command():
    sim = simulator()
    action = command(sim)
    applied(sim, action)  # response is notionally lost; checkpoint survives
    saved = sim.snapshot()
    restarted = simulator(saved)
    assert restarted.apply(action)["status"] == "idempotent"
    assert restarted.snapshot() == saved and len(saved["events"]) == 1


@pytest.mark.parametrize("start,op", [("pending", "restore"), ("indexed", "restore"), ("failed", "restore"),
    ("archiving", "restore"), ("archiving", "replace"), ("archiving", "reindex"), ("archiving", "archive"),
    ("archived", "replace"), ("archived", "reindex"), ("archived", "archive")])
def test_invalid_transition_matrix_is_not_repaired_by_fallback(start, op):
    sim = simulator()
    applied(sim, command(sim))
    if start in {"indexed", "archiving", "archived"}: indexed(sim)
    if start == "failed":
        applied(sim, operation(sim, "dispatch"))
        applied(sim, operation(sim, "acknowledge", receipt=receipt(sim, outcome="failure")))
        applied(sim, operation(sim, "reconcile"))
    if start in {"archiving", "archived"}:
        applied(sim, command(sim, "archive", cid="c2", eid="e2"))
        if start == "archived": indexed(sim, "e2")
    assert document(sim)["state"] == start
    rejected_without_mutation(sim, command(sim, op, cid="new", eid="new"))


@pytest.mark.parametrize("field", ["organization_id", "collection", "module", "topic"])
def test_four_field_scope_boundary_disallows_implicit_moves(field):
    sim = simulator()
    applied(sim, command(sim))
    rejected_without_mutation(sim, command(sim, "replace", cid="c2", eid="e2", scope={**SCOPE, field: "foreign"}))


@pytest.mark.parametrize("value", ["*", "all", "ALL", " org"])
def test_nonexplicit_scope_is_rejected(value):
    sim = simulator()
    rejected_without_mutation(sim, command(sim, scope={**SCOPE, "organization_id": value}))


def test_acknowledgement_alone_does_not_make_fixture_eligible():
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, operation(sim, "dispatch"))
    applied(sim, operation(sim, "acknowledge", receipt=receipt(sim)))
    assert not document(sim)["fixture_eligible"] and document(sim)["index_epoch"] == 0
    applied(sim, operation(sim, "reconcile"))
    assert document(sim)["fixture_eligible"]


@pytest.mark.parametrize("field", ["index_verified", "release_authorized", "metadata"])
def test_receipt_metadata_is_not_authority(field):
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, operation(sim, "dispatch"))
    ack = receipt(sim)
    ack[field] = True
    rejected_without_mutation(sim, operation(sim, "acknowledge", receipt=ack))
    assert not document(sim)["fixture_eligible"]


def test_failed_delete_cleanup_retains_tombstone_and_identity():
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, command(sim, "delete", cid="c2", eid="e2"))
    applied(sim, operation(sim, "dispatch", "e2"))
    applied(sim, operation(sim, "acknowledge", "e2", receipt=receipt(sim, "e2", "failure")))
    applied(sim, operation(sim, "reconcile", "e2"))
    assert document(sim)["tombstoned"] and not document(sim)["fixture_eligible"]
    rejected_without_mutation(sim, command(sim, cid="c3", eid="e3"))


def test_new_explicit_reindex_intent_can_recover_failed_index_without_retry():
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, operation(sim, "dispatch"))
    applied(sim, operation(sim, "acknowledge", receipt=receipt(sim, outcome="failure")))
    applied(sim, operation(sim, "reconcile"))
    applied(sim, command(sim, "reindex", cid="c2", eid="e2"))
    assert document(sim)["lifecycle_epoch"] == 2 and event(sim, "e1")["status"] == "failed"
    indexed(sim, "e2")
    assert document(sim)["fixture_eligible"]


def test_one_global_dispatch_reservation_covers_different_documents():
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, command(sim, cid="c2", eid="e2", did="doc2"))
    applied(sim, operation(sim, "dispatch", "e1"))
    assert rejected_without_mutation(sim, operation(sim, "dispatch", "e2"))["reason"] == "concurrent_dispatch_forbidden"


def test_events_are_bounded_and_rejection_is_atomic():
    sim = simulator()
    applied(sim, command(sim, cid="c0", eid="e0"))
    for i in range(1, 64):
        applied(sim, command(sim, "reindex", cid=f"c{i}", eid=f"e{i}"))
    report = rejected_without_mutation(sim, command(sim, "reindex", cid="c64", eid="e64"))
    assert report["reason"] == "event_limit_exceeded"
    assert len(sim.snapshot()["events"]) == 64


@pytest.mark.parametrize("mode", ["duplicate_command", "missing_event", "bad_request_hash", "policy", "raw_contents", "oversize_journal"])
def test_malformed_cross_references_policy_and_journal_fail_closed(mode):
    sim = simulator()
    applied(sim, command(sim))
    raw = sim.snapshot()
    if mode == "duplicate_command": raw["journal"].append(copy.deepcopy(raw["journal"][0]))
    if mode == "missing_event": raw["events"] = []
    if mode == "bad_request_hash": raw["events"][0]["request_sha256"] = "0"*64
    if mode == "policy": raw["policy_sha256"] = "0"*64
    if mode == "raw_contents": raw["documents"][0]["contents"] = "do-not-expose-secret"
    if mode == "oversize_journal": raw["journal"] *= 257
    raw["state_sha256"] = digest({k: v for k, v in raw.items() if k != "state_sha256"})
    restarted = simulator(raw)
    report = restarted.report()
    closed(report)
    assert report["status"] == "blocked" and "do-not-expose" not in str(report)


def test_journal_step_budget_never_automatically_discards_old_proofs():
    sim = simulator()
    for i in range(64):
        applied(sim, command(sim, "create" if i == 0 else "reindex", cid=f"c{i}", eid=f"e{i}"))
        indexed(sim, f"e{i}")
    assert len(sim.snapshot()["journal"]) == 256
    report = rejected_without_mutation(sim, command(sim, "reindex", cid="c64", eid="e64"))
    assert report["reason"] == "step_limit_exceeded"
    assert simulator(sim.snapshot()).snapshot() == sim.snapshot()


def test_oversized_initial_state_is_not_replaced_with_empty_fallback():
    raw = empty_state()
    raw["untrusted"] = "do-not-expose"*100000
    restored = LifecycleSimulator(state=raw, expected_state_sha256="0"*64)
    assert restored.snapshot() is None
    report = restored.report()
    closed(report)
    assert report["status"] == "blocked" and len(str(report)) < 1500


def test_explicit_recovery_is_checkpointed_and_does_not_allow_parallel_dispatch():
    sim = simulator()
    applied(sim, command(sim))
    applied(sim, command(sim, cid="c2", eid="e2", did="doc2"))
    applied(sim, operation(sim, "dispatch"))
    for invalid in (False, 1, "true", None):
        rejected_without_mutation(sim, operation(sim, "recover", prior_dispatch_stopped=invalid))
    applied(sim, operation(sim, "recover", prior_dispatch_stopped=True))
    saved = sim.snapshot()
    sim = simulator(saved)
    assert sim.snapshot() == saved and event(sim, "e1")["status"] == "replay_ready"
    rejected_without_mutation(sim, operation(sim, "dispatch", "e2"))
    rejected_without_mutation(sim, operation(sim, "acknowledge", receipt=receipt(sim)))
    applied(sim, operation(sim, "dispatch", replay=True))
    rejected_without_mutation(sim, operation(sim, "recover", prior_dispatch_stopped=True))
    applied(sim, operation(sim, "acknowledge", receipt=receipt(sim)))
    applied(sim, operation(sim, "reconcile"))
    assert document(sim)["fixture_eligible"]


@pytest.mark.parametrize("stage", ["pending", "acknowledged", "completed"])
def test_recovery_is_not_a_general_retry_or_fallback(stage):
    sim = simulator()
    applied(sim, command(sim))
    if stage != "pending":
        applied(sim, operation(sim, "dispatch"))
        applied(sim, operation(sim, "acknowledge", receipt=receipt(sim)))
    if stage == "completed": applied(sim, operation(sim, "reconcile"))
    rejected_without_mutation(sim, operation(sim, "recover", prior_dispatch_stopped=True))
