"""Synthetic bytes-only planner; no database, discovery or real index evidence."""
import copy
import hashlib
import json

import pytest

from evaluation.governed_answers.backfill_planner import (
    plan_backfill, verify_plan, policy_sha256, manifest_sha256,
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def fixture(document_id="doc-1", scope=None):
    scope = scope or dict(organization_id="org", collection="knowledge", module="engineering", topic="policy")
    file_bytes = b"synthetic original file contents"
    chunks = (b"exact first chunk", b"exact second chunk")
    manifest = [{"chunk_index": i, "sha256": digest(data), "byte_length": len(data)} for i, data in enumerate(chunks)]
    record = dict(document_id=document_id, scope=scope, legacy_status="indexed", file_sha256=digest(file_bytes),
        chunk_count=2, chunk_hashes=tuple(digest(data) for data in chunks), lifecycle_epoch=3, content_epoch=2,
        index_epoch=2, scope_revision=4, index_evidence=dict(state="synthetic_complete", lifecycle_epoch=3,
            content_epoch=2, manifest_sha256=manifest_sha256(document_id=document_id, scope=scope,
                file_sha256=digest(file_bytes), content_epoch=2, chunks=manifest)))
    return dict(records=(record,), mappings=(dict(document_id=document_id, scope=scope, file_fixture_id="file-1"),),
        file_fixtures={"file-1": file_bytes}, chunk_fixtures=tuple(dict(document_id=document_id, chunk_index=i, data=data)
            for i, data in enumerate(chunks)))


def row(plan):
    assert plan["status"] == "dry_run"
    assert len(plan["rows"]) == 1
    return plan["rows"][0]


def closed(plan):
    for key in ("production_enabled", "release_authorized", "semantic_grounding_verified", "authenticated_scope_verified", "index_verified"):
        assert plan[key] is False
    assert plan["dry_run"] is True and plan["proposition_to_inference"] == "closed"
    assert sum(plan["counts"].values()) == plan["row_count"]
    assert len(json.dumps(plan).encode()) <= 1048576
    assert all(r["planned_state"] != "indexed" and r["index_verified"] is False for r in plan["rows"])
    assert "synthetic original file contents" not in json.dumps(plan)
    assert "exact first chunk" not in json.dumps(plan)


def test_valid_deterministic_proposal_only():
    args = fixture()
    before = copy.deepcopy(args)
    plan = plan_backfill(**args)
    closed(plan)
    proposed = row(plan)
    assert proposed["disposition"] == "pending_verification" and proposed["planned_state"] == "pending"
    assert proposed["reasons"] == ["real_index_verification_required"]
    assert proposed["file_sha256"] == digest(args["file_fixtures"]["file-1"])
    assert [c["sha256"] for c in proposed["chunks"]] == list(args["records"][0]["chunk_hashes"])
    assert plan["policy_sha256"] == policy_sha256()
    assert args == before and plan_backfill(**args) == plan and verify_plan(plan, **args)


def merged(a, b):
    return dict(records=a["records"]+b["records"], mappings=a["mappings"]+b["mappings"],
        file_fixtures={**a["file_fixtures"], **b["file_fixtures"]}, chunk_fixtures=a["chunk_fixtures"]+b["chunk_fixtures"])


@pytest.mark.parametrize("different_scope", [False, True])
def test_equal_bytes_do_not_merge_identity_or_scope(different_scope):
    a = fixture()
    scope = {**a["records"][0]["scope"], "organization_id": "other"} if different_scope else None
    args = merged(a, fixture("doc-2", scope))
    plan = plan_backfill(**args)
    closed(plan)
    assert plan["counts"]["pending_verification"] == 2
    assert {r["document_id"] for r in plan["rows"]} == {"doc-1", "doc-2"}
    assert all(r["equal_content_record_count"] == 2 for r in plan["rows"])
    assert len({r["manifest_sha256"] for r in plan["rows"]}) == 2


def test_top_level_collection_order_is_not_semantic():
    args = merged(fixture(), fixture("doc-2"))
    plan = plan_backfill(**args)
    reordered = {**args, **{key: tuple(reversed(args[key])) for key in ("records", "mappings", "chunk_fixtures")}}
    assert plan_backfill(**reordered) == plan
    # Lists/tuples in JSON record arrays have the same declared semantics.
    changed = copy.deepcopy(args)
    changed["records"][0]["chunk_hashes"] = list(changed["records"][0]["chunk_hashes"])
    assert plan_backfill(**changed) == plan


@pytest.mark.parametrize("mode", ["missing", "none", "empty", "mismatch", "declared_missing", "declared_malformed"])
def test_missing_or_mismatched_file_bytes_quarantine(mode):
    args = fixture()
    if mode == "missing": args["file_fixtures"] = {}
    if mode == "none": args["file_fixtures"]["file-1"] = None
    if mode == "empty": args["file_fixtures"]["file-1"] = b""
    if mode == "mismatch": args["file_fixtures"]["file-1"] = b"other"
    if mode == "declared_missing": args["records"][0]["file_sha256"] = None
    if mode == "declared_malformed": args["records"][0]["file_sha256"] = "bad-hash"
    plan = plan_backfill(**args)
    closed(plan)
    assert row(plan)["disposition"] == "quarantined"


@pytest.mark.parametrize("field", ["organization_id", "collection", "module", "topic"])
def test_mapping_must_match_every_scope_component(field):
    args = fixture()
    args["mappings"][0]["scope"] = {**args["records"][0]["scope"], field: "other"}
    assert "scope_mapping_mismatch" in row(plan_backfill(**args))["reasons"]


@pytest.mark.parametrize("value", ["*", "all", "ALL", " org", "org ", "org*", "", "\norg"])
def test_wildcard_blank_or_normalized_scope_is_not_accepted(value):
    args = fixture()
    args["records"][0]["scope"]["organization_id"] = value
    plan = plan_backfill(**args)
    closed(plan)
    assert plan["status"] == "blocked" or row(plan)["disposition"] == "quarantined"


@pytest.mark.parametrize("mode", ["duplicate_record", "incompatible_scope", "duplicate_mapping", "conflicting_mapping", "missing_mapping"])
def test_identity_and_mapping_conflicts_are_never_deduplicated(mode):
    args = fixture()
    if mode in {"duplicate_record", "incompatible_scope"}:
        other = copy.deepcopy(args["records"][0])
        if mode == "incompatible_scope": other["scope"]["topic"] = "other"
        args["records"] += (other,)
    elif mode in {"duplicate_mapping", "conflicting_mapping"}:
        other = copy.deepcopy(args["mappings"][0])
        if mode == "conflicting_mapping": other["scope"]["topic"] = "other"
        args["mappings"] += (other,)
    else: args["mappings"] = ()
    plan = plan_backfill(**args)
    closed(plan)
    assert plan["counts"]["quarantined"] == len(args["records"])
    assert plan["row_count"] == len(args["records"])


@pytest.mark.parametrize("mode", ["missing", "duplicate", "gap", "data_order", "hash_order", "none", "empty", "wrong_hash", "bad_hash", "count"])
def test_exact_ordered_complete_chunk_manifest_required(mode):
    args = fixture()
    chunks = list(args["chunk_fixtures"])
    if mode == "missing": chunks.pop()
    if mode == "duplicate": chunks.append(copy.deepcopy(chunks[0]))
    if mode == "gap": chunks[1]["chunk_index"] = 2
    if mode == "data_order": chunks[0]["data"], chunks[1]["data"] = chunks[1]["data"], chunks[0]["data"]
    if mode == "hash_order": args["records"][0]["chunk_hashes"] = tuple(reversed(args["records"][0]["chunk_hashes"]))
    if mode == "none": chunks[0]["data"] = None
    if mode == "empty": chunks[0]["data"] = b""
    if mode == "wrong_hash": args["records"][0]["chunk_hashes"] = ("0"*64, "1"*64)
    if mode == "bad_hash": args["records"][0]["chunk_hashes"] = ("bad", "1"*64)
    if mode == "count": args["records"][0]["chunk_count"] = 3
    args["chunk_fixtures"] = tuple(chunks)
    plan = plan_backfill(**args)
    closed(plan)
    assert row(plan)["disposition"] == "quarantined"


@pytest.mark.parametrize("mode", ["absent", "unverified", "stale_content", "stale_lifecycle", "wrong_manifest", "actual_api", "forged_verified"])
def test_legacy_indexed_cannot_replace_bound_synthetic_evidence(mode):
    args = fixture()
    record = args["records"][0]
    if mode == "absent": record["index_evidence"] = None
    if mode == "unverified": record["index_evidence"]["state"] = "unverified"
    if mode == "stale_content": record["index_evidence"]["content_epoch"] = 1
    if mode == "stale_lifecycle": record["index_evidence"]["lifecycle_epoch"] = 1
    if mode == "wrong_manifest": record["index_evidence"]["manifest_sha256"] = "0"*64
    if mode == "actual_api": record["index_evidence"]["execution_source"] = "actual_api"
    if mode == "forged_verified": record["index_evidence"]["verified"] = True
    plan = plan_backfill(**args)
    closed(plan)
    assert row(plan)["disposition"] == "quarantined"


def with_prior(args):
    record = args["records"][0]
    record["prior"] = {key: copy.deepcopy(record[key]) for key in (
        "scope", "lifecycle_epoch", "content_epoch", "index_epoch", "scope_revision")}
    record["prior"]["tombstoned"] = False
    return record


def test_tombstones_retained_without_file_or_chunk_bytes():
    args = fixture()
    record = with_prior(args)
    record.update(legacy_status="tombstoned", file_sha256=None, chunk_count=0, chunk_hashes=(), index_evidence=None)
    record["prior"]["tombstoned"] = True
    args["file_fixtures"], args["chunk_fixtures"] = {}, ()
    plan = plan_backfill(**args)
    closed(plan)
    assert row(plan)["disposition"] == "retained_tombstone" and row(plan)["tombstone_retained"]


@pytest.mark.parametrize("field", ["lifecycle_epoch", "content_epoch", "index_epoch", "scope_revision"])
@pytest.mark.parametrize("mode", ["negative", "bool", "regression"])
def test_epoch_validation_and_no_regression(field, mode):
    args = fixture()
    record = with_prior(args)
    record[field] = -1 if mode == "negative" else True if mode == "bool" else record[field]-1
    plan = plan_backfill(**args)
    closed(plan)
    assert row(plan)["disposition"] == "quarantined"


@pytest.mark.parametrize("mode", ["resurrection", "scope_move", "index_ahead", "content_without_lifecycle", "lifecycle_without_revision"])
def test_incompatible_identity_transitions_are_quarantined(mode):
    args = fixture()
    record = with_prior(args)
    if mode == "resurrection": record["prior"]["tombstoned"] = True
    if mode == "scope_move": record["prior"]["scope"]["topic"] = "other"
    if mode == "index_ahead": record["index_epoch"] += 1
    if mode == "content_without_lifecycle": record["content_epoch"] += 1
    if mode == "lifecycle_without_revision": record["lifecycle_epoch"] += 1
    plan = plan_backfill(**args)
    closed(plan)
    assert row(plan)["disposition"] == "quarantined"
    if mode == "resurrection":
        assert row(plan)["tombstone_retained"] and row(plan)["planned_state"] == "tombstoned"


@pytest.mark.parametrize("mode", ["input", "policy", "authority", "counts", "rows", "rehashed_authority"])
def test_input_policy_and_report_tampering_are_detected(mode):
    args = fixture()
    plan = plan_backfill(**args)
    if mode == "input":
        args["file_fixtures"]["file-1"] += b"changed"
        blocked = plan_backfill(**args, expected_input_sha256=plan["input_sha256"])
        assert blocked["status"] == "blocked"
    elif mode == "policy":
        assert plan_backfill(**args, expected_policy_sha256="0"*64)["errors"] == ["policy_binding_mismatch"]
        plan["policy_sha256"] = "0"*64
    elif mode in {"authority", "rehashed_authority"}:
        plan["release_authorized"] = True
        if mode == "rehashed_authority":
            del plan["plan_sha256"]
            plan["plan_sha256"] = digest(json.dumps(plan, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode())
    elif mode == "counts": plan["counts"]["pending_verification"] = 99
    else: plan["rows"][0]["planned_state"] = "indexed"
    assert not verify_plan(plan, **args)


@pytest.mark.parametrize("mode", ["records_list", "too_many_records", "huge_bytes", "huge_chunk", "huge_string", "cycle", "object", "bad_mapping", "orphan_chunk", "orphan_mapping"])
def test_malformed_or_oversized_envelopes_have_bounded_reports(mode):
    args = fixture()
    if mode == "records_list": args["records"] = list(args["records"])
    if mode == "too_many_records": args["records"] *= 101
    if mode == "huge_bytes": args["file_fixtures"]["file-1"] = b"x" * (1048576+1)
    if mode == "huge_chunk": args["chunk_fixtures"][0]["data"] = b"x" * 65537
    if mode == "huge_string": args["records"][0]["password"] = "sensitive" * 1000
    if mode == "cycle": args["records"][0]["cycle"] = args["records"][0]
    if mode == "object": args["records"] = (object(),)
    if mode == "bad_mapping": args["mappings"][0]["credential"] = "do-not-emit"
    if mode == "orphan_chunk": args["chunk_fixtures"][0]["document_id"] = "orphan"
    if mode == "orphan_mapping": args["mappings"][0]["document_id"] = "orphan"
    plan = plan_backfill(**args)
    closed(plan)
    assert plan["status"] == "blocked" and plan["rows"] == []
    assert len(json.dumps(plan)) < 1500 and "do-not-emit" not in json.dumps(plan)


def test_malformed_record_diagnostics_do_not_echo_credentials_or_contents():
    args = fixture()
    args["records"][0]["password"] = "do-not-emit"
    args["records"] += (None,)
    plan = plan_backfill(**args)
    closed(plan)
    assert plan["counts"]["quarantined"] == 2
    assert "do-not-emit" not in json.dumps(plan)
    assert all(r["reasons"] == ["record_malformed"] for r in plan["rows"])


def test_duplicate_bomb_does_not_repeat_large_chunk_reports():
    args = fixture()
    args["records"] *= 100
    args["chunk_fixtures"] *= 100
    plan = plan_backfill(**args)
    closed(plan)
    assert plan["row_count"] == 100 and all("chunks" not in r for r in plan["rows"])


def test_empty_inventory_is_an_empty_dry_run_not_permission():
    plan = plan_backfill(records=(), mappings=(), file_fixtures={}, chunk_fixtures=())
    closed(plan)
    assert plan["row_count"] == 0


@pytest.mark.parametrize("field,value", [("file_sha256", "0"*64), ("chunk_hashes", ("0"*64, "1"*64))])
def test_known_prior_content_cannot_change_at_same_content_epoch(field, value):
    args = fixture()
    record = with_prior(args)
    record["prior"][field] = value
    plan = plan_backfill(**args)
    assert "content_changed_without_epoch_advance" in row(plan)["reasons"]


def test_file_swap_invalidates_synthetic_index_manifest_even_with_same_chunks():
    args = fixture()
    args["file_fixtures"]["file-1"] = b"a different original"
    args["records"][0]["file_sha256"] = digest(b"a different original")
    assert "index_evidence_stale_or_unbound" in row(plan_backfill(**args))["reasons"]


def test_type_tagged_byte_binding_cannot_be_spoofed_by_metadata_object():
    args = fixture()
    args["records"][0]["extra"] = b"private-fixture"
    first = plan_backfill(**args)
    args["records"][0]["extra"] = {"kind": "bytes", "sha256": digest(b"private-fixture"), "byte_length": 15}
    second = plan_backfill(**args)
    assert first["input_sha256"] != second["input_sha256"]


def test_duplicate_scoped_identity_cannot_erase_a_tombstone():
    args = fixture()
    tombstone = copy.deepcopy(args["records"][0])
    tombstone["legacy_status"] = "tombstoned"
    args["records"] += (tombstone,)
    plan = plan_backfill(**args)
    closed(plan)
    assert plan["counts"]["quarantined"] == 2
    assert any(r["tombstone_retained"] and r["planned_state"] == "tombstoned" for r in plan["rows"])


def test_aggregate_bytes_limit_is_observed_before_planning():
    args = fixture()
    args["file_fixtures"] = {f"fixture-{i}": b"x"*1048576 for i in range(5)}
    plan = plan_backfill(**args)
    closed(plan)
    assert plan["status"] == "blocked" and plan["rows"] == []


@pytest.mark.parametrize("field", ["records", "mappings", "chunk_fixtures"])
def test_nested_order_permutation_does_not_alter_binding(field):
    args = merged(fixture(), fixture("doc-2"))
    first = plan_backfill(**args)
    args[field] = tuple(reversed(args[field]))
    assert plan_backfill(**args) == first


def test_planning_does_not_discover_files_read_environment_or_dispatch_services(monkeypatch):
    import builtins
    import os
    import socket
    import subprocess
    from pathlib import Path
    args = fixture()
    def forbidden(*unused, **kwargs):
        raise AssertionError("No I/O or environment lookup is permitted")
    with monkeypatch.context() as patch:
        patch.setattr(builtins, "open", forbidden)
        patch.setattr(os, "getenv", forbidden)
        patch.setattr(Path, "glob", forbidden)
        patch.setattr(Path, "rglob", forbidden)
        patch.setattr(socket, "socket", forbidden)
        patch.setattr(subprocess, "Popen", forbidden)
        plan = plan_backfill(**args)
    closed(plan)
    assert plan["counts"]["pending_verification"] == 1


@pytest.mark.parametrize("status,disposition", [("pending", "pending_verification"), ("archived", "quarantined"), ("error", "quarantined")])
def test_legacy_status_never_promotes_to_indexed(status, disposition):
    args = fixture()
    args["records"][0]["legacy_status"] = status
    plan = plan_backfill(**args)
    closed(plan)
    assert row(plan)["disposition"] == disposition


@pytest.mark.parametrize("field", ["lifecycle_epoch", "scope_revision"])
def test_new_tombstone_requires_lifecycle_and_revision_advance(field):
    args = fixture()
    record = with_prior(args)
    record["legacy_status"] = "tombstoned"
    record["lifecycle_epoch"] += 1
    record["scope_revision"] += 1
    record[field] = record["prior"][field]
    result = row(plan_backfill(**args))
    assert result["disposition"] == "quarantined" and result["tombstone_retained"]
    assert "tombstone_transition_without_epoch_advance" in result["reasons"]


def test_monotonic_content_progression_can_remain_a_pending_proposal():
    args = fixture()
    record = with_prior(args)
    record.update(lifecycle_epoch=4, content_epoch=3, index_epoch=3, scope_revision=5)
    chunks = [{"chunk_index": c["chunk_index"], "sha256": digest(c["data"]), "byte_length": len(c["data"])} for c in args["chunk_fixtures"]]
    record["index_evidence"].update(lifecycle_epoch=4, content_epoch=3,
        manifest_sha256=manifest_sha256(document_id=record["document_id"], scope=record["scope"],
            file_sha256=record["file_sha256"], content_epoch=3, chunks=chunks))
    plan = plan_backfill(**args)
    closed(plan)
    assert row(plan)["disposition"] == "pending_verification" and verify_plan(plan, **args)


def test_cumulative_metadata_is_bounded_during_traversal():
    args = fixture()
    args["records"][0].update({f"extra-{i}": "x"*4000 for i in range(300)})
    plan = plan_backfill(**args)
    closed(plan)
    assert plan["status"] == "blocked" and len(json.dumps(plan)) < 1500
