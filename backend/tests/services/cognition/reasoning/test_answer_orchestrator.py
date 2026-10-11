"""Scripted fixture enforcement only; no judge accuracy or live API evidence."""
import json
import pytest
from app.services.cognition.reasoning.answer_models import AnswerScope
from app.services.cognition.reasoning.answer_orchestrator import OfflineAnswerCoordinator
from app.services.cognition.reasoning.answer_provenance import build_registry
from app.services.cognition.reasoning.answer_renderer import render_fixture
from app.services.cognition.reasoning.models import (
    CandidateProposition, CandidateRelationshipReference, EvidenceSource, EvidenceBundle,
    EvidenceItem, EvidenceDisposition, PremiseRelationship, PremiseRelationshipKind,
)
from app.services.cognition.reasoning.premise_extractor import PremiseExtractor
from app.services.cognition.reasoning.semantic_proposition_generator import ProviderSemanticPropositionGenerator
from app.services.cognition.reasoning.semantic_generation_provider import SemanticGenerationResponse, SemanticGenerationFailure
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticAdmissibilityResponse, SemanticAdmissibilityFailure
from app.services.cognition.reasoning.statement_admissibility_validator import FreeFormStatementAdmissibilityValidator, VerbatimPremiseStatementValidator


class GenerationFixture:
    def __init__(self):
        self.calls=0
        self.failure=None
        self.malformed=False
        self.omit=False
        self.untrusted_candidate=None
    def generate(self, *, premises, relationships):
        self.calls+=1
        if self.failure:
            raise SemanticGenerationFailure(self.failure)
        if self.malformed:
            return SemanticGenerationResponse(content="not json")
        candidate=CandidateProposition(statement="The supplied reports disagree about approval.",
            premise_ids=[p.premise_id for p in premises],
            relationship_references=[CandidateRelationshipReference(source_premise_id=r.source_premise_id,
                target_premise_id=r.target_premise_id,kind=r.kind) for r in relationships],
            qualifications=["Source truth is not determined."], generator_metadata={"semantic_grounding_verified":True})
        if self.omit:
            candidate.premise_ids=candidate.premise_ids[:2]
            candidate.relationship_references=candidate.relationship_references[:1]
        self.untrusted_candidate=candidate
        return SemanticGenerationResponse(content=candidate.model_dump_json())


class JudgeFixture:
    def __init__(self):
        self.calls=0
        self.requests=[]
        self.failure=None
        self.defect=None
        self.malformed=False
        self.inconsistent=False
    def assess(self, *, request):
        self.calls+=1
        self.requests.append(request.model_copy(deep=True))
        if self.failure:
            raise SemanticAdmissibilityFailure(self.failure)
        if self.malformed:
            return SemanticAdmissibilityResponse(content="{}")
        codes=("unsupported_fact","certainty_inflation","causal_overreach","negation_reversal",
            "fabricated_precision","conflict_suppression","unsupported_qualification","insufficient_support")
        verdict={c:c==self.defect for c in codes}
        verdict.update(admissible=not self.defect,rejection_reasons=[self.defect] if self.defect else [])
        if self.inconsistent:
            verdict["admissible"]=True
            verdict["unsupported_fact"]=True
        return SemanticAdmissibilityResponse(content=json.dumps(verdict))


def fixture(count=2):
    sources=[EvidenceSource(document_id="doc",organization_id="org",collection="knowledge",chunk_index=i,
        module="engineering",topic="policy",status="indexed",file_hash="hash",
        text=f"Report {i} says approval {'is required' if i == 0 else 'is not required'}.") for i in range(count)]
    catalog={"doc":dict(organization_id="org",collection="knowledge",module="engineering",topic="policy",status="indexed",file_hash="hash")}
    registry=build_registry(sources=sources,catalog=catalog,snapshot_id="snapshot",organization_id="org",collection="knowledge")
    items=[EvidenceItem(statement=e.text,disposition=EvidenceDisposition.CONTEXTUAL,
        source=EvidenceSource(**e.model_dump(exclude={"evidence_id","snapshot_id","text_sha256"}),metadata={"evidence_id":e.evidence_id})) for e in registry.evidence]
    premises=PremiseExtractor().extract(EvidenceBundle(question="Question",contextual=items))
    relationships=[PremiseRelationship(source_premise_id=p.premise_id,target_premise_id=q.premise_id,
        kind=PremiseRelationshipKind.CONFLICTS,basis="The fixture reports disagree.",confidence=0.8)
        for i,p in enumerate(premises) for q in premises[i+1:]]
    return dict(question="What do the reports say?",sources=sources,catalog=catalog,
        scope=AnswerScope(organization_id="org",module="engineering",topic="policy"),
        collection="knowledge",snapshot_id="snapshot",relationships=relationships)


def coordinator():
    generator=GenerationFixture()
    judge=JudgeFixture()
    engine=OfflineAnswerCoordinator(generator=ProviderSemanticPropositionGenerator(provider=generator),
        statement_validator=FreeFormStatementAdmissibilityValidator(provider=judge))
    return engine,generator,judge


def test_complete_fixture_passes_both_gates_but_public_release_remains_disabled():
    engine,generator,judge=coordinator()
    result=engine.evaluate_fixture(**fixture())
    assert generator.calls==judge.calls==1
    assert result.fixture_claim.validation.statement_status=="admissible"
    assert result.fixture_claim.validation.semantic_grounding_verified is False
    assert result.public_response.outcome=="disabled"
    assert result.public_response.answer_text is None and not result.public_response.claims
    assert result.public_response.conflicts == ("The fixture reports disagree.",)
    assert result.public_response.validation.citation_status == "passed"
    assert result.fixture_claim.statement in result.fixture_text
    assert "[1] [2]" in result.fixture_text
    assert result.execution_source == "unit_test" and not result.empirical_acceptance
    assert "generator_metadata" not in judge.requests[0].model_dump_json()


@pytest.mark.parametrize("defect", ["unsupported_fact","certainty_inflation","causal_overreach","negation_reversal",
    "fabricated_precision","conflict_suppression","unsupported_qualification","insufficient_support"])
def test_semantic_defects_withhold_entire_fixture(defect):
    engine,generator,judge=coordinator()
    judge.defect=defect
    result=engine.evaluate_fixture(**fixture())
    assert result.public_response.outcome=="rejected"
    assert result.public_response.validation.rejection_reasons==(defect,)
    assert result.fixture_text is None and result.fixture_claim is None
    assert result.public_response.conflicts


@pytest.mark.parametrize("failure", ["unavailable","refused","malformed_response"])
def test_provider_failures_have_no_fallback(failure):
    engine,generator,judge=coordinator()
    generator.failure=failure
    result=engine.evaluate_fixture(**fixture())
    assert result.public_response.outcome=="provider_failure" and judge.calls==0
    assert result.fixture_text is None
    generator.failure=None
    judge.failure=failure
    result=engine.evaluate_fixture(**fixture())
    assert result.public_response.outcome=="blocked_validation"
    assert result.fixture_text is None


@pytest.mark.parametrize("mode", ["malformed","inconsistent"])
def test_malformed_or_inconsistent_judge_never_approves(mode):
    engine,_,judge=coordinator()
    setattr(judge,mode,True)
    result=engine.evaluate_fixture(**fixture())
    assert result.public_response.outcome=="blocked_validation"
    assert result.fixture_claim is None


def test_partial_registry_never_silently_omits_bad_evidence():
    engine,generator,judge=coordinator()
    data=fixture()
    data["sources"].append(data["sources"][0].model_copy(update={"chunk_index":2,"status":"archived"}))
    result=engine.evaluate_fixture(**data)
    assert result.public_response.outcome=="blocked_provenance"
    assert result.public_response.validation.rejection_reasons == ("source_not_indexed",)
    assert generator.calls==judge.calls==0


@pytest.mark.parametrize("mode", ["missing","unresolved","low","foreign"])
def test_incomplete_relationship_coverage_blocks_generation(mode):
    engine,generator,judge=coordinator()
    data=fixture()
    if mode=="missing":data["relationships"]=[]
    elif mode=="unresolved":data["relationships"][0].kind=PremiseRelationshipKind.UNRESOLVED
    elif mode=="low":data["relationships"][0].confidence=0.74
    else:data["relationships"][0].source_premise_id="unknown"
    result=engine.evaluate_fixture(**data)
    assert result.public_response.outcome=="blocked_relationships"
    assert generator.calls==judge.calls==0


def test_missing_evidence_and_single_premise_make_no_provider_calls():
    engine,generator,judge=coordinator()
    data=fixture();data["sources"]=[]
    assert engine.evaluate_fixture(**data).public_response.outcome=="insufficient_evidence"
    assert engine.evaluate_fixture(**fixture(1)).public_response.outcome=="blocked_relationships"
    assert generator.calls==judge.calls==0


def test_omitted_conflicting_premise_is_not_partial_success():
    engine,generator,judge=coordinator()
    generator.omit=True
    result=engine.evaluate_fixture(**fixture(3))
    assert result.public_response.outcome=="rejected" and judge.calls==0
    assert not result.fixture_claim
    assert len(result.public_response.conflicts)==3


def test_renderer_rechecks_mutated_validation_and_complete_citations():
    engine,_,_=coordinator()
    result=engine.evaluate_fixture(**fixture())
    public=result.public_response
    inputs={"question":public.question,"scope":public.scope.model_dump(),
        "evidence":[e.model_dump() for e in public.evidence],
        "premises":[p.model_dump() for p in public.premises],
        "relationships":[r.model_dump(mode="json") for r in public.relationships]}
    assert render_fixture(result.fixture_claim,public.evidence,inputs=inputs)==result.fixture_text
    with pytest.raises(ValueError):
        render_fixture(result.fixture_claim,result.public_response.evidence[:1],inputs=inputs)
    changed=result.fixture_claim.model_copy(update={"statement":"Invented after assessment"})
    with pytest.raises(ValueError):
        render_fixture(changed,result.public_response.evidence,inputs=inputs)


def test_composition_refuses_compatibility_and_self_assessment():
    with pytest.raises(ValueError):
        OfflineAnswerCoordinator(generator=GenerationFixture(),statement_validator=VerbatimPremiseStatementValidator())
    shared=GenerationFixture()
    with pytest.raises(ValueError):
        OfflineAnswerCoordinator(generator=ProviderSemanticPropositionGenerator(provider=shared),
            statement_validator=FreeFormStatementAdmissibilityValidator(provider=shared))


def test_invalid_request_rejects_before_injected_work():
    engine,generator,judge=coordinator()
    data=fixture();data["question"]=" "
    with pytest.raises(ValueError):
        engine.evaluate_fixture(**data)
    assert generator.calls==judge.calls==0


def test_malformed_generation_and_independent_relationship_abstain():
    engine,generator,judge=coordinator()
    generator.malformed=True
    result=engine.evaluate_fixture(**fixture())
    assert result.public_response.outcome=="provider_failure" and judge.calls==0
    data=fixture();data["relationships"][0].kind=PremiseRelationshipKind.INDEPENDENT
    assert engine.evaluate_fixture(**data).public_response.outcome=="blocked_relationships"


def test_no_inference_or_legacy_communication_dependency():
    # Guard the actual import boundary, rather than merely expecting a mock call count.
    import ast
    from pathlib import Path
    import app.services.cognition.reasoning.answer_orchestrator as module
    tree=ast.parse(Path(module.__file__).read_text())
    imports=[node.module or "" for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
    assert not any(any(name in value for name in ("inference_engine","llm_formatter","reasoning_service","llm_service","providers")) for value in imports)
    engine,generator,judge=coordinator()
    data=fixture(); before=[s.model_dump() for s in data["sources"]]
    result=engine.evaluate_fixture(**data)
    assert [s.model_dump() for s in data["sources"]]==before
    assert result.public_response.validation.release_status=="disabled"


def test_untrusted_fixture_metadata_cannot_create_empirical_acceptance():
    from app.services.cognition.reasoning.answer_orchestrator import OfflineAnswerEvaluation
    engine,_,_=coordinator()
    result=engine.evaluate_fixture(**fixture())
    with pytest.raises(TypeError):
        OfflineAnswerEvaluation(public_response=result.public_response,empirical_acceptance=True)


def test_ambiguous_source_and_relationship_budget_are_not_truncated():
    engine,generator,judge=coordinator()
    data=fixture()
    data["sources"].append(data["sources"][0].model_copy(update={"text":"Conflicting copy"}))
    assert engine.evaluate_fixture(**data).public_response.validation.rejection_reasons == ("ambiguous_source_identity",)
    data=fixture();data["relationships"]*=301
    assert engine.evaluate_fixture(**data).public_response.validation.rejection_reasons == ("relationship_budget_exceeded",)
    assert generator.calls==judge.calls==0
