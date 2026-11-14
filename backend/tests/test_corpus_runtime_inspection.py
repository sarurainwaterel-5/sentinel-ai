"""Actual source composition rejects invented premises and unsafe review rendering."""
import hashlib
import pytest
from evaluation.governed_answers.corpus_runtime_inspection import extractive_case, render_checked_inspection
from evaluation.governed_answers.live_provider_rehearsal import canonical
from evaluation.governed_answers.runtime_inspection_rehearsal import InspectionResult
from evaluation.governed_answers.transactional_inspection_publication import PublicationDenied


def inputs():
    texts = ['Source <script>alert(1)</script>', 'Second exact source.']
    verified = dict(document=dict(document_id='actual-document'), chunks=[
        dict(index=i, text=text, sha256=hashlib.sha256(text.encode()).hexdigest(), byte_length=len(text.encode()))
        for i, text in enumerate(texts)])
    relationships = [dict(source_premise_id='premise-0', target_premise_id='premise-1',
                          kind='complements', basis='Explicit operator hypothesis, not a source fact.')]
    return verified, relationships


def test_exact_sources_become_exact_premises():
    verified, relationships = inputs()
    case = extractive_case(question='What do the sources state?', verified=verified, relationships=relationships)
    assert [p['statement'] for p in case['premises']] == [c['text'] for c in verified['chunks']]
    assert case['sources'][0]['document_id'] == 'actual-document'
    assert case['premises'][0]['evidence_ids'] == ['evidence-0']
    assert case['relationships'] == relationships
    relationships[0]['basis'] = 'changed'
    assert case['relationships'][0]['basis'] != 'changed'


@pytest.mark.parametrize('mutation', ['hash', 'length', 'duplicate', 'single', 'empty', 'unsupported', 'self', 'uncovered', 'budget'])
def test_invalid_source_or_relationship_denied(mutation):
    verified, relationships = inputs()
    if mutation == 'hash': verified['chunks'][0]['sha256'] = '0' * 64
    if mutation == 'length': verified['chunks'][0]['byte_length'] += 1
    if mutation == 'duplicate': verified['chunks'][1]['index'] = 0
    if mutation == 'single': verified['chunks'].pop()
    if mutation == 'empty': relationships.clear()
    if mutation == 'unsupported': relationships[0]['target_premise_id'] = 'invented'
    if mutation == 'self': relationships[0]['target_premise_id'] = 'premise-0'
    if mutation == 'uncovered': verified['chunks'].append(dict(index=2, text='third', byte_length=5, sha256=hashlib.sha256(b'third').hexdigest()))
    if mutation == 'budget': relationships[0]['basis'] = 'x' * 2049
    with pytest.raises(ValueError):
        extractive_case(question='What?', verified=verified, relationships=relationships)


def report():
    verified, relationships = inputs()
    return dict(status='inspection_only', preview_allowed=True, production_enabled=False,
        release_authorized=False, proposition_to_inference='closed', inspection_publication_barrier_implemented=True,
        context=extractive_case(question='<img src=x>', verified=verified, relationships=relationships),
        candidate=dict(statement='<script>candidate</script>', qualifications=['<unsafe>']),
        inspection_publication_binding=dict(document_id='actual-document'), configuration={},
        statement_assessment=dict(admissible=True), relevance_assessment=dict(answers_question=True))


def test_review_escapes_all_source_and_candidate_html():
    document = render_checked_inspection(InspectionResult(canonical(report())))
    assert '<script>' not in document and '<img src=x>' not in document
    assert '&lt;script&gt;candidate&lt;/script&gt;' in document
    assert 'Production disabled' in document and 'operator-supplied hypotheses' in document
    assert 'Actual corpus runtime inspection' in document


@pytest.mark.parametrize('key,value', [('production_enabled', True), ('release_authorized', True),
    ('inspection_publication_barrier_implemented', False), ('preview_allowed', False),
    ('status', 'withheld'), ('proposition_to_inference', 'open')])
def test_unpublished_or_released_candidate_cannot_render(key, value):
    value_report = report(); value_report[key] = value
    with pytest.raises(PublicationDenied):
        render_checked_inspection(InspectionResult(canonical(value_report)))

# Opt-in integration uses disposable PostgreSQL; provider responses are HTTP mocks.
from test_transactional_inspection_publication import setup_catalog


@pytest.mark.parametrize('mode', ['success', 'revoke', 'reject'])
def test_corpus_sql_sdk_publication_and_revocation(setup_catalog, mode):
    revoke = mode == 'revoke'
    import asyncio
    import json
    import httpx
    from openai import AsyncOpenAI
    from app.services.providers.openai_governed_transport import OpenAIGovernedTransport, RoleConfiguration
    from evaluation.governed_answers.catalog_index_reconciler import CatalogIndexReconciler
    from evaluation.governed_answers.corpus_runtime_inspection import inspect_corpus, CorpusInspectionWithheld

    writer, store, initial_barrier, proof, _, _ = setup_catalog
    class Index:
        dimension = 4
        def read_all(self, document_id, *, progress=None):
            snapshot = reconciler._snapshot(document_id, require_active=True)
            return [reconciler._point(snapshot, c, include_vector=False) for c in snapshot['chunks']]
    reconciler = CatalogIndexReconciler(writer, chunk_store=store, index=Index())
    calls = []
    async def exercise():
        async def handler(request):
            payload = json.loads(request.content)
            role = ['generation', 'statement', 'relevance'][len(calls)]
            calls.append(role)
            wire = json.loads(payload['input'][1]['content'])
            if role == 'generation':
                # OpenAI transport generation wire contains the context directly.
                value = dict(statement='Synthetic mocked candidate.', premise_ids=['premise-0', 'premise-1'],
                    relationship_references=[dict(source_premise_id='premise-0', target_premise_id='premise-1', kind='complements')], qualifications=[])
                if revoke:
                    writer.set_grants('synthetic', expected_permission_epoch=proof.permission_epoch, scopes=[])
            elif role == 'statement':
                value = dict(admissible=True, rejection_reasons=[], **{k: False for k in
                    ('unsupported_fact','certainty_inflation','causal_overreach','negation_reversal',
                     'fabricated_precision','conflict_suppression','unsupported_qualification','insufficient_support')})
            else:
                value = dict(request_sha256=wire['request_sha256'], answers_question=mode != 'reject', uncertain=False, reason='Mock only')
            return httpx.Response(200, json=dict(id='resp_mock', object='response', created_at=0,
                status='completed', model=payload['model'], error=None, incomplete_details=None,
                output=[dict(id='msg_mock', type='message', role='assistant', status='completed',
                             content=[dict(type='output_text', text=json.dumps(value), annotations=[])])]))
        clients = [AsyncOpenAI(api_key='synthetic-unused', max_retries=0,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler))) for _ in range(3)]
        transport = OpenAIGovernedTransport(**{role: RoleConfiguration(client=client, model='mock-'+role)
            for role, client in zip(('generation','statement','relevance'), clients)})
        try:
            return await inspect_corpus(reconciler=reconciler, session=initial_barrier.session,
                principal=initial_barrier.principal, document_id='document', chunk_indices=[0,1],
                question='What do these sources state?', relationships=[dict(source_premise_id='premise-0',
                    target_premise_id='premise-1', kind='complements', basis='Explicit synthetic hypothesis.')],
                transport=transport, current_gate_sha256=lambda:'a'*64, timeout_seconds=5)
        finally:
            await asyncio.gather(*(client.close() for client in clients))
    if revoke:
        with pytest.raises(PublicationDenied): asyncio.run(exercise())
        assert calls == ['generation']
    elif mode == 'reject':
        with pytest.raises(CorpusInspectionWithheld) as caught: asyncio.run(exercise())
        assert caught.value.reason == 'relevance_rejected'
        assert caught.value.attempted_calls == 3
        assert not hasattr(caught.value, 'candidate')
        with writer.transaction() as cursor:
            cursor.execute('SELECT count(*) AS n FROM inspection_publications')
            assert cursor.fetchone()['n'] == 0
    else:
        publication_id, checked = asyncio.run(exercise())
        assert len(publication_id) == 48 and calls == ['generation','statement','relevance']
        rendered = render_checked_inspection(checked)
        assert 'Synthetic mocked candidate.' in rendered
        assert checked.to_dict()['inspection_publication_binding']['document_id'] == 'document'
