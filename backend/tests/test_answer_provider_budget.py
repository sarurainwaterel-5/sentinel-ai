"""Offline resource/timeout enforcement; no real provider, token or cost evidence."""
import asyncio
import importlib.util
import json
from pathlib import Path

import pytest

from evaluation.governed_answers.provider_budget_guard import (
    BudgetedStageResult, OfflineBudgetLimits, OfflineProviderBudget, ScriptedProviderFailure,
)
from evaluation.governed_answers.presentation_guard import RelevanceVerdict, guard_fixture

CANDIDATE = json.dumps({"statement":"The supplied reports disagree about approval.",
    "premise_ids":["p1","p2"],"relationship_references":[],"qualifications":[],"generator_metadata":{}})
CHECKS = ("unsupported_fact", "certainty_inflation", "causal_overreach", "negation_reversal",
          "fabricated_precision", "conflict_suppression", "unsupported_qualification", "insufficient_support")
VERDICT = json.dumps({"admissible":True, **{code:False for code in CHECKS}, "rejection_reasons":[]})


@pytest.fixture
def anyio_backend():
    return "asyncio"


class Provider:
    execution_source = "unit_test"

    def __init__(self, response=CANDIDATE):
        self.response = response
        self.calls = 0
        self.requests = []

    async def call(self, *, request):
        self.calls += 1
        self.requests.append(request)
        return self.response


class Clock:
    def __init__(self): self.value = 100.0
    def __call__(self): return self.value


def assert_closed(result):
    report = result.report()
    for key in ("empirical_acceptance", "release_authorized", "production_enabled", "semantic_grounding_verified"):
        assert report[key] is False
    assert report["proposition_to_inference"] == "closed"
    assert result.empirical_acceptance is False and result.release_authorized is False
    if result.status == "blocked": assert result.response_json is None


@pytest.mark.anyio
async def test_all_three_stages_share_one_budget_and_no_authority():
    budget = OfflineProviderBudget()
    generation = await budget.execute(stage="generation", request_json='{"premises":[]}', provider=Provider())
    statement = await budget.execute(stage="statement_assessment", request_json='{"candidate":"fixture"}', provider=Provider(VERDICT))
    class Relevance(Provider):
        async def call(self, *, request):
            self.calls += 1
            return RelevanceVerdict(request_sha256=request.request_sha256, answers_question=True,
                uncertain=False, reason="Scripted relevance.").model_dump_json()
    relevance = await budget.execute(stage="relevance_assessment", request_json='{"question":"Fixture?"}', provider=Relevance())
    for result in (generation,statement,relevance):
        assert result.status == "completed"
        assert_closed(result)
    assert relevance.report()["calls"] == {"generation":1,"statement_assessment":1,"relevance_assessment":1}
    assert relevance.report()["total_calls"] == 3
    assert generation.response_json == CANDIDATE


@pytest.mark.anyio
async def test_stage_and_total_caps_deny_before_call_and_close_session():
    for limits in (OfflineBudgetLimits(generation_calls=0), OfflineBudgetLimits(total_calls=0)):
        provider = Provider()
        budget = OfflineProviderBudget(limits)
        result = await budget.execute(stage="generation", request_json="{}", provider=provider)
        assert result.reason == "call_limit_exceeded" and provider.calls == 0
        assert_closed(result)
        second = await budget.execute(stage="statement_assessment", request_json="{}", provider=provider)
        assert second.status == "blocked" and provider.calls == 0
    budget = OfflineProviderBudget(OfflineBudgetLimits(total_calls=1))
    await budget.execute(stage="generation", request_json="{}", provider=Provider())
    provider = Provider(VERDICT)
    denied = await budget.execute(stage="statement_assessment", request_json="{}", provider=provider)
    assert denied.reason == "call_limit_exceeded" and provider.calls == 0


@pytest.mark.anyio
async def test_successful_stage_cannot_be_retried_past_its_cap():
    budget = OfflineProviderBudget()
    provider = Provider()
    assert (await budget.execute(stage="generation",request_json="{}",provider=provider)).status == "completed"
    denied = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert denied.reason == "call_limit_exceeded" and provider.calls == 1


@pytest.mark.anyio
@pytest.mark.parametrize("payload", [None, {}, "[]", "not json", '{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'])
async def test_malformed_requests_never_invoke_provider(payload):
    provider = Provider()
    result = await OfflineProviderBudget().execute(stage="generation",request_json=payload,provider=provider)
    assert result.reason == "request_malformed" and provider.calls == 0
    assert_closed(result)


@pytest.mark.anyio
async def test_canonical_request_hash_and_utf8_limits():
    provider = Provider()
    budget = OfflineProviderBudget()
    result = await budget.execute(stage="generation",request_json=' { "b": 2, "a": "é" } ',provider=provider)
    assert result.status == "completed"
    assert provider.requests[0].content_json == '{"a":"é","b":2}'
    assert result.report()["request_bytes"] == len('{"a":"é","b":2}'.encode())
    limited = Provider()
    denied = await OfflineProviderBudget(OfflineBudgetLimits(max_request_bytes=10)).execute(
        stage="generation",request_json='{"text":"éééé"}',provider=limited)
    assert denied.reason == "request_size_exceeded" and limited.calls == 0


@pytest.mark.anyio
async def test_aggregate_request_bytes_are_shared():
    budget = OfflineProviderBudget(OfflineBudgetLimits(total_request_bytes=3))
    assert (await budget.execute(stage="generation",request_json="{}",provider=Provider())).status == "completed"
    provider = Provider(VERDICT)
    denied = await budget.execute(stage="statement_assessment",request_json="{}",provider=provider)
    assert denied.reason == "request_size_exceeded" and provider.calls == 0


@pytest.mark.anyio
async def test_response_caps_discard_entire_reply_without_truncation():
    provider = Provider()
    budget = OfflineProviderBudget(OfflineBudgetLimits(max_response_bytes=10))
    result = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert result.reason == "response_size_exceeded" and result.response_json is None
    assert result.report()["observed_response_bytes"] == len(CANDIDATE.encode())
    budget = OfflineProviderBudget(OfflineBudgetLimits(total_response_bytes=len(CANDIDATE.encode())+1))
    assert (await budget.execute(stage="generation",request_json="{}",provider=Provider())).status == "completed"
    result = await budget.execute(stage="statement_assessment",request_json="{}",provider=Provider(VERDICT))
    assert result.reason == "response_size_exceeded"
    assert_closed(result)


@pytest.mark.anyio
@pytest.mark.parametrize("response", [None, {}, 1, "", "[]", "{}", "broken", '{"statement":"a","statement":"b"}', '{"x":NaN}'])
async def test_malformed_generation_response_closes_budget_without_retry(response):
    provider = Provider(response)
    budget = OfflineProviderBudget()
    result = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert result.status == "blocked" and result.response_json is None
    again = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert again.status == "blocked" and provider.calls == 1
    assert_closed(result)


@pytest.mark.anyio
async def test_inconsistent_statement_and_unbound_relevance_verdicts_fail_closed():
    contradictory = json.loads(VERDICT)
    contradictory["unsupported_fact"] = True
    statement = await OfflineProviderBudget().execute(stage="statement_assessment",request_json="{}",provider=Provider(json.dumps(contradictory)))
    relevance = await OfflineProviderBudget().execute(stage="relevance_assessment",request_json="{}",provider=Provider(
        RelevanceVerdict(request_sha256="0"*64, answers_question=True, uncertain=False, reason="Unbound.").model_dump_json()))
    for result in (statement,relevance):
        assert result.reason == "response_malformed_or_unbound"
        assert_closed(result)


@pytest.mark.anyio
@pytest.mark.parametrize("reason", ["unavailable", "refused", "unexpected", "mutated"])
async def test_failures_are_bounded_and_permanently_stop_calls(reason):
    class Failing(Provider):
        async def call(self, *, request):
            self.calls += 1
            if reason == "unexpected": raise RuntimeError("private provider detail")
            failure = ScriptedProviderFailure("unavailable" if reason == "mutated" else reason)
            if reason == "mutated": failure.reason = "private provider detail"
            raise failure
    provider = Failing()
    budget = OfflineProviderBudget()
    result = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert result.status == "blocked" and "private provider detail" not in result.report_json
    await budget.execute(stage="statement_assessment",request_json="{}",provider=provider)
    assert provider.calls == 1
    assert_closed(result)


@pytest.mark.anyio
async def test_per_call_timeout_cancels_cooperative_provider_and_drops_output():
    cancelled = asyncio.Event()
    class Waiting(Provider):
        async def call(self, *, request):
            self.calls += 1
            try: await asyncio.Event().wait()
            finally: cancelled.set()
    provider = Waiting()
    budget = OfflineProviderBudget(OfflineBudgetLimits(per_call_timeout_seconds=0.02))
    result = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert result.reason == "provider_timeout" and result.response_json is None
    await asyncio.wait_for(cancelled.wait(),0.2)
    assert_closed(result)
    denied = await budget.execute(stage="statement_assessment",request_json="{}",provider=provider)
    assert denied.status == "blocked" and provider.calls == 1


@pytest.mark.anyio
async def test_late_cancellation_resistant_reply_is_quarantined_not_accepted():
    release = asyncio.Event()
    cancellation_seen = asyncio.Event()
    completed = asyncio.Event()
    class Late(Provider):
        async def call(self, *, request):
            self.calls += 1
            try: await asyncio.Event().wait()
            except asyncio.CancelledError:
                cancellation_seen.set()
                await release.wait()
                completed.set()
                return CANDIDATE
    provider = Late()
    budget = OfflineProviderBudget(OfflineBudgetLimits(per_call_timeout_seconds=0.02))
    try:
        result = await budget.execute(stage="generation",request_json="{}",provider=provider)
        assert result.reason == "provider_timeout" and result.response_json is None
        await asyncio.wait_for(cancellation_seen.wait(),0.2)
        denied = await budget.execute(stage="generation",request_json="{}",provider=provider)
        assert denied.status == "blocked" and provider.calls == 1
    finally:
        release.set()
        await asyncio.wait_for(completed.wait(),0.2)
        await asyncio.sleep(0)
    assert result.response_json is None
    assert_closed(result)


@pytest.mark.anyio
async def test_overall_request_deadline_limits_first_call_and_following_stages():
    class Waiting(Provider):
        async def call(self, *, request):
            await asyncio.Event().wait()
    result = await OfflineProviderBudget(OfflineBudgetLimits(
        request_timeout_seconds=0.02,per_call_timeout_seconds=1.0)).execute(
        stage="generation",request_json="{}",provider=Waiting())
    assert result.reason == "request_deadline_exceeded"
    clock = Clock()
    budget = OfflineProviderBudget(clock=clock)
    clock.value += 3
    provider = Provider()
    result = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert result.reason == "request_deadline_exceeded" and provider.calls == 0


@pytest.mark.anyio
async def test_late_completed_result_is_discarded_by_monotonic_deadline():
    clock = Clock()
    class Late(Provider):
        async def call(self, *, request):
            clock.value += 1.0
            return CANDIDATE
    result = await OfflineProviderBudget(clock=clock).execute(stage="generation",request_json="{}",provider=Late())
    assert result.reason == "provider_timeout" and result.response_json is None


@pytest.mark.anyio
@pytest.mark.parametrize("value", [99.0, float("nan"), float("inf"), True])
async def test_invalid_or_backward_clock_cannot_expand_deadlines(value):
    clock = Clock()
    budget = OfflineProviderBudget(clock=clock)
    clock.value = value
    provider = Provider()
    result = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert result.reason == "invalid_clock" and provider.calls == 0


@pytest.mark.anyio
async def test_concurrent_calls_cannot_bypass_caps_or_release_first_result():
    started = asyncio.Event()
    class Waiting(Provider):
        async def call(self, *, request):
            self.calls += 1
            started.set()
            await asyncio.Event().wait()
    first_provider = Waiting()
    second_provider = Provider(VERDICT)
    budget = OfflineProviderBudget()
    first = asyncio.create_task(budget.execute(stage="generation",request_json="{}",provider=first_provider))
    await asyncio.wait_for(started.wait(),0.2)
    second = await budget.execute(stage="statement_assessment",request_json="{}",provider=second_provider)
    completed = await asyncio.wait_for(first,0.2)
    assert second.reason == completed.reason == "concurrent_call_not_allowed"
    assert first_provider.calls == 1 and second_provider.calls == 0
    assert_closed(second)
    assert_closed(completed)


@pytest.mark.anyio
async def test_parent_cancellation_stops_budget_and_cancels_provider():
    started = asyncio.Event()
    stopped = asyncio.Event()
    class Waiting(Provider):
        async def call(self, *, request):
            started.set()
            try: await asyncio.Event().wait()
            finally: stopped.set()
    budget = OfflineProviderBudget()
    task = asyncio.create_task(budget.execute(stage="generation",request_json="{}",provider=Waiting()))
    await asyncio.wait_for(started.wait(),0.2)
    task.cancel()
    with pytest.raises(asyncio.CancelledError): await task
    await asyncio.wait_for(stopped.wait(),0.2)
    denied = await budget.execute(stage="generation",request_json="{}",provider=Provider())
    assert denied.reason == "request_cancelled"


@pytest.mark.anyio
async def test_provider_self_cancellation_is_a_blocked_result():
    class Cancelled(Provider):
        async def call(self, *, request): raise asyncio.CancelledError()
    result = await OfflineProviderBudget().execute(stage="generation",request_json="{}",provider=Cancelled())
    assert result.reason == "provider_cancelled"
    assert_closed(result)


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["missing", "non_scripted", "synchronous"])
async def test_only_explicit_async_scripted_providers_are_called(mode):
    provider = Provider()
    if mode == "missing": provider = None
    elif mode == "non_scripted": provider.execution_source = "actual_api"
    else:
        def call(*, request): raise AssertionError("Synchronous provider must never run")
        provider.call = call
    result = await OfflineProviderBudget().execute(stage="generation",request_json="{}",provider=provider)
    assert result.reason == "provider_not_async_scripted"
    assert_closed(result)


@pytest.mark.anyio
async def test_unknown_stages_do_not_invoke_provider_or_echo_untrusted_stage():
    provider = Provider()
    result = await OfflineProviderBudget().execute(stage=["private"],request_json="{}",provider=provider)
    assert result.reason == "unknown_stage" and provider.calls == 0
    assert result.report()["stage"] == "unknown"


@pytest.mark.anyio
async def test_successful_negative_verdict_delivery_does_not_approve_a_preview():
    spec = importlib.util.spec_from_file_location("budget_fixture_helpers",
        Path(__file__).parent / "services/cognition/reasoning/test_answer_orchestrator.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    engine, _, _ = helpers.coordinator()
    raw = engine.evaluate_fixture(**helpers.fixture())
    class Capture:
        execution_source = "unit_test"
        def assess(self, *, request):
            self.request = request
            return RelevanceVerdict(request_sha256=request.request_sha256,answers_question=False,
                uncertain=False,reason="Scripted question not answered.")
    capture = Capture()
    guard_fixture(raw,assessor=capture)
    response = capture.assess(request=capture.request).model_dump_json()
    delivered = await OfflineProviderBudget().execute(stage="relevance_assessment",
        request_json=capture.request.context_json,provider=Provider(response))
    assert delivered.status == "completed"
    class Cached:
        execution_source = "unit_test"
        def assess(self, *, request): return RelevanceVerdict.model_validate_json(delivered.response_json,strict=True)
    guarded = guard_fixture(raw,assessor=Cached())
    assert guarded.preview_allowed is False
    assert guarded.rejection_reasons == ("fixture_question_not_answered",)
    assert_closed(delivered)


@pytest.mark.parametrize("values", [
    {"total_calls":True}, {"generation_calls":-1}, {"per_call_timeout_seconds":float("nan")},
    {"per_call_timeout_seconds":0.0}, {"request_timeout_seconds":float("inf")},
    {"max_response_bytes":0}, {"retry_count":1}, {"production_enabled":True},
])
def test_invalid_budget_and_authority_options_are_rejected(values):
    with pytest.raises(ValueError): OfflineBudgetLimits(**values)


def test_result_cannot_be_constructed_with_release_or_empirical_authority():
    for field in ("empirical_acceptance","production_enabled","release_authorized"):
        with pytest.raises(TypeError):
            BudgetedStageResult(status="completed",response_json=CANDIDATE,reason=None,
                                report_json="{}",**{field:True})


def preview_fixture():
    spec = importlib.util.spec_from_file_location("budget_preview_helpers",
        Path(__file__).parent / "services/cognition/reasoning/test_answer_orchestrator.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    engine, generator, judge = helpers.coordinator()
    raw = engine.evaluate_fixture(**helpers.fixture())
    class Positive:
        execution_source = "unit_test"
        def assess(self, *, request):
            self.request = request
            return RelevanceVerdict(request_sha256=request.request_sha256,answers_question=True,
                                   uncertain=False,reason="Scripted positive display relevance.")
    assessor = Positive()
    presentation = guard_fixture(raw,assessor=assessor)
    return raw, generator.untrusted_candidate, judge.requests[0], assessor.request, presentation


async def receipts(budget, fixture, change=None):
    raw, candidate, statement_request, relevance_request, _ = fixture
    generation_request = {"premises":[p.model_dump(mode="json") for p in raw.public_response.premises],
                          "relationships":[r.model_dump(mode="json") for r in raw.public_response.relationships]}
    generation_content = candidate.model_dump_json()
    if change == "generation_request": generation_request["unbound"] = True
    if change == "candidate":
        data = json.loads(generation_content)
        data["statement"] = "A different candidate."
        generation_content = json.dumps(data)
    assert (await budget.execute(stage="generation",request_json=json.dumps(generation_request),provider=Provider(generation_content))).status == "completed"
    statement_json = statement_request.model_dump_json()
    if change == "statement_request": statement_json = '{}'
    verdict = VERDICT
    if change == "statement_rejected":
        data = json.loads(verdict)
        data.update(admissible=False,unsupported_fact=True,rejection_reasons=["unsupported_fact"])
        verdict = json.dumps(data)
    assert (await budget.execute(stage="statement_assessment",request_json=statement_json,provider=Provider(verdict))).status == "completed"
    relevance_json = relevance_request.context_json
    if change == "relevance_request":
        data = json.loads(relevance_json)
        data["question"] = "A different question?"
        relevance_json = json.dumps(data)
    class Positive(Provider):
        async def call(self, *, request):
            return RelevanceVerdict(request_sha256=request.request_sha256,
                answers_question=change != "relevance_negative",uncertain=change == "relevance_uncertain",
                reason="Scripted relevance receipt.").model_dump_json()
    assert (await budget.execute(stage="relevance_assessment",request_json=relevance_json,provider=Positive())).status == "completed"


def withheld_presentation(result):
    assert result.preview_allowed is False
    report = result.to_component_report()
    assert report["fixture_claim"] is None and report["fixture_text"] is None
    assert report["public_response"] is None
    assert report["provider_budget_guard"]["release_authorized"] is False
    assert report["provider_budget_guard"]["production_enabled"] is False


@pytest.mark.anyio
async def test_complete_snapshot_bound_receipts_preserve_exact_preview_and_seal_budget():
    fixture = preview_fixture()
    budget = OfflineProviderBudget()
    await receipts(budget,fixture)
    result = budget.guard_presentation(fixture[-1])
    assert result.preview_allowed is True
    report = result.to_component_report()
    assert report["fixture_claim"] == fixture[-1].to_component_report()["fixture_claim"]
    assert report["fixture_text"] == fixture[0].fixture_text
    assert report["public_response"]["answer_text"] is None and report["public_response"]["claims"] == []
    assert report["provider_budget_guard"]["total_calls"] == 3
    assert report["provider_budget_guard"]["status"] == "passed_offline_budget"
    provider = Provider()
    denied = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert denied.reason == "budget_finalized" and provider.calls == 0
    withheld_presentation(budget.guard_presentation(fixture[-1]))


@pytest.mark.anyio
@pytest.mark.parametrize("change", ["generation_request", "candidate", "statement_request", "statement_rejected",
                                   "relevance_request", "relevance_negative", "relevance_uncertain"])
async def test_transport_completion_cannot_promote_unbound_or_rejected_preview(change):
    fixture = preview_fixture()
    budget = OfflineProviderBudget()
    await receipts(budget,fixture,change)
    result = budget.guard_presentation(fixture[-1])
    assert result.rejection_reasons == ("presentation_budget_unbound_or_rejected",)
    withheld_presentation(result)


@pytest.mark.anyio
async def test_missing_receipts_and_late_finalization_withhold_existing_preview():
    fixture = preview_fixture()
    budget = OfflineProviderBudget()
    withheld_presentation(budget.guard_presentation(fixture[-1]))
    clock = Clock()
    budget = OfflineProviderBudget(clock=clock)
    await receipts(budget,fixture)
    clock.value += 3.0
    result = budget.guard_presentation(fixture[-1])
    assert result.rejection_reasons == ("request_deadline_exceeded",)
    withheld_presentation(result)


@pytest.mark.anyio
async def test_failed_budget_cannot_use_earlier_candidate_or_external_preview_as_fallback():
    fixture = preview_fixture()
    budget = OfflineProviderBudget()
    result = await budget.execute(stage="generation",request_json="{}",provider=Provider('broken'))
    assert result.status == "blocked"
    withheld_presentation(budget.guard_presentation(fixture[-1]))


@pytest.mark.anyio
async def test_finalized_display_snapshot_cannot_be_changed_by_caller_mutation():
    fixture = preview_fixture()
    budget = OfflineProviderBudget()
    await receipts(budget,fixture)
    result = budget.guard_presentation(fixture[-1])
    report = result.to_component_report()
    report["fixture_text"] = "Invented"
    assert result.to_component_report()["fixture_text"] == fixture[0].fixture_text


@pytest.mark.anyio
async def test_numeric_overflow_in_untrusted_metadata_is_rejected():
    response = CANDIDATE.replace('"generator_metadata": {}','"generator_metadata": {"overflow":1e999}')
    result = await OfflineProviderBudget().execute(stage="generation",request_json="{}",provider=Provider(response))
    assert result.reason == "response_malformed_or_unbound"


@pytest.mark.anyio
async def test_callback_cannot_rebind_stored_request_receipt():
    import hashlib
    class Mutating(Provider):
        async def call(self, *, request):
            object.__setattr__(request,"content_json",'{"question":"Changed"}')
            object.__setattr__(request,"request_sha256",hashlib.sha256(request.content_json.encode()).hexdigest())
            return RelevanceVerdict(request_sha256=request.request_sha256,answers_question=True,
                uncertain=False,reason="Mutated request.").model_dump_json()
    result = await OfflineProviderBudget().execute(stage="relevance_assessment",request_json="{}",provider=Mutating())
    assert result.reason == "response_malformed_or_unbound"
    assert result.report()["request_sha256"] == hashlib.sha256(b"{}").hexdigest()
    assert_closed(result)


@pytest.mark.anyio
async def test_generation_callback_cannot_also_be_its_assessor():
    provider = Provider()
    budget = OfflineProviderBudget()
    assert (await budget.execute(stage="generation",request_json="{}",provider=provider)).status == "completed"
    provider.response = VERDICT
    denied = await budget.execute(stage="statement_assessment",request_json="{}",provider=provider)
    assert denied.reason == "generation_assessment_provider_shared" and provider.calls == 1
    assert_closed(denied)


@pytest.mark.anyio
async def test_assessment_callback_cannot_later_be_used_for_generation():
    provider = Provider(VERDICT)
    budget = OfflineProviderBudget()
    assert (await budget.execute(stage="statement_assessment",request_json="{}",provider=provider)).status == "completed"
    provider.response = CANDIDATE
    denied = await budget.execute(stage="generation",request_json="{}",provider=provider)
    assert denied.reason == "generation_assessment_provider_shared" and provider.calls == 1
    assert_closed(denied)


@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["root_release", "guard_enable", "inference", "source_scope_claim"])
async def test_forged_authority_metadata_cannot_pass_final_budget_guard(mode):
    from evaluation.governed_answers.presentation_guard import GuardedPresentation
    fixture = preview_fixture()
    budget = OfflineProviderBudget()
    await receipts(budget,fixture)
    report = fixture[-1].to_component_report()
    if mode == "root_release": report["release_authorized"] = True
    elif mode == "guard_enable": report["presentation_guard"]["production_enabled"] = True
    elif mode == "inference": report["proposition_to_inference"] = "open"
    else: report["evidence_scope_guard"] = {"fixture_scope_checked":True,"release_authorized":True}
    forged = GuardedPresentation(report_json=json.dumps(report),preview_allowed=True,rejection_reasons=())
    result = budget.guard_presentation(forged)
    withheld_presentation(result)
    assert result.rejection_reasons == ("presentation_budget_unbound_or_rejected",)


@pytest.mark.anyio
async def test_budget_finalization_composes_with_real_offline_scope_and_relevance_guards():
    import hashlib
    from app.services.cognition.reasoning.answer_models import AnswerClaim, GovernedAnswer
    from app.services.cognition.reasoning.answer_orchestrator import OfflineAnswerEvaluation
    from evaluation.governed_answers.presentation_guard import _snapshot
    from evaluation.governed_answers.evidence_scope_guard import (
        OperatorScopeFixture, CatalogDocumentFixture, CatalogSnapshotFixture, evaluate_scoped_fixture,
    )
    spec = importlib.util.spec_from_file_location("budget_scoped_helpers",
        Path(__file__).parent / "services/cognition/reasoning/test_answer_orchestrator.py")
    helpers = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helpers)
    data = helpers.fixture()
    for source in data["sources"]: source.file_hash = "a"*64
    engine, generator, judge = helpers.coordinator()
    class Reader:
        execution_source = "unit_test"
        def __init__(self,value): self.value=value
        def read(self): return self.value
    authority = OperatorScopeFixture(operator_id="scripted",organization_id="org",collection="knowledge",
        allowed_modules=("engineering",),allowed_topics=("policy",),scope_epoch=1)
    document = CatalogDocumentFixture(document_id="doc",organization_id="org",collection="knowledge",
        module="engineering",topic="policy",status="indexed",file_hash="a"*64,version_epoch=1,
        chunk_hashes=tuple(hashlib.sha256(s.text.encode()).hexdigest() for s in data["sources"]))
    class Positive:
        execution_source = "unit_test"
        def assess(self,*,request):
            return RelevanceVerdict(request_sha256=request.request_sha256,answers_question=True,
                                   uncertain=False,reason="Scripted positive.")
    scoped = evaluate_scoped_fixture(**{k:data[k] for k in ("question","scope","collection","sources","relationships")},
        authority_reader=Reader(authority),catalog_reader=Reader(CatalogSnapshotFixture(revision=1,documents=(document,))),
        coordinator=engine,relevance_assessor=Positive())
    assert scoped.preview_allowed is True
    report = scoped.to_component_report()
    raw = OfflineAnswerEvaluation(public_response=GovernedAnswer.model_validate_json(json.dumps(report["public_response"]),strict=True),
        fixture_claim=AnswerClaim.model_validate_json(json.dumps(report["fixture_claim"]),strict=True),fixture_text=report["fixture_text"])
    _,_,_,relevance_request = _snapshot(raw)
    fixture = (raw,generator.untrusted_candidate,judge.requests[0],relevance_request,scoped)
    budget = OfflineProviderBudget()
    await receipts(budget,fixture)
    final = budget.guard_presentation(scoped)
    assert final.preview_allowed is True
    assert final.to_component_report()["fixture_text"] == raw.fixture_text
    assert final.to_component_report()["evidence_scope_guard"]["production_authenticated_scope_verified"] is False
    assert final.to_component_report()["provider_budget_guard"]["release_authorized"] is False
