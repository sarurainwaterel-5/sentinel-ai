"""Scripted permission/version enforcement, never real authentication or storage."""
import hashlib
import importlib.util
from pathlib import Path

import pytest

from app.services.cognition.reasoning.answer_models import AnswerScope
from evaluation.governed_answers.evidence_scope_guard import (
    OperatorScopeFixture, CatalogDocumentFixture, CatalogSnapshotFixture,
    ScopedFixturePresentation, evaluate_scoped_fixture,
)
from evaluation.governed_answers.presentation_guard import RelevanceVerdict

spec = importlib.util.spec_from_file_location("evidence_scope_fixture_helpers",
    Path(__file__).parent / "services/cognition/reasoning/test_answer_orchestrator.py")
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


class Reader:
    execution_source = "unit_test"

    def __init__(self, value):
        self.value = value
        self.calls = 0

    def read(self):
        self.calls += 1
        return self.value


class Relevance:
    execution_source = "unit_test"

    def __init__(self, answer=True):
        self.answer = answer
        self.calls = 0

    def assess(self, *, request):
        self.calls += 1
        return RelevanceVerdict(request_sha256=request.request_sha256,
            answers_question=self.answer, uncertain=False, reason="Scripted relevance only.")


@pytest.fixture
def setup():
    data = helpers.fixture()
    for source in data["sources"]:
        source.file_hash = "a" * 64
    engine, generator, judge = helpers.coordinator()
    authority = OperatorScopeFixture(operator_id="scripted-operator", organization_id="org",
        collection="knowledge", allowed_modules=("engineering",), allowed_topics=("policy",), scope_epoch=3)
    document = CatalogDocumentFixture(document_id="doc", organization_id="org", collection="knowledge",
        module="engineering", topic="policy", status="indexed", file_hash="a"*64, version_epoch=4,
        chunk_hashes=tuple(hashlib.sha256(s.text.encode()).hexdigest() for s in data["sources"]))
    snapshot = CatalogSnapshotFixture(revision=10, documents=(document,))
    args = {k:data[k] for k in ("question", "scope", "collection", "sources", "relationships")}
    args.update(authority_reader=Reader(authority), catalog_reader=Reader(snapshot), coordinator=engine,
                relevance_assessor=Relevance())
    return args, generator, judge


def closed(result):
    report = result.to_component_report()
    assert result.release_authorized is False and result.production_enabled is False
    assert result.empirical_acceptance is False
    assert report["empirical_acceptance"] is False
    guard = report["evidence_scope_guard"]
    assert guard["production_authenticated_scope_verified"] is False
    assert guard["release_authorized"] is False and guard["production_enabled"] is False
    assert guard["semantic_grounding_verified"] is False and guard["proposition_to_inference"] == "closed"
    if not result.preview_allowed:
        assert report["fixture_claim"] is None and report["fixture_text"] is None


def test_valid_scope_and_unchanged_catalog_allow_only_an_offline_preview(setup):
    args, generator, judge = setup
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is True
    assert generator.calls == judge.calls == args["relevance_assessor"].calls == 1
    assert args["authority_reader"].calls == args["catalog_reader"].calls == 3
    report = result.to_component_report()
    assert report["public_response"]["answer_text"] is None and report["public_response"]["claims"] == []
    assert report["evidence_scope_guard"]["fixture_scope_checked"] is True
    assert report["fixture_claim"]["statement"] == "The supplied reports disagree about approval."


@pytest.mark.parametrize("field,value", [("organization_id","other"), ("module","finance"), ("topic","secret")])
def test_requested_scope_cannot_override_operator_permissions(setup, field, value):
    args, generator, judge = setup
    args["scope"] = args["scope"].model_copy(update={field:value})
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False
    assert generator.calls == judge.calls == args["relevance_assessor"].calls == 0
    assert args["catalog_reader"].calls == 0


def test_requested_collection_denied_before_catalog_or_candidate_work(setup):
    args, generator, judge = setup
    args["collection"] = "foreign"
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False
    assert args["catalog_reader"].calls == generator.calls == judge.calls == 0


@pytest.mark.parametrize("field", ["module", "topic"])
def test_implicit_all_scope_is_not_fixture_authorization(setup, field):
    args, generator, _ = setup
    args["scope"] = args["scope"].model_copy(update={field:None})
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False and generator.calls == 0


@pytest.mark.parametrize("which", ["authority_reader", "catalog_reader"])
@pytest.mark.parametrize("mode", ["missing", "non_scripted", "malformed", "failure"])
def test_untrusted_or_unavailable_reader_fails_before_candidate_work(setup, which, mode):
    args, generator, judge = setup
    if mode == "missing":
        args[which] = None
    elif mode == "non_scripted":
        args[which].execution_source = "actual_api"
    elif mode == "malformed":
        args[which].value = {"authenticated":True}
    else:
        def failure():
            raise RuntimeError("private backend detail")
        args[which].read = failure
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False
    assert generator.calls == judge.calls == args["relevance_assessor"].calls == 0
    assert "private backend detail" not in result.report_json


@pytest.mark.parametrize("field,value", [
    ("organization_id","foreign"), ("collection","foreign"), ("module","finance"),
    ("topic","other"), ("status","archived"), ("file_hash","b"*64),
    ("text","Changed chunk text"), ("chunk_index",-1), ("chunk_index",100),
    ("document_id","missing"),
])
def test_source_scope_locator_version_or_content_failure_withholds_entire_set(setup, field, value):
    args, generator, judge = setup
    setattr(args["sources"][0], field, value)
    args["sources"][0].metadata = {"authenticated":True, "organization_id":"org"}
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False
    assert result.to_component_report()["public_response"] is None
    assert generator.calls == judge.calls == args["relevance_assessor"].calls == 0


@pytest.mark.parametrize("field,value", [
    ("organization_id","foreign"), ("collection","foreign"), ("module","finance"),
    ("topic","other"), ("status","archived"), ("status","pending"), ("status","error"),
    ("chunk_hashes",("b"*64,"c"*64)),
])
def test_catalog_scope_and_eligibility_are_authoritative(setup, field, value):
    args, generator, _ = setup
    snapshot = args["catalog_reader"].value
    document = snapshot.documents[0].model_copy(update={field:value})
    args["catalog_reader"].value = snapshot.model_copy(update={"documents":(document,)})
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False and generator.calls == 0


def test_missing_catalog_document_cannot_be_silently_dropped(setup):
    args, generator, _ = setup
    args["catalog_reader"].value = CatalogSnapshotFixture(revision=10, documents=())
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False and generator.calls == 0


def test_duplicate_locator_and_budget_overrun_do_not_truncate(setup):
    args, generator, _ = setup
    args["sources"].append(args["sources"][0].model_copy(deep=True))
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False and generator.calls == 0
    args["sources"] *= 3
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False and generator.calls == 0


@pytest.mark.parametrize("change", ["archive", "delete", "file_version", "scope", "global_revision",
                                     "archive_restore_aba", "update_revert_aba", "document_epoch"])
def test_catalog_changes_after_candidate_work_invalidate_preview_before_relevance(setup, change):
    args, generator, judge = setup
    reader = args["catalog_reader"]
    snapshot = reader.value
    document = snapshot.documents[0]
    original = generator.generate
    def changed_catalog(**kwargs):
        response = original(**kwargs)
        if change == "archive":
            reader.value = snapshot.model_copy(update={"documents":(document.model_copy(update={"status":"archived"}),)})
        elif change == "delete":
            reader.value = snapshot.model_copy(update={"documents":()})
        elif change == "file_version":
            reader.value = snapshot.model_copy(update={"documents":(document.model_copy(update={"file_hash":"b"*64,"version_epoch":5}),)})
        elif change == "scope":
            reader.value = snapshot.model_copy(update={"documents":(document.model_copy(update={"organization_id":"other"}),)})
        elif change == "document_epoch":
            reader.value = snapshot.model_copy(update={"documents":(document.model_copy(update={"version_epoch":6}),)})
        else:
            # Revision advancement models both transitions of an ABA cycle;
            # the final document bytes/status can equal the original snapshot.
            reader.value = snapshot.model_copy(update={"revision":12})
        return response
    generator.generate = changed_catalog
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False
    assert result.rejection_reasons == ("fixture_authority_or_catalog_changed",)
    assert generator.calls == judge.calls == 1 and args["relevance_assessor"].calls == 0


def test_scope_revocation_after_work_blocks_relevance_and_preview(setup):
    args, generator, _ = setup
    reader = args["authority_reader"]
    initial = reader.value
    original = generator.generate
    def revoke(**kwargs):
        response = original(**kwargs)
        reader.value = initial.model_copy(update={"scope_epoch":4})
        return response
    generator.generate = revoke
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False and args["relevance_assessor"].calls == 0


def test_changes_during_relevance_assessment_are_rechecked(setup):
    args, _, _ = setup
    reader = args["catalog_reader"]
    original = args["relevance_assessor"].assess
    def change(*, request):
        verdict = original(request=request)
        reader.value = reader.value.model_copy(update={"revision":11})
        return verdict
    args["relevance_assessor"].assess = change
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False
    assert result.rejection_reasons == ("fixture_authority_or_catalog_changed",)


def test_final_catalog_read_failure_withholds_even_after_candidate_acceptance(setup):
    args, generator, _ = setup
    reader = args["catalog_reader"]
    initial_read = reader.read
    def fail_later():
        if reader.calls:
            raise RuntimeError("private database detail")
        return initial_read()
    reader.read = fail_later
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert generator.calls == 1 and result.preview_allowed is False
    assert result.rejection_reasons == ("fixture_final_snapshot_unavailable",)
    assert "private database detail" not in result.report_json


def test_scope_success_does_not_replace_question_relevance(setup):
    args, _, _ = setup
    args["relevance_assessor"] = Relevance(answer=False)
    result = evaluate_scoped_fixture(**args)
    closed(result)
    assert result.preview_allowed is False
    assert result.rejection_reasons == ("fixture_question_not_answered",)
    assert result.to_component_report()["evidence_scope_guard"]["fixture_scope_checked"] is True


def test_stored_output_is_an_immutable_snapshot_not_caller_state(setup):
    args, _, _ = setup
    result = evaluate_scoped_fixture(**args)
    report = result.to_component_report()
    report["fixture_claim"]["statement"] = "Changed"
    args["sources"][0].text = "Changed source"
    assert result.to_component_report()["fixture_claim"]["statement"] != "Changed"
    assert result.to_component_report()["public_response"]["evidence"][0]["text"] != "Changed source"


def test_fixture_permissions_cannot_claim_authenticated_production_scope():
    with pytest.raises(ValueError):
        OperatorScopeFixture(operator_id="test", organization_id="org", collection="knowledge",
            allowed_modules=("*",), allowed_topics=("policy",), scope_epoch=0)
    with pytest.raises(ValueError):
        OperatorScopeFixture(operator_id="test", organization_id="org", collection="knowledge",
            allowed_modules=("engineering",), allowed_topics=("policy",), scope_epoch=0, authenticated=True)
    with pytest.raises(ValueError):
        CatalogSnapshotFixture(revision=0, documents=(), execution_source="actual_api")


def test_no_production_flags_can_be_set_in_result_constructor():
    for field in ("release_authorized", "production_enabled", "empirical_acceptance"):
        with pytest.raises(TypeError):
            ScopedFixturePresentation(report_json="{}", preview_allowed=False, rejection_reasons=(), **{field:True})
