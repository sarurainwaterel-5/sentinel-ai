"""Real SDK HTTP mocks; no paid calls or semantic evidence."""
import asyncio
import copy
import hashlib
import json
import httpx
from openai import AsyncOpenAI
import pytest
from app.services.providers.openai_governed_transport import OpenAIGovernedTransport, RoleConfiguration
from evaluation.governed_answers.live_provider_rehearsal import canonical, load_inputs
from evaluation.governed_answers.runtime_inspection_rehearsal import inspect_runtime

async def exercise(mutation=None, failure=None, timeout=2, cancel=False, invoke=None, binding_override=None, catalog_context=False):
    cases, labels, _ = load_inputs()
    case = copy.deepcopy(next(c for c in cases if labels[c['case_id']]['statement_admissible'] and labels[c['case_id']]['answers_question']))
    if catalog_context:
        for index, source in enumerate(case['sources']):
            source['document_id'] = 'document'
            source['chunk_index'] = 256 if catalog_context == 'large' and index == 1 else index
    if failure == 'fabricated_premise':
        case['premises'][0]['statement'] = 'Fabricated unsupported premise for boundary regression.'
    if failure == 'empty_sources':
        case['sources'] = []
        for premise in case['premises']:
            premise['evidence_ids'] = []
    if failure == 'unsupported_premise':
        case['premises'][0]['evidence_ids'] = []
    context = {k:case[k] for k in ('question','sources','premises','relationships')}
    binding = dict(question=case['question'],context_sha256=hashlib.sha256(canonical(context).encode()).hexdigest(),principal_id='synthetic',permission_epoch=1,credential_epoch=1,catalog_epoch=1,gate_sha256='a'*64,eligible=True,scope=dict(organization_id='synthetic',collection='review',module='synthetic',topic='review'))
    if binding_override:
        binding.update(binding_override)
    if mutation and mutation[0] == 'initial':
        binding[mutation[1]] = mutation[2]
    calls, clients = [], []
    entered, cancelled = asyncio.Event(), asyncio.Event()
    async def handler(request):
        payload = json.loads(request.content)
        role = ['generation','statement','relevance'][len(calls)]
        calls.append((request,payload))
        if mutation and mutation[0] == role:
            binding[mutation[1]] = mutation[2]
        if cancel or failure == 'delay':
            entered.set()
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                cancelled.set()
                raise
        if failure == 'configuration_changed':
            object.__setattr__(transport._roles[role], 'model', 'mutated-model')
        if failure == role:
            return httpx.Response(500,json={'error':{'message':'mock failure'}})
        if role == 'generation':
            value = {k:case['candidate'][k] for k in ('statement','premise_ids','relationship_references','qualifications')}
        elif role == 'statement':
            value = dict(admissible=True,rejection_reasons=[],**{k:False for k in ('unsupported_fact','certainty_inflation','causal_overreach','negation_reversal','fabricated_precision','conflict_suppression','unsupported_qualification','insufficient_support')})
        else:
            wire = json.loads(payload['input'][1]['content'])
            value = dict(request_sha256=wire['request_sha256'],answers_question=True,uncertain=False,reason='Mock label only')
        if failure == 'relevance_rejected' and role == 'relevance':
            value.update(answers_question=False)
        if failure == 'digest_mismatch' and role == 'relevance':
            value.update(request_sha256='0'*64)
        if failure == 'structure' and role == 'generation':
            value['premise_ids'] = ['unknown-1','unknown-2']
        if failure == 'malformed':
            value = {}
        if failure == 'rejected' and role == 'statement':
            value.update(admissible=False,unsupported_fact=True,rejection_reasons=['unsupported_fact'])
        return httpx.Response(200,json={'id':'resp_mock','object':'response','created_at':0,'status':'completed','model':payload['model'],'error':None,'incomplete_details':None,'output':[{'id':'msg_mock','type':'message','role':'assistant','status':'completed','content':[{'type':'output_text','text':json.dumps(value),'annotations':[]}]}]})
    roles = ('generation','statement','relevance')
    for role in roles:
        clients.append(AsyncOpenAI(api_key='synthetic-unused',base_url='https://mock.invalid/v1',max_retries=0,http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))))
    transport = OpenAIGovernedTransport(**{r:RoleConfiguration(client=c,model='mock-'+r) for r,c in zip(roles,clients)})
    async def retrieve():
        if mutation and mutation[0] == 'retrieve':
            binding[mutation[1]] = mutation[2]
        return case
    try:
        task = asyncio.create_task((invoke or inspect_runtime)(transport=transport,retrieve=retrieve,current_binding=lambda:binding,timeout_seconds=timeout))
        if cancel:
            await entered.wait()
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert cancelled.is_set()
            return None,calls
        result = (await task).to_dict()
        if failure == 'delay':
            assert cancelled.is_set()
        return result,calls
    finally:
        await asyncio.gather(*(c.close() for c in clients))

def test_sdk_wire_composition_is_inspection_only():
    result,calls = asyncio.run(exercise())
    assert result['status'] == 'inspection_only' and result['attempted_calls'] == 3
    assert result['transport_execution_source'] == 'openai_responses_transport'
    assert not result['production_enabled'] and not result['release_authorized']
    assert not result['publication_barrier_implemented']
    assert result['statement_assessment']['admissible'] is True
    assert result['relevance_assessment']['answers_question'] is True
    assert result['relevance_assessment']['request_sha256'] == result['request_sha256']['relevance']
    for role, (request,payload) in zip(('generation','statement','relevance'), calls):
        config = result['configuration']['roles'][role]
        assert config == dict(model='mock-'+role,reasoning_effort=None,sdk_retries=0)
        wire = json.loads(payload['input'][1]['content'])
        expected = wire['request_sha256'] if role == 'relevance' else hashlib.sha256(canonical(wire).encode()).hexdigest()
        assert result['request_sha256'][role] == expected
        assert request.url.path == '/v1/responses'
        assert payload['store'] is False and payload['truncation'] == 'disabled'
        assert payload['text']['format']['type'] == 'json_schema'

@pytest.mark.parametrize('stage',['retrieve','generation','statement','relevance'])
@pytest.mark.parametrize('field,value',[('permission_epoch',2),('catalog_epoch',2),('eligible',False),('question','Changed question'),('context_sha256','b'*64),('gate_sha256','b'*64),('scope',dict(organization_id='other',collection='review',module='synthetic',topic='review'))])
def test_binding_changes_discard_all_partial_output(stage,field,value):
    result,calls = asyncio.run(exercise(mutation=(stage,field,value)))
    assert result['status'] == 'withheld'
    assert not {'candidate','context','binding'} & result.keys()
    assert len(calls) == ['retrieve','generation','statement','relevance'].index(stage)

@pytest.mark.parametrize('failure,count',[('generation',1),('statement',2),('relevance',3),('malformed',1),('rejected',2),('relevance_rejected',3),('digest_mismatch',3),('structure',1),('configuration_changed',1),('empty_sources',0),('unsupported_premise',0)])
def test_failure_no_retry_or_partial_answer(failure,count):
    result,calls = asyncio.run(exercise(failure=failure))
    assert result['status'] == 'withheld' and 'candidate' not in result
    assert len(calls) == count

def test_outer_deadline_cancels_sdk():
    result,calls = asyncio.run(exercise(failure='delay',timeout=.02))
    assert result['reason'] == 'timeout' and len(calls) == 1

def test_request_cancellation_propagates():
    _,calls = asyncio.run(exercise(cancel=True))
    assert len(calls) == 1

@pytest.mark.parametrize('field,value',[('eligible',False),('permission_epoch',True),('gate_sha256','missing'),('scope',{})])
def test_invalid_initial_gate_denies_before_sdk(field,value):
    result,calls = asyncio.run(exercise(mutation=('initial',field,value)))
    assert result['status'] == 'withheld' and calls == []
