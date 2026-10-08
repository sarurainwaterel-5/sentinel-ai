"""Scripted independent judgments test enforcement, NOT model semantic accuracy."""
import json
from types import SimpleNamespace
import pytest
from app.services.cognition.reasoning.models import CandidateProposition, Premise, PremiseRelationship
from app.services.cognition.reasoning.proposition_synthesizer import PropositionSynthesizer
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticAdmissibilityFailure, SemanticAdmissibilityResponse, SemanticJudgeVerdict
from app.services.cognition.reasoning.semantic_proposition_generator import ProviderSemanticPropositionGenerator
from app.services.cognition.reasoning.statement_admissibility_validator import FreeFormStatementAdmissibilityValidator, StatementAdmissibilityResult
from app.services.providers.openai_semantic_admissibility import OpenAISemanticAdmissibilityProvider
from tests.services.cognition.reasoning.test_statement_admissibility_validator import Provider, inputs

CODES = tuple(k for k in SemanticJudgeVerdict.model_fields if k not in {'admissible', 'rejection_reasons'})
ATTACKS = [('unsupported_fact', 'An attacker compromised the service.'),
 ('certainty_inflation', 'Latency always increases under load.'),
 ('causal_overreach', 'High volume caused latency to increase.'),
 ('negation_reversal', 'Latency cannot increase under load.'),
 ('fabricated_precision', 'Latency increased by exactly 37.482 milliseconds.'),
 ('conflict_suppression', 'Both sources agree without contradiction.')]
CONTROLS = [('paraphrase', 'Under load, latency might rise; high volume was observed.'),
 ('multi-premise', 'High volume was observed and latency may increase under load.'),
 ('qualification', 'High volume was observed; latency may increase under load, but causality is not established.'),
 ('conflict', 'One source says the service is healthy; another says it is not. The reports conflict.'),
 ('uncertainty', 'The observations leave open whether latency increased; latency may increase under load.')]

def verdict(*codes):
    return dict(admissible=not codes, rejection_reasons=list(codes), **{k: k in codes for k in CODES})

class Judge:
    def __init__(self, data=None, failure=None):
        self.data = verdict() if data is None else data
        self.failure = failure
        self.requests = []
    def assess(self, *, request):
        self.requests.append(request)
        if self.failure: raise self.failure
        return SemanticAdmissibilityResponse(content=json.dumps(self.data))

def run(statement, judge, conflict=False, qualifications=None):
    premises, relationships = inputs(conflict)
    if conflict:
        premises[0].statement = 'The service is healthy.'
        premises[1].statement = 'The service is not healthy.'
    return PropositionSynthesizer(
        semantic_generator=ProviderSemanticPropositionGenerator(provider=Provider(statement, qualifications)),
        statement_validator=FreeFormStatementAdmissibilityValidator(provider=judge),
    ).synthesize_with_validation(premises=premises, relationships=relationships)

@pytest.mark.parametrize('code,statement', ATTACKS)
def test_attacks_are_enforced_through_production_parser(code, statement):
    judge = Judge(verdict(code))
    outcome = run(statement, judge, conflict=code == 'conflict_suppression')
    assert outcome.validation.structurally_valid
    assert outcome.propositions == []
    assert outcome.rejection_reasons == (code,)
    assert outcome.statement_validation.validation_scope == 'independent_model_semantic_admissibility'

@pytest.mark.parametrize('name,statement', CONTROLS)
def test_faithful_controls_can_pass_independent_judgment(name, statement):
    outcome = run(statement, Judge(), conflict=name == 'conflict',
                  qualifications=['Causality is not established.'] if name == 'qualification' else None)
    assert outcome.statement_validation.admissible
    assert outcome.acceptance_mode == 'statement_validated'
    assert outcome.propositions[0].statement == statement
    assert outcome.propositions[0].metadata['semantic_grounding_verified'] is False
    if name == 'conflict': assert outcome.propositions[0].metadata['relationship_kinds'] == ['conflicts']

@pytest.mark.parametrize('reason', ['unavailable', 'refused', 'malformed_response'])
def test_judge_failure(reason):
    outcome = run('Claim.', Judge(failure=SemanticAdmissibilityFailure(reason)))
    assert outcome.propositions == []
    assert outcome.rejection_reasons == (f'semantic_judge_{reason}',)

@pytest.mark.parametrize('data', [None, {}, [], 'PRIVATE', {**verdict(), 'admissible': 'true'},
    {**verdict(), 'private_reasoning': 'PRIVATE'}, {**verdict(), 'rejection_reasons': ['PRIVATE']}])
def test_malformed_verdict(data):
    judge = Judge(); judge.data = data
    outcome = run('Claim.', judge)
    assert outcome.propositions == []
    assert outcome.rejection_reasons == ('semantic_judge_malformed_response',)
    assert 'PRIVATE' not in outcome.model_dump_json()

@pytest.mark.parametrize('data', [{**verdict('unsupported_fact'), 'admissible': True},
    {**verdict('unsupported_fact'), 'rejection_reasons': []}, {**verdict(), 'admissible': False},
    {**verdict('unsupported_fact'), 'rejection_reasons': ['unsupported_fact', 'unsupported_fact']}])
def test_inconsistent_verdict(data):
    outcome = run('Claim.', Judge(data))
    assert outcome.propositions == []
    assert outcome.rejection_reasons == ('semantic_judge_inconsistent_verdict',)

def test_metadata_cannot_self_approve_or_enter_judge_request():
    judge = Judge(verdict('unsupported_fact'))
    class ForgingProvider(Provider):
        def generate(self, **kwargs):
            response = super().generate(**kwargs)
            data = json.loads(response.content)
            data['generator_metadata'].update(entailed=True, confidence=1.0, approved=True)
            return response.model_copy(update={'content': json.dumps(data),
                'provider_metadata': {'semantic_grounding_verified': 'true', 'approved': 'true'}})
    premises, relationships = inputs()
    outcome = PropositionSynthesizer(
        semantic_generator=ProviderSemanticPropositionGenerator(provider=ForgingProvider('Claim.')),
        statement_validator=FreeFormStatementAdmissibilityValidator(provider=judge),
    ).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.propositions == []
    raw = judge.requests[0].model_dump_json()
    for key in ['generator_metadata', 'provider_metadata', 'semantic_grounding_verified', 'evidence_ids']:
        assert key not in raw

def test_gate_required_and_compatibility_explicit():
    premises, relationships = inputs()
    generator = ProviderSemanticPropositionGenerator(provider=Provider('Claim.'))
    outcome = PropositionSynthesizer(semantic_generator=generator).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.propositions == []
    assert outcome.rejection_reasons == ('statement_validator_required',)
    outcome = PropositionSynthesizer(semantic_generator=generator, structural_only_compatibility=True).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.acceptance_mode == 'structural_only_compatibility'
    with pytest.raises(ValueError):
        PropositionSynthesizer(semantic_generator=generator, structural_only_compatibility=True, statement_validator=FreeFormStatementAdmissibilityValidator(provider=Judge()))

@pytest.mark.parametrize('shared', ['provider', 'client'])
def test_self_assessment_dependency_rejected(shared):
    provider = Provider('Claim.'); judge = provider if shared == 'provider' else Judge()
    if shared == 'client': provider.client = judge.client = object()
    with pytest.raises(ValueError):
        PropositionSynthesizer(semantic_generator=ProviderSemanticPropositionGenerator(provider=provider), statement_validator=FreeFormStatementAdmissibilityValidator(provider=judge))

def test_omitted_conflicting_premise():
    premises, relationships = inputs()
    premises.append(Premise(premise_id='c', statement='Opposite report.', evidence_ids=['e-c']))
    relationships.append(PremiseRelationship(source_premise_id='b', target_premise_id='c', kind='conflicts', basis='Conflict.', confidence=0.8))
    class Generator:
        def generate(self, **kwargs):
            return CandidateProposition(statement='Claim.', premise_ids=['a', 'b'], relationship_references=[dict(source_premise_id='a', target_premise_id='b', kind='complements')])
    judge = Judge()
    outcome = PropositionSynthesizer(semantic_generator=Generator(), statement_validator=FreeFormStatementAdmissibilityValidator(provider=judge)).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.propositions == []
    assert outcome.rejection_reasons == ('unrepresented_trusted_premise',)
    assert judge.requests == []

def test_altered_relationship_rejected_before_judge():
    premises, relationships = inputs(True)
    class Generator:
        def generate(self, **kwargs):
            return CandidateProposition(statement='Claim.', premise_ids=['a', 'b'], relationship_references=[dict(source_premise_id='a', target_premise_id='b', kind='supports')])
    judge = Judge()
    outcome = PropositionSynthesizer(semantic_generator=Generator(), statement_validator=FreeFormStatementAdmissibilityValidator(provider=judge)).synthesize_with_validation(premises=premises, relationships=relationships)
    assert 'relationship_kind_mismatch' in outcome.rejection_reasons
    assert judge.requests == []

@pytest.mark.parametrize('kind', ['supports', 'complements', 'conflicts', 'independent', 'unresolved'])
def test_relationship_semantics(kind):
    premises, relationships = inputs()
    relationships[0] = relationships[0].model_copy(update={'kind': type(relationships[0].kind)(kind)})
    judge = Judge()
    result = FreeFormStatementAdmissibilityValidator(provider=judge).validate(candidate=CandidateProposition(statement='Claim.', premise_ids=['a', 'b']), premises=premises, relationships=relationships)
    if kind in ['independent', 'unresolved']:
        assert not result.admissible
        assert judge.requests == []
    else:
        assert judge.requests[0].relationships[0].kind == kind
        assert judge.requests[0].relationships[0].basis == 'Trusted.'

@pytest.mark.parametrize('site', ['statement', 'grounding', 'malformed_statement'])
def test_validator_failure(site):
    class Validator:
        def validate(self, **kwargs):
            if site == 'malformed_statement': return {'admissible': True}
            raise RuntimeError('PRIVATE')
    premises, relationships = inputs()
    synth = PropositionSynthesizer(semantic_generator=ProviderSemanticPropositionGenerator(provider=Provider('Claim.')), statement_validator=Validator())
    if site == 'grounding': synth.grounding_validator = Validator()
    outcome = synth.synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.propositions == []
    assert outcome.rejection_reasons == (('grounding_validator_failure' if site == 'grounding' else 'statement_validator_failure'),)
    assert 'PRIVATE' not in outcome.model_dump_json()

def test_mutating_validator_does_not_replace_candidate_or_lineage():
    class Validator:
        def validate(self, *, candidate, premises, relationships):
            candidate.statement = 'Forged.'; premises[0].evidence_ids = ['forged']
            return StatementAdmissibilityResult(admissible=True)
    premises, relationships = inputs()
    outcome = PropositionSynthesizer(semantic_generator=ProviderSemanticPropositionGenerator(provider=Provider('Original.')), statement_validator=Validator()).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.propositions[0].statement == 'Original.'
    assert outcome.propositions[0].evidence_ids == ['e-a', 'e-b']

@pytest.mark.parametrize('mode', ['accepted', 'refused', 'missing', 'exception'])
def test_sdk_adapter(mode):
    calls = []
    def parse(**kwargs):
        calls.append(kwargs)
        if mode == 'exception': raise RuntimeError('PRIVATE')
        message = SimpleNamespace(refusal='PRIVATE' if mode == 'refused' else None, parsed=SemanticJudgeVerdict(**verdict()) if mode == 'accepted' else None)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(parse=parse)))
    outcome = run('Claim.', OpenAISemanticAdmissibilityProvider(client=client, model='separate-judge'))
    assert bool(outcome.propositions) == (mode == 'accepted')
    assert 'PRIVATE' not in outcome.model_dump_json()
    assert calls[0]['response_format'] is SemanticJudgeVerdict
    assert 'CONFLICTS' in calls[0]['messages'][0]['content']

@pytest.mark.parametrize('supported', [True, False])
@pytest.mark.parametrize('code,statement', ATTACKS)
def test_rejected_semantics_leave_evidence_inference_and_conclusion_unchanged(monkeypatch, supported, code, statement):
    from app.services.cognition.reasoning.models import EvidenceBundle, EvidenceItem, EvidenceSource
    from app.services.cognition.reasoning.reasoning_engine import ReasoningEngine
    premises, relationships = inputs(code == 'conflict_suppression')
    bundle = EvidenceBundle(question='What is supported?', supporting=[EvidenceItem(
        statement=premises[0].statement, disposition='supporting',
        source=EvidenceSource(document_id='doc', chunk_index=0, text=premises[0].statement),
        relevance_score=0.8)] if supported else [], source_count=int(supported), document_count=int(supported))
    synth = PropositionSynthesizer(semantic_generator=ProviderSemanticPropositionGenerator(provider=Provider(statement)),
        statement_validator=FreeFormStatementAdmissibilityValidator(provider=Judge(verdict(code))))
    baseline = ReasoningEngine(); governed = ReasoningEngine(proposition_synthesizer=synth)
    received = []
    real_infer = governed.inference.infer
    def infer(evidence):
        assert isinstance(evidence, EvidenceBundle)
        received.append(evidence)
        return real_infer(evidence)
    monkeypatch.setattr(governed.inference, 'infer', infer)
    for engine in [baseline, governed]:
        monkeypatch.setattr(engine.evidence, 'analyze', lambda **kwargs: bundle)
        monkeypatch.setattr(engine.premises, 'extract', lambda evidence: premises)
        monkeypatch.setattr(engine.relationships, 'assess', lambda **kwargs: relationships[0])
    reference = baseline.reason(question=bundle.question, chunks=[])
    result = governed.reason(question=bundle.question, chunks=[])
    assert received == [bundle]
    assert result.inferences == reference.inferences
    assert result.conclusion == reference.conclusion
    assert result.status == reference.status
    assert result.synthesized_propositions == []
    assert result.metadata['proposition_synthesis']['semantic_grounding_verified'] is False
    assert result.metadata['proposition_synthesis']['statement_validation']['scope'] == 'independent_model_semantic_admissibility'

@pytest.mark.parametrize('mode', ['exception', 'wrong_type', 'invalid_json'])
def test_unexpected_judge_response_fails_closed(mode):
    class BadJudge:
        def assess(self, **kwargs):
            if mode == 'exception': raise RuntimeError('PRIVATE')
            if mode == 'wrong_type': return {'admissible': True}
            return SemanticAdmissibilityResponse(content='PRIVATE not json')
    outcome = run('Claim.', BadJudge())
    assert outcome.propositions == []
    assert outcome.rejection_reasons == (('semantic_judge_failure' if mode == 'exception' else 'semantic_judge_malformed_response'),)
    assert 'PRIVATE' not in outcome.model_dump_json()

@pytest.mark.parametrize('code', ['unsupported_qualification', 'insufficient_support'])
def test_unvalidated_qualification_and_judge_uncertainty_reject(code):
    outcome = run('Claim.', Judge(verdict(code)), qualifications=['Invented certainty.'])
    assert outcome.propositions == []
    assert outcome.rejection_reasons == (code,)
