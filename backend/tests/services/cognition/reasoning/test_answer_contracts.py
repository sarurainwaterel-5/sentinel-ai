"""Offline contract/provenance enforcement, not empirical semantic evidence."""
import pytest
from pydantic import ValidationError
from app.schemas.cognition.answer import GovernedAnswerRequest
from app.services.cognition.reasoning.answer_models import AnswerClaim, ClaimValidation, GovernedAnswer
from app.services.cognition.reasoning.answer_provenance import build_registry
from app.services.cognition.reasoning.models import EvidenceSource


def source(**changes):
    return EvidenceSource(document_id="d1", organization_id="org", collection="knowledge",
        chunk_index=0, text="May require human approval.\nDo not execute.", status="indexed",
        file_hash="hash", module="engineering", topic="policy").model_copy(update=changes)


def registry(sources, **changes):
    args = dict(sources=sources, snapshot_id="snapshot", organization_id="org", collection="knowledge",
        catalog={"d1":dict(organization_id="org",collection="knowledge",status="indexed",file_hash="hash",module="engineering",topic="policy")})
    return build_registry(**(args | changes))


def test_exact_source_and_excerpts_are_preserved_without_mutation():
    item = source(metadata={"evidence_id":"forged", "semantic_grounding_verified":True})
    result = registry([item])
    assert not result.rejection_reasons
    evidence = result.evidence[0]
    assert evidence.evidence_id != "forged"
    assert evidence.text == item.text
    assert result.excerpt(evidence.evidence_id, 0, 3) == "May"
    with pytest.raises(ValidationError):
        evidence.text = "Changed"
    with pytest.raises(ValidationError):
        type(evidence).model_validate(evidence.model_dump() | {"text_sha256":"0"*64})
    assert item.metadata["evidence_id"] == "forged"


@pytest.mark.parametrize("changes,reason", [
    ({"document_id":None}, "incomplete_locator"),
    ({"chunk_index":None}, "incomplete_locator"),
    ({"text":" "}, "incomplete_locator"),
    ({"organization_id":"other"}, "source_scope_mismatch"),
    ({"collection":"other"}, "source_scope_mismatch"),
    ({"file_hash":"changed"}, "file_hash_mismatch"),
    ({"status":"archived"}, "source_not_indexed"),
    ({"module":"trading"}, "catalog_metadata_mismatch"),
])
def test_bad_provenance_never_supports_a_claim(changes, reason):
    result = registry([source(**changes)])
    assert result.evidence == ()
    assert result.rejection_reasons == (reason,)


def test_duplicate_identity_deduplicates_but_conflicting_content_abstains():
    assert len(registry([source(),source()]).evidence) == 1
    result = registry([source(),source(text="No approval required.")])
    assert not result.evidence
    assert result.rejection_reasons == ("ambiguous_source_identity",)


@pytest.mark.parametrize("start,end", [(-1,2),(0,999),(2,1),(0,0),(True,2)])
def test_invalid_excerpt_bounds_reject(start,end):
    result=registry([source()])
    with pytest.raises(ValueError):
        result.excerpt(result.evidence[0].evidence_id,start,end)


def test_request_reuses_bounds_and_rejects_release_overrides():
    assert GovernedAnswerRequest(question=" test ").question == "test"
    for changes in ({"limit":26},{"question":" "},{"enable":True},{"limit":"5"}):
        with pytest.raises(ValidationError):
            GovernedAnswerRequest.model_validate({"question":"test"}|changes)


@pytest.mark.parametrize("value", [True,0,"false"])
def test_grounding_marker_cannot_be_certified_or_coerced(value):
    with pytest.raises(ValidationError):
        ClaimValidation(semantic_grounding_verified=value)


def test_synthesis_requires_distinct_premises_and_valid_lineage():
    args=dict(claim_id="c",statement="Two source reports disagree.",kind="attributed_synthesis",premise_ids=("p1","p2"),evidence_ids=("e",))
    AnswerClaim(**args)
    for changes in ({"premise_ids":("p1",)},{"premise_ids":("p1","p1")},{"evidence_ids":(" ",)},{"statement":" "}):
        with pytest.raises(ValidationError):
            AnswerClaim(**(args|changes))


def test_positive_statement_status_requires_explicit_gates():
    with pytest.raises(ValidationError):
        ClaimValidation(statement_status="admissible",structural_status="passed")


def test_disabled_envelope_cannot_publish_answer_or_claims():
    GovernedAnswer(question="Question",snapshot_id="snapshot",evidence=registry([source()]).evidence)
    claim=AnswerClaim(claim_id="c",statement="Quoted report",kind="source_report",premise_ids=("p",),evidence_ids=("e",))
    for changes in ({"answer_text":"Answer"},{"outcome":"answered"},{"claims":(claim,)},{"snapshot_id":"other","evidence":registry([source()]).evidence}):
        with pytest.raises(ValidationError):
            GovernedAnswer(**(dict(question="Question",snapshot_id="snapshot")|changes))


def test_registry_order_and_identity_ignore_similarity_and_metadata():
    a=source(chunk_index=1)
    b=source(chunk_index=2)
    assert registry([a,b]) == registry([b,a])
    original=registry([a]).evidence[0]
    assert registry([source(chunk_index=1,score=0.99,metadata={"evidence_id":"fake"})]).evidence[0] == original


def test_catalog_required_and_scope_never_widens():
    assert registry([source()],catalog={}).rejection_reasons == ("catalog_scope_mismatch",)
    assert registry([source()],topic="missing").rejection_reasons == ("retrieval_scope_mismatch",)
    with pytest.raises(ValueError):
        registry([source()],snapshot_id=" ")
    with pytest.raises(ValueError):
        registry([source()]*26)


def test_scope_envelope_cannot_expose_other_organization():
    from app.services.cognition.reasoning.answer_models import AnswerScope
    with pytest.raises(ValidationError):
        GovernedAnswer(question="Q",snapshot_id="snapshot",scope=AnswerScope(organization_id="other"), evidence=registry([source()]).evidence)


def test_admissibility_is_bound_to_exact_displayed_text():
    from app.services.cognition.reasoning.statement_admissibility_validator import StatementAdmissibilityResult
    verdict=ClaimValidation(structural_status="passed",statement_status="admissible",
        statement_result=StatementAdmissibilityResult(admissible=True,validation_scope="independent_model_semantic_admissibility"),
        candidate_sha256="0"*64,inputs_sha256="1"*64,policy_version="existing")
    with pytest.raises(ValidationError):
        AnswerClaim(claim_id="c",statement="Changed after validation",kind="attributed_synthesis",
            premise_ids=("p1","p2"),evidence_ids=("e",),validation=verdict)
