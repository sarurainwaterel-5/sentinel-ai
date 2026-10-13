"""Scripted contract-to-coordinator integration; no real stores or providers."""
import asyncio
import hashlib
import importlib.util
from pathlib import Path

import pytest

from evaluation.governed_answers.scoped_async_coordinator import OfflineScopedAsyncCoordinator
from evaluation.governed_answers.scope_catalog_contracts import (
    EvidenceScope, ScriptedIdentity, AuthoritySnapshot, CatalogSnapshot, DocumentVersion, EvidenceChunk,
)
from evaluation.governed_answers.provider_budget_guard import OfflineBudgetLimits

spec = importlib.util.spec_from_file_location("scoped_async_helpers", Path(__file__).parent / "test_answer_async_coordinator.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
setup = helpers.setup


@pytest.fixture
def anyio_backend():
    return "asyncio"


class Reader:
    execution_source = "unit_test"
    def __init__(self, value):
        self.value, self.failure, self.hook = value, False, None
    def read(self, **kwargs):
        if self.failure: raise RuntimeError("private store detail")
        if self.hook: self.hook()
        return self.value


@pytest.fixture
def integration(setup):
    args, generation, judge = setup
    scope = EvidenceScope(organization_id="org", collection="knowledge", module="engineering", topic="policy")
    identity = ScriptedIdentity(principal_id="fixture-admin")
    authority = Reader(AuthoritySnapshot(principal_id=identity.principal_id, permission_epoch=3, grants=(scope,)))
    document = DocumentVersion(document_id="doc", scope=scope, state="indexed", lifecycle_epoch=4,
        content_epoch=1, index_epoch=1, file_sha256="a"*64,
        chunk_hashes=tuple(hashlib.sha256(s.text.encode()).hexdigest() for s in args["sources"]))
    catalog = Reader(CatalogSnapshot(scope=scope, revision=10, documents=(document,)))
    evidence = tuple(EvidenceChunk(document_id="doc", scope=scope, chunk_index=s.chunk_index, text=s.text,
        file_sha256="a"*64, lifecycle_epoch=4, content_epoch=1, index_epoch=1) for s in args["sources"])
    events = []
    providers = [helpers.Provider("generation", generation, events), helpers.Provider("statement_assessment", judge, events),
        helpers.Provider("relevance_assessment", None, events)]
    request = dict(identity=identity, scope=scope, request_id="request-1", question=args["question"],
        evidence=evidence, relationships=args["relationships"])
    return request, providers, authority, catalog, events


def engine(providers, authority, catalog, **kwargs):
    return OfflineScopedAsyncCoordinator(generation_provider=providers[0], statement_provider=providers[1],
        relevance_provider=providers[2], authority_reader=authority, catalog_reader=catalog, **kwargs)


def closed(result):
    report = result.to_component_report()
    assert result.release_authorized is result.production_enabled is result.empirical_acceptance is False
    metadata = report["scope_catalog_integration"]
    assert metadata["authenticated_scope_verified"] is metadata["semantic_grounding_verified"] is False
    assert metadata["proposition_to_inference"] == "closed"
    if not result.preview_allowed:
        assert report["public_response"] is report["fixture_claim"] is report["fixture_text"] is None
    return report


@pytest.mark.anyio
async def test_success_preserves_exact_assessed_statement_citations_and_receipts(integration):
    request, providers, authority, catalog, events = integration
    result = await engine(providers, authority, catalog).evaluate_fixture(**request)
    report = closed(result)
    assert result.preview_allowed
    assert events == ["generation", "statement_assessment", "relevance_assessment"]
    assert report["fixture_claim"]["statement"] == "The supplied reports disagree about approval."
    assert "[1] [2]" in report["fixture_text"]
    assert len(report["scope_catalog_integration"]["context_sha256"]) == 64
    assert report["async_coordinator"]["stage_receipts"][-1]["total_calls"] == 3
    assert report["public_response"]["answer_text"] is None and report["public_response"]["claims"] == []
    # Existing exact snapshot/relevance guard checks the deterministic rendering.
    assert report["presentation_guard"]["status"] == "allowed_offline_fixture"
    from evaluation.governed_answers.evidence_scope_guard import evaluate_scoped_fixture
    legacy, _, _ = helpers.setup.__wrapped__()
    assert report["fixture_text"] == evaluate_scoped_fixture(**legacy).to_component_report()["fixture_text"]


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["identity", "foreign_scope", "grant", "source_hash", "index", "state", "shared_client"])
async def test_preflight_denies_before_all_provider_calls(integration, mode):
    request, providers, authority, catalog, events = integration
    if mode == "identity": request["identity"] = {"X-User": "fixture-admin"}
    if mode == "foreign_scope": request["scope"] = request["scope"].model_copy(update={"organization_id": "other"})
    if mode == "grant": authority.value = authority.value.model_copy(update={"grants": ()})
    if mode == "source_hash": request["evidence"] = (request["evidence"][0].model_copy(update={"text": "wrong"}),)
    if mode in {"index", "state"}:
        doc = catalog.value.documents[0]
        change = {"index_epoch": 0} if mode == "index" else {"state": "restoring"}
        catalog.value = catalog.value.model_copy(update={"documents": (doc.model_copy(update=change),)})
    if mode == "shared_client": providers[0].client = providers[1].client = object()
    result = await engine(providers, authority, catalog).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and events == []


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
@pytest.mark.parametrize("mutation", ["revocation", "epoch", "archive_restore", "delete_recreate", "content", "unavailable", "relationship"])
async def test_each_provider_await_rechecks_live_contract_readers(integration, stage, mutation):
    request, providers, authority, catalog, events = integration
    async def mutate():
        if mutation == "revocation": authority.value = authority.value.model_copy(update={"grants": ()})
        elif mutation == "epoch": authority.value = authority.value.model_copy(update={"permission_epoch": 4})
        elif mutation == "unavailable": catalog.failure = True
        elif mutation == "relationship": request["relationships"][0].basis += " changed"
        else:
            doc = catalog.value.documents[0]
            field = "content_epoch" if mutation == "content" else "lifecycle_epoch"
            catalog.value = catalog.value.model_copy(update={"documents": (doc.model_copy(update={field: getattr(doc, field)+2}),)})
    providers[stage].hook = mutate
    result = await engine(providers, authority, catalog).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and len(events) == stage+1
    assert "private store detail" not in result.report_json


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["statement", "irrelevant", "uncertain", "unbound"])
async def test_negative_or_unbound_assessment_cannot_be_promoted_by_scope(integration, mode):
    request, providers, authority, catalog, events = integration
    if mode == "statement": providers[1].fixture.defect = "negation_reversal"
    if mode == "irrelevant": providers[2].answer = False
    if mode == "uncertain": providers[2].uncertain = True
    if mode == "unbound": providers[2].mismatch = True
    result = await engine(providers, authority, catalog).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and len(events) == (2 if mode == "statement" else 3)


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
async def test_expired_outer_deadline_withholds(integration, stage):
    request, providers, authority, catalog, events = integration
    now = [100.0]
    async def expire(): now[0] += 3
    providers[stage].hook = expire
    result = await engine(providers, authority, catalog, clock=lambda: now[0]).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and len(events) == stage+1


@pytest.mark.anyio
async def test_capture_time_consumes_shared_request_deadline(integration):
    request, providers, authority, catalog, events = integration
    now = [100.0]
    def expire(): now[0] += 3
    catalog.hook = expire
    result = await engine(providers, authority, catalog, clock=lambda: now[0]).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and events == []


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
async def test_cancellation_and_resistant_late_response_never_return_fixture(integration, stage):
    request, providers, authority, catalog, events = integration
    entered, release, late = asyncio.Event(), asyncio.Event(), asyncio.Event()
    async def resist():
        entered.set()
        try: await release.wait()
        except asyncio.CancelledError: await release.wait()
        late.set()
    providers[stage].hook = resist
    task = asyncio.create_task(engine(providers, authority, catalog).evaluate_fixture(**request))
    await asyncio.wait_for(entered.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    release.set()
    await asyncio.wait_for(late.wait(), 1)
    await asyncio.sleep(0)
    assert len(events) == stage+1


@pytest.mark.anyio
async def test_call_budget_is_not_reset_by_bridge(integration):
    request, providers, authority, catalog, events = integration
    result = await engine(providers, authority, catalog, limits=OfflineBudgetLimits(total_calls=1)).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and events == ["generation"]


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["revocation", "expiry"])
async def test_final_return_checkpoint_withholds_complete_inner_success(integration, monkeypatch, mode):
    from evaluation.governed_answers.scoped_async_coordinator import OfflineAsyncAnswerCoordinator
    request, providers, authority, catalog, events = integration
    now = [100.0]
    original = OfflineAsyncAnswerCoordinator.evaluate_fixture
    async def late_change(self, **kwargs):
        result = await original(self, **kwargs)
        assert result.preview_allowed
        if mode == "revocation": authority.value = authority.value.model_copy(update={"grants": ()})
        else: now[0] += 3
        return result
    monkeypatch.setattr(OfflineAsyncAnswerCoordinator, "evaluate_fixture", late_change)
    result = await engine(providers, authority, catalog, clock=lambda: now[0]).evaluate_fixture(**request)
    report = closed(result)
    assert not result.preview_allowed and len(events) == 3
    assert len(report["async_coordinator"]["stage_receipts"]) == 3


@pytest.mark.anyio
async def test_client_identity_change_during_call_is_detected(integration):
    request, providers, authority, catalog, events = integration
    async def change(): providers[0].client = object()
    providers[0].hook = change
    result = await engine(providers, authority, catalog).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and events == ["generation"]
