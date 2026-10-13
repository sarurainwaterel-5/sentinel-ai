"""Fresh async scripted composition; no provider accuracy or release evidence."""
import asyncio
import importlib.util
import json
from pathlib import Path

import pytest

from app.services.cognition.reasoning.models import Premise, PremiseRelationship
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticAdmissibilityRequest
from evaluation.governed_answers.async_coordinator import (
    OfflineAsyncAnswerCoordinator, _GenerationReplay, _StatementReplay, _RelevanceReplay,
)
from evaluation.governed_answers.evidence_scope_guard import evaluate_scoped_fixture
from evaluation.governed_answers.presentation_guard import RelevanceVerdict
from evaluation.governed_answers.provider_budget_guard import OfflineBudgetLimits, ScriptedProviderFailure

spec = importlib.util.spec_from_file_location("async_scope_helpers",
    Path(__file__).parent / "test_answer_evidence_scope_guard.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
setup = helpers.setup


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
@pytest.mark.parametrize("mode", ["missing", "synchronous"])
async def test_all_async_capabilities_validated_before_any_dispatch(composition, stage, mode):
    inputs, providers, events, _ = composition
    providers[stage].call = None if mode == "missing" else lambda **kwargs: "{}"
    result = await engine(providers).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and events == []


@pytest.mark.anyio
@pytest.mark.parametrize("uncertain,reason", [(False, "fixture_question_not_answered"), (True, "relevance_assessment_uncertain")])
async def test_preserve_bounded_relevance_withholding_reason(composition, uncertain, reason):
    inputs, providers, _, _ = composition
    providers[2].answer = False
    providers[2].uncertain = uncertain
    result = await engine(providers).evaluate_fixture(**inputs)
    report = closed(result)
    assert not result.preview_allowed and result.rejection_reasons == (reason,)
    assert report["async_coordinator"]["rejection_reasons"] == [reason]


@pytest.fixture
def anyio_backend():
    return "asyncio"


class Provider:
    execution_source = "unit_test"

    def __init__(self, role, fixture, events):
        self.role, self.fixture, self.events = role, fixture, events
        self.requests = []
        self.hook = None
        self.failure = None
        self.response = None
        self.answer, self.uncertain, self.mismatch = True, False, False

    async def call(self, *, request):
        self.requests.append(request)
        self.events.append(self.role)
        if self.hook:
            await self.hook()
        if self.failure:
            raise self.failure
        if self.response is not None:
            return self.response
        data = json.loads(request.content_json)
        if self.role == "generation":
            return self.fixture.generate(premises=[Premise.model_validate(p) for p in data["premises"]],
                relationships=[PremiseRelationship.model_validate(r) for r in data["relationships"]]).content
        if self.role == "statement_assessment":
            return self.fixture.assess(request=SemanticAdmissibilityRequest.model_validate_json(request.content_json)).content
        return RelevanceVerdict(request_sha256="0" * 64 if self.mismatch else request.request_sha256,
            answers_question=self.answer, uncertain=self.uncertain, reason="Scripted relevance only.").model_dump_json()


@pytest.fixture
def composition(setup):
    args, generator, judge = setup
    events = []
    providers = [Provider("generation", generator, events), Provider("statement_assessment", judge, events),
                 Provider("relevance_assessment", None, events)]
    inputs = {k: v for k, v in args.items() if k not in {"coordinator", "relevance_assessor"}}
    return inputs, providers, events, args


def engine(providers, **kwargs):
    return OfflineAsyncAnswerCoordinator(generation_provider=providers[0],
        statement_provider=providers[1], relevance_provider=providers[2], **kwargs)


def closed(result):
    report = result.to_component_report()
    assert result.execution_source == "unit_test"
    assert result.production_enabled is result.release_authorized is result.empirical_acceptance is False
    metadata = report["async_coordinator"]
    assert metadata["semantic_grounding_verified"] is False
    assert metadata["proposition_to_inference"] == "closed"
    if not result.preview_allowed:
        assert report["fixture_claim"] is report["fixture_text"] is report["public_response"] is None
    return report


@pytest.mark.anyio
async def test_success_matches_original_exact_text_and_citations(composition):
    inputs, providers, events, original = composition
    expected = evaluate_scoped_fixture(**original).to_component_report()
    result = await engine(providers).evaluate_fixture(**inputs)
    report = closed(result)
    assert result.preview_allowed
    assert events == ["generation", "statement_assessment", "relevance_assessment"]
    assert [len(p.requests) for p in providers] == [1, 1, 1]
    assert report["fixture_text"] == expected["fixture_text"]
    assert report["fixture_claim"] == expected["fixture_claim"]
    assert "[1] [2]" in report["fixture_text"]
    assert report["public_response"]["claims"] == [] and report["public_response"]["answer_text"] is None
    receipts = report["async_coordinator"]["stage_receipts"]
    assert [r["total_calls"] for r in receipts] == [1, 2, 3]
    assert receipts[-1]["calls"] == {stage: 1 for stage in events}
    assert [r["request_sha256"] for r in receipts] == [p.requests[0].request_sha256 for p in providers]
    assert "generator_metadata" not in providers[1].requests[0].content_json
    assert "semantic_grounding_verified" not in providers[2].requests[0].content_json
    report["fixture_claim"]["statement"] = "mutation"
    assert result.to_component_report()["fixture_claim"]["statement"] != "mutation"


@pytest.mark.anyio
@pytest.mark.parametrize("defect", ["unsupported_fact", "certainty_inflation", "causal_overreach",
    "negation_reversal", "fabricated_precision", "conflict_suppression", "unsupported_qualification", "insufficient_support"])
async def test_negative_statement_skips_relevance(composition, defect):
    inputs, providers, events, _ = composition
    providers[1].fixture.defect = defect
    result = await engine(providers).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and result.rejection_reasons == ("async_statement_rejected",)
    assert events == ["generation", "statement_assessment"]


@pytest.mark.anyio
@pytest.mark.parametrize("field", ["answer", "uncertain", "mismatch"])
async def test_negative_uncertain_or_unbound_relevance_withholds(composition, field):
    inputs, providers, events, _ = composition
    setattr(providers[2], field, field != "answer")
    result = await engine(providers).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and len(events) == 3


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
@pytest.mark.parametrize("failure", ["unavailable", "refused", "unexpected", "malformed"])
async def test_failures_never_retry_or_fallback(composition, stage, failure):
    inputs, providers, events, _ = composition
    if failure == "malformed":
        providers[stage].response = "{}"
    else:
        providers[stage].failure = RuntimeError("private provider details") if failure == "unexpected" else ScriptedProviderFailure(failure)
    result = await engine(providers).evaluate_fixture(**inputs)
    report = closed(result)
    assert not result.preview_allowed and len(events) == stage + 1
    assert "private provider details" not in json.dumps(report)
    assert all(len(p.requests) <= 1 for p in providers)


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["permission", "catalog", "relationships", "missing_provider", "actual_api", "shared_object", "shared_client"])
async def test_preflight_denial_and_independence_make_no_calls(composition, mode):
    inputs, providers, events, _ = composition
    if mode == "permission":
        inputs["scope"] = inputs["scope"].model_copy(update={"organization_id": "other"})
    elif mode == "catalog":
        inputs["catalog_reader"].value = inputs["catalog_reader"].value.model_copy(update={"documents": ()})
    elif mode == "relationships":
        inputs["relationships"] = []
    elif mode == "missing_provider":
        providers[2] = None
    elif mode == "actual_api":
        providers[1].execution_source = "actual_api"
    elif mode == "shared_object":
        providers[1] = providers[0]
    else:
        providers[0].client = providers[1].client = object()
    result = await engine(providers).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and not events


@pytest.mark.anyio
async def test_structurally_incomplete_candidate_skips_assessment(composition):
    inputs, providers, events, _ = composition
    # Valid schema with forged authority and invalid structural references.
    providers[0].response = json.dumps({"statement": "Approved", "premise_ids": ["fake"],
        "relationship_references": [], "qualifications": [],
        "generator_metadata": {"semantic_grounding_verified": True, "release_authorized": True}})
    result = await engine(providers).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and events == ["generation"]


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
@pytest.mark.parametrize("mutation", ["source", "relationship", "catalog_epoch", "scope_epoch", "client"])
async def test_mutation_after_each_await_invalidates_entire_result(composition, stage, mutation):
    inputs, providers, events, _ = composition
    async def mutate():
        if mutation == "source":
            inputs["sources"][0].text += " changed"
        elif mutation == "relationship":
            inputs["relationships"][0].basis += " changed"
        elif mutation == "catalog_epoch":
            reader = inputs["catalog_reader"]
            reader.value = reader.value.model_copy(update={"revision": reader.value.revision + 1})
        elif mutation == "scope_epoch":
            reader = inputs["authority_reader"]
            reader.value = reader.value.model_copy(update={"scope_epoch": reader.value.scope_epoch + 1})
        else:
            providers[0].client = object()
    providers[stage].hook = mutate
    result = await engine(providers).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and len(events) == stage + 1


@pytest.mark.anyio
@pytest.mark.parametrize("limits,expected_calls", [
    (OfflineBudgetLimits(total_calls=0), 0), (OfflineBudgetLimits(total_calls=1), 1),
    (OfflineBudgetLimits(total_calls=2), 2), (OfflineBudgetLimits(max_request_bytes=1), 0),
    (OfflineBudgetLimits(max_response_bytes=1), 1), (OfflineBudgetLimits(total_request_bytes=1), 0),
    (OfflineBudgetLimits(total_response_bytes=1), 1)])
async def test_shared_caps_never_dispatch_past_limit(composition, limits, expected_calls):
    inputs, providers, events, _ = composition
    result = await engine(providers, limits=limits).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and len(events) == expected_calls


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
async def test_caller_cancellation_and_late_response_cannot_return_answer(composition, stage):
    inputs, providers, events, _ = composition
    entered, release, late = asyncio.Event(), asyncio.Event(), asyncio.Event()
    async def resist():
        entered.set()
        try:
            await release.wait()
        except asyncio.CancelledError:
            await release.wait()
        late.set()
    providers[stage].hook = resist
    task = asyncio.create_task(engine(providers).evaluate_fixture(**inputs))
    await asyncio.wait_for(entered.wait(), 1)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    release.set()
    await asyncio.wait_for(late.wait(), 1)
    await asyncio.sleep(0)
    assert len(events) == stage + 1


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
async def test_timeout_quarantines_late_completion(composition, stage):
    inputs, providers, events, _ = composition
    release, late = asyncio.Event(), asyncio.Event()
    async def resist():
        try:
            await release.wait()
        except asyncio.CancelledError:
            await release.wait()
        late.set()
    providers[stage].hook = resist
    result = await engine(providers, limits=OfflineBudgetLimits(per_call_timeout_seconds=0.02)).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and result.rejection_reasons == ("provider_timeout",)
    release.set()
    await asyncio.wait_for(late.wait(), 1)
    await asyncio.sleep(0)
    assert not result.preview_allowed and len(events) == stage + 1


@pytest.mark.anyio
@pytest.mark.parametrize("stage", [0, 1, 2])
async def test_aggregate_deadline_is_shared(composition, stage):
    inputs, providers, events, _ = composition
    class Clock:
        value = 100.0
        def __call__(self): return self.value
    clock = Clock()
    async def expire():
        clock.value += 3.0
    providers[stage].hook = expire
    result = await engine(providers, clock=clock).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and result.rejection_reasons == ("request_deadline_exceeded",)
    assert len(events) == stage + 1


def test_cache_replay_rejects_mismatched_receipts():
    with pytest.raises(ValueError):
        _GenerationReplay("{}", "{}").generate(premises=[], relationships=[])
    with pytest.raises(ValueError):
        _StatementReplay("{}", "{}").assess(request=SemanticAdmissibilityRequest(
            statement="fixture", qualifications=(), premises=(), relationships=()))
    from evaluation.governed_answers.presentation_guard import RelevanceRequest
    with pytest.raises(ValueError):
        _RelevanceReplay("{}", "{}").assess(request=RelevanceRequest(context_json='{"question":"different"}'))


@pytest.mark.anyio
async def test_reused_coordinator_allocates_fresh_request_budgets(composition):
    inputs, providers, events, _ = composition
    coordinator = engine(providers)
    first = await coordinator.evaluate_fixture(**inputs)
    second = await coordinator.evaluate_fixture(**inputs)
    assert first.preview_allowed and second.preview_allowed
    assert closed(first)["fixture_text"] == closed(second)["fixture_text"]
    assert [len(p.requests) for p in providers] == [2, 2, 2]


@pytest.mark.anyio
@pytest.mark.parametrize("stage", ["generation", "statement_assessment", "relevance_assessment"])
@pytest.mark.parametrize("tamper", ["hash", "missing_response"])
async def test_unbound_or_missing_stage_receipt_withholds(composition, monkeypatch, stage, tamper):
    from dataclasses import replace
    from evaluation.governed_answers.provider_budget_guard import OfflineProviderBudget
    original = OfflineProviderBudget.execute
    async def changed(self, **kwargs):
        result = await original(self, **kwargs)
        if kwargs["stage"] == stage:
            if tamper == "missing_response":
                return replace(result, response_json=None)
            report = result.report()
            report["request_sha256"] = "0" * 64
            return replace(result, report_json=json.dumps(report))
        return result
    monkeypatch.setattr(OfflineProviderBudget, "execute", changed)
    inputs, providers, events, _ = composition
    result = await engine(providers).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and result.rejection_reasons == ("async_receipt_unbound",)
    assert len(events) == ["generation", "statement_assessment", "relevance_assessment"].index(stage) + 1


@pytest.mark.anyio
async def test_stale_response_cannot_pass_existing_structural_gate(composition):
    inputs, providers, events, _ = composition
    original = providers[0].fixture.generate
    def stale(**kwargs):
        response = original(**kwargs)
        data = json.loads(response.content)
        data["premise_ids"] = ["prior-request-premise"]
        return response.model_copy(update={"content": json.dumps(data)})
    providers[0].fixture.generate = stale
    result = await engine(providers).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and events == ["generation"]


@pytest.mark.anyio
async def test_expiry_during_finalization_withholds_all_completed_receipts(composition):
    inputs, providers, events, _ = composition
    class Clock:
        value = 100.0
        def __call__(self): return self.value
    clock = Clock()
    reader = inputs["catalog_reader"]
    read = reader.read
    final_reads = 0
    async def arm():
        def expire_after_post_stage_recheck():
            nonlocal final_reads
            final_reads += 1
            # The first three reads are the post-relevance preflight.
            # Expire while the final scoped presentation is being assembled.
            if final_reads == 4:
                clock.value += 3.0
            return read()
        reader.read = expire_after_post_stage_recheck
    providers[2].hook = arm
    result = await engine(providers, clock=clock).evaluate_fixture(**inputs)
    report = closed(result)
    assert not result.preview_allowed and result.rejection_reasons == ("request_deadline_exceeded",)
    assert len(events) == len(report["async_coordinator"]["stage_receipts"]) == 3


@pytest.mark.anyio
async def test_catalog_change_during_final_presentation_withholds(composition):
    inputs, providers, events, _ = composition
    reader = inputs["catalog_reader"]
    read = reader.read
    final_reads = 0
    async def arm():
        def changed():
            nonlocal final_reads
            final_reads += 1
            if final_reads == 5:
                reader.value = reader.value.model_copy(update={"revision": reader.value.revision + 1})
            return read()
        reader.read = changed
    providers[2].hook = arm
    result = await engine(providers).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and len(events) == 3


@pytest.mark.anyio
@pytest.mark.parametrize("clock_value,reason", [(103.0, "request_deadline_exceeded"), (99.0, "invalid_clock")])
async def test_expiry_or_invalid_clock_inside_final_receipt_validation(composition, monkeypatch, clock_value, reason):
    from evaluation.governed_answers import provider_budget_guard
    inputs, providers, events, _ = composition
    class Clock:
        value = 100.0
        def __call__(self): return self.value
    clock = Clock()
    snapshot = provider_budget_guard._snapshot
    def late_snapshot(evaluation):
        result = snapshot(evaluation)
        clock.value = clock_value
        return result
    monkeypatch.setattr(provider_budget_guard, "_snapshot", late_snapshot)
    result = await engine(providers, clock=clock).evaluate_fixture(**inputs)
    closed(result)
    assert not result.preview_allowed and result.rejection_reasons == (reason,)
    assert len(events) == 3
