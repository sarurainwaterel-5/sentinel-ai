"""Adversarial offline presentation eligibility, not real relevance measurements."""
import dataclasses
import importlib.util
import json
from pathlib import Path

import pytest

from evaluation.governed_answers.presentation_guard import (
    GuardedPresentation, RelevanceAssessmentFailure, RelevanceVerdict, guard_fixture,
)
from app.services.cognition.reasoning.answer_models import AnswerClaim, GovernedAnswer
from app.services.cognition.reasoning.answer_orchestrator import OfflineAnswerEvaluation

# Reuse the existing committed coordinator's scripted setup without changing it.
HELPERS = Path(__file__).parent / "services/cognition/reasoning/test_answer_orchestrator.py"
spec = importlib.util.spec_from_file_location("presentation_guard_fixture_helpers", HELPERS)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


class Assessment:
    execution_source = "unit_test"

    def __init__(self, answers=True, uncertain=False):
        self.answers = answers
        self.uncertain = uncertain
        self.calls = 0
        self.request = None

    def assess(self, *, request):
        self.calls += 1
        self.request = request
        return RelevanceVerdict(request_sha256=request.request_sha256,
                                answers_question=self.answers, uncertain=self.uncertain,
                                reason="Scripted display relevance only.")


@pytest.fixture
def raw():
    engine, _, _ = helpers.coordinator()
    return engine.evaluate_fixture(**helpers.fixture())


def assert_withheld(result):
    report = result.to_component_report()
    assert result.preview_allowed is False
    assert result.rejection_reasons
    assert report["fixture_claim"] is None and report["fixture_text"] is None
    assert result.empirical_acceptance is False and result.release_authorized is False
    assert result.production_enabled is False
    assert report["empirical_acceptance"] is False
    guard = report["presentation_guard"]
    assert guard["status"] == "withheld"
    assert guard["release_authorized"] is False and guard["production_enabled"] is False
    assert guard["semantic_grounding_verified"] is False and guard["proposition_to_inference"] == "closed"
    if report["public_response"]:
        assert report["public_response"]["answer_text"] is None
        assert report["public_response"]["claims"] == []
        assert report["public_response"]["validation"]["release_status"] == "disabled"


def test_bound_positive_assessment_retains_exact_fixture_and_citations(raw):
    assessor = Assessment()
    result = guard_fixture(raw, assessor=assessor)
    report = result.to_component_report()
    assert result.preview_allowed is True and not result.rejection_reasons
    assert report["fixture_text"] == raw.fixture_text
    assert report["fixture_claim"] == raw.fixture_claim.model_dump(mode="json")
    assert report["public_response"] == raw.public_response.model_dump(mode="json")
    assert report["presentation_guard"]["request_sha256"] == assessor.request.request_sha256
    assert result.empirical_acceptance is False and result.release_authorized is False


def test_irrelevant_retention_question_is_withheld_even_when_statement_admissible():
    engine, _, _ = helpers.coordinator()
    data = helpers.fixture()
    data["question"] = "What is the Cedar backup retention period?"
    raw = engine.evaluate_fixture(**data)
    assert raw.fixture_claim.validation.statement_status == "admissible"
    result = guard_fixture(raw, assessor=Assessment(answers=False))
    assert_withheld(result)
    assert result.rejection_reasons == ("fixture_question_not_answered",)
    assert result.to_component_report()["public_response"]["outcome"] == "blocked_validation"
    assert raw.fixture_claim is not None  # frozen coordinator output is untouched


def test_missing_relevance_assessment_never_uses_admissibility_as_substitute(raw):
    result = guard_fixture(raw)
    assert_withheld(result)
    assert result.rejection_reasons == ("relevance_assessment_missing",)


@pytest.mark.parametrize("answers", [True, False])
def test_uncertainty_withholds_even_positive_verdict(raw, answers):
    result = guard_fixture(raw, assessor=Assessment(answers=answers, uncertain=True))
    assert_withheld(result)
    assert result.rejection_reasons == ("relevance_assessment_uncertain",)


@pytest.mark.parametrize("reason", ["unavailable", "refused", "timeout", "unexpected"])
def test_assessor_failures_have_no_preview_fallback(raw, reason):
    class Failing(Assessment):
        def assess(self, *, request):
            if reason == "unexpected":
                raise RuntimeError("private provider detail")
            raise RelevanceAssessmentFailure(reason)
    result = guard_fixture(raw, assessor=Failing())
    assert_withheld(result)
    assert "private provider detail" not in result.report_json


@pytest.mark.parametrize("value", [None, {}, True, "admissible", {"answers_question": True},
                                   {"request_sha256": "0" * 64, "answers_question": True}])
def test_malformed_or_partial_verdicts_do_not_allow_preview(raw, value):
    class Malformed(Assessment):
        def assess(self, *, request):
            return value
    result = guard_fixture(raw, assessor=Malformed())
    assert_withheld(result)
    assert result.rejection_reasons == ("relevance_assessment_malformed",)


@pytest.mark.parametrize("field,value", [("answers_question", 1), ("uncertain", "false"),
                                         ("reason", " "), ("request_sha256", "stale")])
def test_bypassed_model_validation_is_rechecked(raw, field, value):
    class Malformed(Assessment):
        def assess(self, *, request):
            verdict = super().assess(request=request)
            object.__setattr__(verdict, field, value)
            return verdict
    assert_withheld(guard_fixture(raw, assessor=Malformed()))


def test_verdict_for_other_request_is_rejected(raw):
    class Unbound(Assessment):
        def assess(self, *, request):
            return RelevanceVerdict(request_sha256="0" * 64, answers_question=True,
                                    uncertain=False, reason="Wrong request.")
    result = guard_fixture(raw, assessor=Unbound())
    assert_withheld(result)
    assert result.rejection_reasons == ("relevance_assessment_unbound",)


@pytest.mark.parametrize("change", ["question", "candidate", "qualification", "source_text",
                                    "scope", "snapshot", "relationships"])
def test_verdict_cannot_be_replayed_across_context_changes(raw, change):
    original = Assessment()
    guard_fixture(raw, assessor=original)
    data = helpers.fixture()
    engine, generator, _ = helpers.coordinator()
    if change == "question":
        data["question"] = "A different question?"
    elif change == "source_text":
        data["sources"][0].text = "A new fictional report says approval is required."
    elif change == "scope":
        data["scope"] = data["scope"].model_copy(update={"score_threshold": 0.6})
    elif change == "snapshot":
        data["snapshot_id"] = "new-snapshot"
    elif change == "relationships":
        data["relationships"][0].basis = "A changed fixture relationship attribution."
    else:
        original_generate = generator.generate
        def modified_generate(**kwargs):
            response = original_generate(**kwargs)
            candidate = json.loads(response.content)
            if change == "candidate":
                candidate["statement"] = "Report 0 and Report 1 disagree about approval."
            else:
                candidate["qualifications"] = ["A different bounded qualification."]
            return helpers.SemanticGenerationResponse(content=json.dumps(candidate))
        generator.generate = modified_generate
    changed = engine.evaluate_fixture(**data)
    assert changed.fixture_claim is not None
    class Replay(Assessment):
        def assess(self, *, request):
            return RelevanceVerdict(request_sha256=original.request.request_sha256,
                                    answers_question=True, uncertain=False, reason="Replayed.")
    result = guard_fixture(changed, assessor=Replay())
    assert_withheld(result)
    assert result.rejection_reasons == ("relevance_assessment_unbound",)


def test_source_mutation_during_assessment_is_detected(raw):
    class Mutating(Assessment):
        def assess(self, *, request):
            verdict = super().assess(request=request)
            object.__setattr__(raw.public_response.evidence[0], "text", "Changed source")
            return verdict
    result = guard_fixture(raw, assessor=Mutating())
    assert_withheld(result)
    assert result.rejection_reasons == ("fixture_changed_during_relevance_assessment",)


def test_callback_cannot_mutate_guard_request_to_rebind_approval(raw):
    class Mutating(Assessment):
        def assess(self, *, request):
            object.__setattr__(request, "context_json", "{}")
            return RelevanceVerdict(request_sha256=request.request_sha256,
                                    answers_question=True, uncertain=False, reason="Mutated.")
    result = guard_fixture(raw, assessor=Mutating())
    assert_withheld(result)
    assert result.rejection_reasons == ("relevance_assessment_unbound",)


def test_nested_caller_mutations_cannot_change_stored_guarded_result(raw):
    result = guard_fixture(raw, assessor=Assessment())
    report = result.to_component_report()
    report["fixture_claim"]["statement"] = "Invented"
    report["public_response"]["evidence"][0]["text"] = "Invented source"
    assert result.to_component_report()["fixture_claim"]["statement"] == raw.fixture_claim.statement
    assert result.to_component_report()["public_response"]["evidence"][0]["text"] == raw.public_response.evidence[0].text


def test_rejected_fixture_never_calls_relevance_assessor():
    engine, _, judge = helpers.coordinator()
    judge.defect = "unsupported_fact"
    raw = engine.evaluate_fixture(**helpers.fixture())
    assessor = Assessment()
    result = guard_fixture(raw, assessor=assessor)
    assert_withheld(result)
    assert assessor.calls == 0
    assert result.to_component_report()["public_response"]["outcome"] == "rejected"


@pytest.mark.parametrize("mode", ["claim_text", "rendered_text", "missing_evidence", "scope", "empirical", "unknown"])
def test_changed_or_unrecognized_input_never_calls_assessor(raw, mode):
    if mode == "claim_text":
        raw = dataclasses.replace(raw, fixture_claim=raw.fixture_claim.model_copy(update={"statement": "Changed"}))
    elif mode == "rendered_text":
        raw = dataclasses.replace(raw, fixture_text="Invented display")
    elif mode == "missing_evidence":
        raw = dataclasses.replace(raw, public_response=raw.public_response.model_copy(update={"evidence": ()}))
    elif mode == "scope":
        raw = dataclasses.replace(raw, public_response=raw.public_response.model_copy(update={"scope":raw.public_response.scope.model_copy(update={"organization_id":"other"})}))
    elif mode == "empirical":
        object.__setattr__(raw, "empirical_acceptance", True)
    else:
        raw = {}
    assessor = Assessment()
    result = guard_fixture(raw, assessor=assessor)
    assert_withheld(result)
    assert assessor.calls == 0


def test_non_scripted_assessor_rejected_before_call(raw):
    assessor = Assessment()
    assessor.execution_source = "actual_api"
    result = guard_fixture(raw, assessor=assessor)
    assert_withheld(result)
    assert assessor.calls == 0


def test_request_contains_exact_context_but_no_gold_or_generation_metadata(raw):
    assessor = Assessment()
    guard_fixture(raw, assessor=assessor)
    context = json.loads(assessor.request.context_json)
    assert context["question"] == raw.public_response.question
    assert context["candidate"]["statement"] == raw.fixture_claim.statement
    assert context["scope"] == raw.public_response.scope.model_dump()
    assert context["evidence"] == [e.model_dump() for e in raw.public_response.evidence]
    assert context["relationships"] == [r.model_dump(mode="json") for r in raw.public_response.relationships]
    assert "generator_metadata" not in context and "human_classification" not in context and "approved" not in context
    assert "validation" not in context["candidate"]


def test_no_claim_with_unvalidated_text_is_rejected(raw):
    invalid = dataclasses.replace(raw, fixture_claim=None)
    assert_withheld(guard_fixture(invalid, assessor=Assessment()))


def test_empirical_or_release_flags_cannot_be_constructor_arguments(raw):
    result = guard_fixture(raw, assessor=Assessment())
    for name in ("empirical_acceptance", "release_authorized", "production_enabled"):
        with pytest.raises(TypeError):
            GuardedPresentation(report_json=result.report_json, preview_allowed=True,
                                rejection_reasons=(), **{name:True})


@pytest.mark.parametrize("mode", ["missing_scope", "premise_lineage", "relationship_lineage"])
def test_incomplete_presentation_scope_or_claim_lineage_withholds(raw, mode):
    if mode == "missing_scope":
        changed = dataclasses.replace(raw, public_response=raw.public_response.model_copy(update={"scope":None}))
    elif mode == "premise_lineage":
        changed = dataclasses.replace(raw, fixture_claim=raw.fixture_claim.model_copy(update={"premise_ids":("foreign1", "foreign2")}))
    else:
        changed = dataclasses.replace(raw, fixture_claim=raw.fixture_claim.model_copy(update={"relationship_references":()}))
    assessor = Assessment()
    result = guard_fixture(changed, assessor=assessor)
    assert_withheld(result)
    assert assessor.calls == 0


def test_mutated_failure_reason_is_not_reflected_into_output(raw):
    class Failing(Assessment):
        def assess(self, *, request):
            failure = RelevanceAssessmentFailure("unavailable")
            failure.reason = "unbounded private detail"
            raise failure
    result = guard_fixture(raw, assessor=Failing())
    assert_withheld(result)
    assert "unbounded private detail" not in result.report_json
