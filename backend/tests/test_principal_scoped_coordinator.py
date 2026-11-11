"""Principal-bound simulator composition using synthetic credentials only."""
import importlib.util
from pathlib import Path

import pytest

from evaluation.governed_answers.identity_resolution import PrincipalRecord
from evaluation.governed_answers.principal_scoped_coordinator import OfflinePrincipalScopedCoordinator


def load_helpers(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).parent / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


catalog_helpers = load_helpers("principal_catalog_helpers", "test_simulator_catalog_adapter.py")
identity_helpers = load_helpers("principal_identity_helpers", "test_identity_resolution.py")
setup = catalog_helpers.setup
bundle = catalog_helpers.bundle


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def integration(bundle):
    sim, adapter, fixture, args, generation, judge = bundle
    events = []
    providers = [catalog_helpers.helpers.Provider("generation", generation, events),
                 catalog_helpers.helpers.Provider("statement_assessment", judge, events),
                 catalog_helpers.helpers.Provider("relevance_assessment", None, events)]
    reader = identity_helpers.Reader(PrincipalRecord(username="fixture-admin", principal_id="principal-1",
        enabled=True, credential_version=2, credential_format="fixture-v1", permission_epoch=3,
        grants=(catalog_helpers.SCOPE,)))
    verifier = identity_helpers.Verifier()
    request = dict(authorization_values=(identity_helpers.header(),), scope=catalog_helpers.SCOPE,
        request_id="principal-request", question=args["question"], relationships=args["relationships"],
        evidence=adapter.evidence(scope=catalog_helpers.SCOPE, document_ids=("doc",)))
    return request, providers, reader, verifier, adapter, sim, events


def engine(integration, **kwargs):
    _, providers, reader, verifier, adapter, *_ = integration
    return OfflinePrincipalScopedCoordinator(generation_provider=providers[0], statement_provider=providers[1],
        relevance_provider=providers[2], principal_reader=reader, verifier=verifier,
        catalog_reader=adapter.catalog_reader, **kwargs)


def closed(result):
    report = result.to_component_report()
    assert result.release_authorized is result.production_enabled is result.empirical_acceptance is False
    metadata = report["principal_scope_integration"]
    assert metadata["authenticated_scope_verified"] is metadata["semantic_grounding_verified"] is False
    assert metadata["proposition_to_inference"] == "closed"
    assert "synthetic-password" not in result.report_json
    assert identity_helpers.header() not in result.report_json
    assert "private reader error" not in result.report_json
    assert "private verifier error" not in result.report_json
    if not result.preview_allowed:
        assert report["public_response"] is report["fixture_claim"] is report["fixture_text"] is None
    return report


@pytest.mark.anyio
@pytest.mark.parametrize("real_clock", [False, True])
async def test_success_with_simulator_catalog_and_single_verification(integration, real_clock):
    request, _, reader, verifier, _, _, events = integration
    result = await engine(integration, **({} if real_clock else {"clock": lambda: 100.0})).evaluate_fixture(**request)
    report = closed(result)
    assert result.preview_allowed
    assert events == ["generation", "statement_assessment", "relevance_assessment"]
    assert reader.calls > 2 and verifier.calls == 1
    assert "[1] [2]" in report["fixture_text"]
    assert report["public_response"]["answer_text"] is None
    assert report["public_response"]["claims"] == []
    for field in ("principal_context_sha256", "authority_sha256"):
        assert len(report["principal_scope_integration"][field]) == 64


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["malformed", "duplicate", "password", "disabled", "revoked", "identity",
    "scope", "reader_failure", "verifier_failure", "reader_shape", "verifier_shape", "actual_reader", "actual_verifier"])
async def test_credentials_and_capability_denials_precede_provider_work(integration, mode):
    request, _, reader, verifier, _, _, events = integration
    if mode == "malformed": request["authorization_values"] = ("Bearer synthetic",)
    if mode == "duplicate": request["authorization_values"] *= 2
    if mode == "password": request["authorization_values"] = (identity_helpers.header(password="wrong"),)
    if mode == "disabled": reader.record = reader.record.model_copy(update={"enabled": False})
    if mode == "revoked": reader.record = reader.record.model_copy(update={"grants": ()})
    if mode == "identity": reader.record = reader.record.model_copy(update={"username": "someone-else"})
    if mode == "scope": request["scope"] = request["scope"].model_copy(update={"topic": "foreign"})
    if mode == "reader_failure": reader.failure = True
    if mode == "verifier_failure": verifier.failure = True
    if mode == "reader_shape": reader.record = {"enabled": True, "principal_id": "principal-1"}
    if mode == "verifier_shape": verifier.result = {"verified": True}
    if mode == "actual_reader": reader.execution_source = "actual_api"
    if mode == "actual_verifier": verifier.execution_source = "actual_api"
    result = await engine(integration).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and events == []
    assert verifier.calls <= 1


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
@pytest.mark.parametrize("mutation", ["disabled", "revoke", "rotate", "epoch", "principal", "catalog", "both"])
async def test_each_await_rechecks_principal_and_document_lifecycle(integration, stage, mutation):
    request, providers, reader, verifier, adapter, sim, events = integration
    async def change():
        update = {"disabled": {"enabled": False}, "revoke": {"grants": ()},
                  "rotate": {"credential_version": 3}, "epoch": {"permission_epoch": 4},
                  "principal": {"principal_id": "other"}, "both": {"grants": ()}}.get(mutation)
        if update: reader.record = reader.record.model_copy(update=update)
        if mutation in {"catalog", "both"}:
            catalog_helpers.mutate(sim, "archive")
            state = sim.snapshot()
            adapter.replace_snapshot(state=state, expected_state_sha256=state["state_sha256"])
    providers[stage].hook = change
    result = await engine(integration).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and len(events) == stage+1
    assert verifier.calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize("source", ["reader", "verifier", "catalog", "provider"])
async def test_shared_deadline_counts_resolution_capture_and_provider_work(integration, source):
    request, providers, reader, verifier, adapter, _, events = integration
    now = [100.0]
    def expire(): now[0] += 3
    if source == "reader": reader.hook = expire
    if source == "verifier": verifier.hook = expire
    if source == "catalog":
        original = adapter.catalog_reader.read
        def read(**kwargs):
            result = original(**kwargs)
            expire()
            return result
        adapter.catalog_reader.read = read
    if source == "provider":
        async def change(): expire()
        providers[0].hook = change
    result = await engine(integration, clock=lambda: now[0]).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed
    assert len(events) == (1 if source == "provider" else 0)


@pytest.mark.anyio
@pytest.mark.parametrize("field,value", [("principal_id", "principal-2"), ("permission_epoch", 4)])
async def test_principal_and_permission_epoch_are_bound_in_authority_digest(integration, field, value):
    request, _, reader, _, _, _, _ = integration
    first = await engine(integration, clock=lambda: 100.0).evaluate_fixture(**request)
    reader.record = reader.record.model_copy(update={field: value})
    second = await engine(integration, clock=lambda: 100.0).evaluate_fixture(**request)
    a, b = closed(first), closed(second)
    assert first.preview_allowed and second.preview_allowed
    assert a["principal_scope_integration"]["authority_sha256"] != b["principal_scope_integration"]["authority_sha256"]


@pytest.mark.anyio
async def test_revocation_is_terminal_even_when_access_is_restored(integration):
    request, providers, reader, verifier, _, _, events = integration
    original = reader.record
    async def revoke(): reader.record = original.model_copy(update={"grants": ()})
    providers[0].hook = revoke
    result = await engine(integration).evaluate_fixture(**request)
    reader.record = original
    report = closed(result)
    assert not result.preview_allowed and events == ["generation"] and verifier.calls == 1
    assert result.to_component_report() == report


@pytest.mark.anyio
@pytest.mark.parametrize("mutation", ["grant_addition", "verifier_rotation", "reader_failure"])
async def test_catalog_reader_cannot_race_authority_capture(integration, mutation):
    request, _, reader, verifier, adapter, _, events = integration
    original = adapter.catalog_reader.read
    def race(**kwargs):
        result = original(**kwargs)
        if mutation == "grant_addition":
            extra = request["scope"].model_copy(update={"topic": "extra"})
            reader.record = reader.record.model_copy(update={"grants": (*reader.record.grants, extra)})
        if mutation == "verifier_rotation": verifier.supported_formats = ("fixture-v1", "changed")
        if mutation == "reader_failure": reader.failure = True
        return result
    adapter.catalog_reader.read = race
    result = await engine(integration).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and events == [] and verifier.calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize("field,value", [("enabled", False), ("credential_version", 3), ("permission_epoch", 4)])
async def test_verification_race_cannot_issue_authority(integration, field, value):
    request, _, reader, verifier, _, _, events = integration
    def race(): reader.record = reader.record.model_copy(update={field: value})
    verifier.hook = race
    result = await engine(integration).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and events == [] and verifier.calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize("capability", ["principal_reader", "verifier", "catalog_reader", "providers", "clock", "limits"])
async def test_capability_swap_during_provider_await_is_terminal(integration, capability):
    from evaluation.governed_answers.provider_budget_guard import OfflineBudgetLimits
    request, providers, reader, verifier, adapter, _, events = integration
    coordinator = engine(integration)
    async def swap():
        changes = {"principal_reader": identity_helpers.Reader(reader.record),
                   "verifier": identity_helpers.Verifier(), "catalog_reader": object(),
                   "providers": tuple(reversed(providers)), "clock": lambda: 100.0,
                   "limits": OfflineBudgetLimits()}
        setattr(coordinator, capability, changes[capability])
    providers[0].hook = swap
    result = await coordinator.evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and events == ["generation"] and verifier.calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize("invalid", [99.0, float("nan"), float("inf"), True])
async def test_invalid_or_backward_clock_during_await_denies(integration, invalid):
    request, providers, _, _, _, _, events = integration
    now = [100.0]
    async def change(): now[0] = invalid
    providers[0].hook = change
    result = await engine(integration, clock=lambda: now[0]).evaluate_fixture(**request)
    closed(result)
    assert not result.preview_allowed and events == ["generation"]


@pytest.mark.anyio
async def test_entire_grants_set_is_bound_in_authority_digest(integration):
    request, _, reader, _, _, _, _ = integration
    first = await engine(integration, clock=lambda: 100.0).evaluate_fixture(**request)
    extra = request["scope"].model_copy(update={"topic": "extra"})
    reader.record = reader.record.model_copy(update={"grants": (*reader.record.grants, extra)})
    second = await engine(integration, clock=lambda: 100.0).evaluate_fixture(**request)
    assert first.preview_allowed and second.preview_allowed
    assert closed(first)["principal_scope_integration"]["authority_sha256"] != closed(second)["principal_scope_integration"]["authority_sha256"]


@pytest.mark.anyio
async def test_observed_revocation_remains_terminal_after_reader_restores_grants(integration, monkeypatch):
    from evaluation.governed_answers.scoped_async_coordinator import OfflineScopedAsyncCoordinator
    request, providers, reader, _, _, _, events = integration
    original_record = reader.record
    original_evaluate = OfflineScopedAsyncCoordinator.evaluate_fixture
    async def revoke(): reader.record = original_record.model_copy(update={"grants": ()})
    async def restore_after_denial(self, **kwargs):
        denied = await original_evaluate(self, **kwargs)
        assert not denied.preview_allowed
        reader.record = original_record
        return denied
    monkeypatch.setattr(OfflineScopedAsyncCoordinator, "evaluate_fixture", restore_after_denial)
    providers[0].hook = revoke
    result = await engine(integration).evaluate_fixture(**request)
    closed(result)
    assert reader.record == original_record
    assert not result.preview_allowed and events == ["generation"]


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
async def test_cancellation_propagates_and_prevents_later_provider_work(integration, stage):
    import asyncio
    request, providers, _, verifier, _, _, events = integration
    entered, release = asyncio.Event(), asyncio.Event()
    async def block():
        entered.set()
        await release.wait()
    providers[stage].hook = block
    task = asyncio.create_task(engine(integration).evaluate_fixture(**request))
    await asyncio.wait_for(entered.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    release.set()
    await asyncio.sleep(0)
    assert len(events) == stage+1 and verifier.calls == 1
