"""Anchored synthetic catalog composition; no storage, auth, or index proof."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from evaluation.governed_answers.lifecycle_simulator import LifecycleSimulator, empty_state, digest
from evaluation.governed_answers.simulator_catalog_adapter import SimulatorCatalogAdapter, DocumentByteFixture
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope, ScriptedIdentity, AuthoritySnapshot, OfflineEligibilityGuard
from evaluation.governed_answers.scoped_async_coordinator import OfflineScopedAsyncCoordinator

spec = importlib.util.spec_from_file_location("adapter_async_helpers", Path(__file__).parent / "test_answer_async_coordinator.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
setup = helpers.setup
SCOPE = EvidenceScope(organization_id="org", collection="knowledge", module="engineering", topic="policy")


def sha(value):
    return hashlib.sha256(value).hexdigest()


def manifest(file_bytes, chunks):
    return dict(file_sha256=sha(file_bytes), chunk_count=len(chunks), chunks=[dict(chunk_index=i, sha256=sha(value), byte_length=len(value)) for i, value in enumerate(chunks)])


def mutate(sim, operation="create", *, content=None, did="doc", scope=SCOPE):
    state = sim.snapshot()
    doc = next((d for d in state["documents"] if d["document_id"] == did), None)
    revision = next((s["revision"] for s in state["scopes"] if s["scope"] == scope.model_dump()), 0)
    number = len(state["events"])+1
    result = sim.apply(dict(operation=operation, command_id=f"c{number}", event_id=f"e{number}", document_id=did,
        scope=scope.model_dump(), expected_state_sha256=state["state_sha256"], expected_document_sha256=digest(doc) if doc else None,
        expected_scope_revision=revision, manifest=content))
    assert result["status"] == "applied", result
    return f"e{number}"


def index(sim, eid):
    for op in ("dispatch", "acknowledge", "reconcile"):
        event = next(e for e in sim.snapshot()["events"] if e["event_id"] == eid)
        action = dict(operation=op, event_id=eid, expected_state_sha256=sim.snapshot()["state_sha256"], expected_event_sha256=digest(event))
        if op == "acknowledge":
            action["receipt"] = dict(event_id=eid, document_id=event["document_id"], scope=event["scope"], lifecycle_epoch=event["lifecycle_epoch"],
                content_epoch=event["content_epoch"], index_epoch=event["target_index_epoch"], manifest_sha256=event["manifest_sha256"],
                request_sha256=event["request_sha256"], outcome="success", execution_source="unit_test")
        assert sim.apply(action)["status"] == "applied"


def make_adapter(sim, fixtures, grants=(SCOPE,)):
    state = sim.snapshot()
    return SimulatorCatalogAdapter(state=state, expected_state_sha256=state["state_sha256"],
        authority=AuthoritySnapshot(principal_id="fixture-admin", permission_epoch=3, grants=grants), byte_fixtures=fixtures)


@pytest.fixture
def bundle(setup):
    args, generation, judge = setup
    chunks = tuple(s.text.encode() for s in args["sources"])
    file_bytes = b"explicit synthetic source file"
    initial = empty_state()
    sim = LifecycleSimulator(state=initial, expected_state_sha256=initial["state_sha256"])
    index(sim, mutate(sim, content=manifest(file_bytes, chunks)))
    byte_fixture = DocumentByteFixture(document_id="doc", scope=SCOPE, file_bytes=file_bytes, chunks=chunks)
    adapter = make_adapter(sim, (byte_fixture,))
    return sim, adapter, byte_fixture, args, generation, judge


def closed(report):
    for field in ("production_enabled", "release_authorized", "semantic_grounding_verified", "authenticated_scope_verified", "index_verified"):
        assert report[field] is False
    assert report["execution_source"] == "unit_test"
    assert report["proposition_to_inference"] == "closed"


def test_exact_mapping_immutable_inputs_and_deterministic_safe_report(bundle):
    sim, adapter, fixture, *_ = bundle
    snapshot = sim.snapshot()
    evidence = adapter.evidence(scope=SCOPE, document_ids=("doc",))
    catalog = adapter.catalog_reader.read(scope=SCOPE)
    assert catalog.revision == snapshot["scopes"][0]["revision"]
    doc = catalog.documents[0]
    assert (doc.lifecycle_epoch, doc.content_epoch, doc.index_epoch) == (1, 1, 1)
    assert doc.file_sha256 == sha(fixture.file_bytes)
    assert doc.chunk_hashes == tuple(sha(c) for c in fixture.chunks)
    assert tuple(c.text.encode() for c in evidence) == fixture.chunks
    report = adapter.report()
    closed(report)
    assert report == adapter.report() == make_adapter(sim, (fixture,)).report()
    assert fixture.file_bytes.decode() not in json.dumps(report)
    assert all(c.decode() not in json.dumps(report) for c in fixture.chunks)
    snapshot["documents"][0]["state"] = "archived"
    assert adapter.catalog_reader.read(scope=SCOPE) == catalog


@pytest.mark.parametrize("mode", ["file", "chunk", "length", "order", "utf8", "missing"])
def test_bytes_must_match_complete_ordered_manifest(bundle, mode):
    sim, _, fixture, *_ = bundle
    chunks, file_bytes = fixture.chunks, fixture.file_bytes
    if mode == "file": file_bytes += b"x"
    if mode == "chunk": chunks = (b"x" * len(chunks[0]),) + chunks[1:]
    if mode == "length": chunks = (chunks[0]+b"x",) + chunks[1:]
    if mode == "order": chunks = tuple(reversed(chunks))
    if mode == "missing": chunks = chunks[:-1]
    if mode == "utf8":
        chunks = (b"\xff",)
        mutate(sim, "replace", content=manifest(file_bytes, chunks))
        index(sim, "e2")
    altered = DocumentByteFixture(document_id="doc", scope=SCOPE, file_bytes=file_bytes, chunks=chunks)
    with pytest.raises(ValueError):
        make_adapter(sim, (altered,)).evidence(scope=SCOPE, document_ids=("doc",))


@pytest.mark.parametrize("mode", ["anchor", "journal", "flag", "schema"])
def test_malformed_anchored_states_deny_without_fallback(bundle, mode):
    sim, adapter, fixture, *_ = bundle
    state = sim.snapshot()
    anchor = state["state_sha256"]
    if mode == "anchor": anchor = "0"*64
    if mode == "journal": state["journal"] = []
    if mode == "flag": state["production_enabled"] = True
    if mode == "schema": state["unexpected"] = "private source detail"
    with pytest.raises(ValueError):
        adapter.replace_snapshot(state=state, expected_state_sha256=anchor)
    closed(adapter.report())
    assert adapter.report()["status"] == "blocked"
    with pytest.raises(ValueError): adapter.catalog_reader.read(scope=SCOPE)
    assert "private source detail" not in json.dumps(adapter.report())


@pytest.mark.parametrize("mode", ["grant", "foreign", "missing", "duplicate", "empty"])
def test_no_scope_or_selection_is_inferred(bundle, mode):
    sim, adapter, fixture, *_ = bundle
    scope, ids = SCOPE, ("doc",)
    if mode == "grant": adapter = make_adapter(sim, (fixture,), grants=())
    if mode == "foreign": scope = SCOPE.model_copy(update={"organization_id": "foreign"})
    if mode == "missing": ids = ("other",)
    if mode == "duplicate": ids *= 2
    if mode == "empty": ids = ()
    with pytest.raises(ValueError): adapter.evidence(scope=scope, document_ids=ids)


@pytest.fixture
def anyio_backend():
    return "asyncio"


async def evaluate(bundle, stage=None, operation=None, real_clock=False):
    sim, adapter, fixture, args, generation, judge = bundle
    events = []
    providers = [helpers.Provider("generation", generation, events), helpers.Provider("statement_assessment", judge, events), helpers.Provider("relevance_assessment", None, events)]
    if stage is not None:
        async def race():
            content = manifest(fixture.file_bytes+b"new", (b"new source",)) if operation == "replace" else None
            mutate(sim, operation, content=content)
            state = sim.snapshot()
            adapter.replace_snapshot(state=state, expected_state_sha256=state["state_sha256"])
        providers[stage].hook = race
    engine = OfflineScopedAsyncCoordinator(generation_provider=providers[0], statement_provider=providers[1], relevance_provider=providers[2],
        authority_reader=adapter.authority_reader, catalog_reader=adapter.catalog_reader, **({} if real_clock else {"clock": lambda: 0.0}))
    result = await engine.evaluate_fixture(identity=ScriptedIdentity(principal_id="fixture-admin"), scope=SCOPE, request_id="request-1",
        question=args["question"], evidence=adapter.evidence(scope=SCOPE, document_ids=("doc",)), relationships=args["relationships"])
    report = result.to_component_report()
    metadata = report["scope_catalog_integration"]
    assert metadata["authenticated_scope_verified"] is metadata["semantic_grounding_verified"] is False
    assert result.production_enabled is result.release_authorized is result.empirical_acceptance is False
    assert metadata["proposition_to_inference"] == "closed"
    return result, report, events


@pytest.mark.anyio
@pytest.mark.parametrize("real_clock", [False, True])
async def test_anchored_fixture_composes_with_offline_coordinator(bundle, real_clock):
    result, report, events = await evaluate(bundle, real_clock=real_clock)
    assert result.preview_allowed
    assert events == ["generation", "statement_assessment", "relevance_assessment"]
    assert "[1] [2]" in report["fixture_text"]
    assert report["public_response"]["answer_text"] is None
    assert report["public_response"]["claims"] == []


@pytest.mark.anyio
@pytest.mark.parametrize("operation", ["archive", "delete", "replace", "reindex"])
@pytest.mark.parametrize("stage", [0, 1, 2])
async def test_lifecycle_races_during_each_await_withhold_and_stop(bundle, operation, stage):
    result, report, events = await evaluate(bundle, stage, operation)
    assert not result.preview_allowed
    assert len(events) == stage+1
    assert report["fixture_text"] is report["fixture_claim"] is report["public_response"] is None


@pytest.mark.parametrize("operation", ["archive", "delete", "replace", "reindex"])
def test_lifecycle_change_invalidates_previously_captured_evidence(bundle, operation):
    sim, adapter, fixture, *_ = bundle
    guard = OfflineEligibilityGuard(authority_reader=adapter.authority_reader, catalog_reader=adapter.catalog_reader)
    captured = guard.capture(identity=ScriptedIdentity(principal_id="fixture-admin"), scope=SCOPE, request_id="capture", question="What?",
        evidence=adapter.evidence(scope=SCOPE, document_ids=("doc",)))
    assert captured.eligible_fixture
    content = manifest(fixture.file_bytes+b"new", (b"new source",)) if operation == "replace" else None
    mutate(sim, operation, content=content)
    state = sim.snapshot()
    adapter.replace_snapshot(state=state, expected_state_sha256=state["state_sha256"])
    assert not guard.recheck(captured.context).eligible_fixture
    with pytest.raises(ValueError): adapter.evidence(scope=SCOPE, document_ids=("doc",))


@pytest.mark.parametrize("mode", ["rollback", "divergent"])
def test_valid_snapshot_rollback_or_divergence_poison_is_terminal(bundle, mode):
    sim, adapter, fixture, *_ = bundle
    old = sim.snapshot()
    mutate(sim, "reindex")
    current = sim.snapshot()
    adapter.replace_snapshot(state=current, expected_state_sha256=current["state_sha256"])
    target = old
    if mode == "divergent":
        other = LifecycleSimulator(state=old, expected_state_sha256=old["state_sha256"])
        mutate(other, "archive")
        target = other.snapshot()
    with pytest.raises(ValueError, match="^snapshot_invalid$"):
        adapter.replace_snapshot(state=target, expected_state_sha256=target["state_sha256"])
    with pytest.raises(ValueError, match="^snapshot_invalid$"):
        adapter.replace_snapshot(state=current, expected_state_sha256=current["state_sha256"])
    with pytest.raises(ValueError): adapter.authority_reader.read(identity=ScriptedIdentity(principal_id="fixture-admin"))
    with pytest.raises(ValueError): adapter.evidence(scope=SCOPE, document_ids=("doc",))
    assert adapter.report()["status"] == "blocked"


def test_all_input_digests_bind_authority_and_supplied_bytes(bundle):
    sim, adapter, fixture, *_ = bundle
    report = adapter.report()
    granted = make_adapter(sim, (fixture,), grants=()).report()
    altered = fixture.model_copy(update={"file_bytes": fixture.file_bytes+b"x"})
    changed = make_adapter(sim, (altered,)).report()
    assert report["state_sha256"] == granted["state_sha256"] == changed["state_sha256"]
    assert report["authority_sha256"] != granted["authority_sha256"]
    assert report["fixtures_sha256"] != changed["fixtures_sha256"]
    assert len({r["input_sha256"] for r in (report, granted, changed)}) == 3
    assert all(r["report_sha256"] == digest({k:v for k,v in r.items() if k != "report_sha256"}) for r in (report, granted, changed))


@pytest.mark.parametrize("mode", ["file", "chunk", "count", "fixture_count", "ids"])
def test_fixture_bounds_are_enforced(bundle, mode):
    sim, adapter, fixture, *_ = bundle
    if mode == "ids":
        with pytest.raises(ValueError): adapter.evidence(scope=SCOPE, document_ids=tuple(str(i) for i in range(26)))
        return
    fields = fixture.model_dump()
    if mode == "file": fields["file_bytes"] = b"x" * 1048577
    if mode == "chunk": fields["chunks"] = (b"x" * 65537,)
    if mode == "count": fields["chunks"] = (b"x",)*33
    with pytest.raises(ValueError):
        bounded = DocumentByteFixture(**fields)
        make_adapter(sim, (bounded,)*17 if mode == "fixture_count" else (bounded,))


@pytest.mark.parametrize("state", ["pending", "failed", "archived", "tombstoned"])
def test_noneligible_lifecycle_rows_are_retained_but_never_evidence(bundle, state):
    sim, _, fixture, *_ = bundle
    if state in {"pending", "failed"}:
        mutate(sim, "reindex")
        if state == "failed":
            event = next(e for e in sim.snapshot()["events"] if e["event_id"] == "e2")
            assert sim.apply(dict(operation="dispatch", event_id="e2", expected_state_sha256=sim.snapshot()["state_sha256"], expected_event_sha256=digest(event)))["status"] == "applied"
            event = next(e for e in sim.snapshot()["events"] if e["event_id"] == "e2")
            receipt = dict(event_id="e2", document_id="doc", scope=event["scope"], lifecycle_epoch=event["lifecycle_epoch"], content_epoch=event["content_epoch"],
                index_epoch=event["target_index_epoch"], manifest_sha256=event["manifest_sha256"], request_sha256=event["request_sha256"], outcome="failure", execution_source="unit_test")
            for op in ("acknowledge", "reconcile"):
                event = next(e for e in sim.snapshot()["events"] if e["event_id"] == "e2")
                action = dict(operation=op, event_id="e2", expected_state_sha256=sim.snapshot()["state_sha256"], expected_event_sha256=digest(event))
                if op == "acknowledge": action["receipt"] = receipt
                assert sim.apply(action)["status"] == "applied"
    else:
        index(sim, mutate(sim, "archive" if state == "archived" else "delete"))
    adapter = make_adapter(sim, (fixture,))
    assert len(adapter.catalog_reader.read(scope=SCOPE).documents) == 1
    assert adapter.catalog_reader.read(scope=SCOPE).documents[0].state == state
    with pytest.raises(ValueError): adapter.evidence(scope=SCOPE, document_ids=("doc",))


@pytest.mark.anyio
async def test_invalid_replacement_during_provider_await_withholds(bundle):
    _, adapter, _, args, generation, judge = bundle
    events = []
    providers = [helpers.Provider("generation", generation, events), helpers.Provider("statement_assessment", judge, events), helpers.Provider("relevance_assessment", None, events)]
    async def poison():
        with pytest.raises(ValueError): adapter.replace_snapshot(state={}, expected_state_sha256="0"*64)
    providers[0].hook = poison
    result = await OfflineScopedAsyncCoordinator(generation_provider=providers[0], statement_provider=providers[1], relevance_provider=providers[2],
        authority_reader=adapter.authority_reader, catalog_reader=adapter.catalog_reader, clock=lambda: 0.0).evaluate_fixture(
            identity=ScriptedIdentity(principal_id="fixture-admin"), scope=SCOPE, request_id="poison", question=args["question"],
            evidence=adapter.evidence(scope=SCOPE, document_ids=("doc",)), relationships=args["relationships"])
    assert not result.preview_allowed and events == ["generation"]
    report = result.to_component_report()
    assert report["fixture_text"] is report["fixture_claim"] is report["public_response"] is None
    closed(adapter.report())


def test_distinct_ids_with_identical_bytes_remain_distinct(bundle):
    sim, _, fixture, *_ = bundle
    index(sim, mutate(sim, content=manifest(fixture.file_bytes, fixture.chunks), did="doc2"))
    other = DocumentByteFixture(document_id="doc2", scope=SCOPE, file_bytes=fixture.file_bytes, chunks=fixture.chunks)
    adapter = make_adapter(sim, (fixture, other))
    evidence = adapter.evidence(scope=SCOPE, document_ids=("doc2", "doc"))
    assert tuple(e.document_id for e in evidence) == ("doc2",)*len(fixture.chunks) + ("doc",)*len(fixture.chunks)
    assert {d.document_id for d in adapter.catalog_reader.read(scope=SCOPE).documents} == {"doc", "doc2"}
