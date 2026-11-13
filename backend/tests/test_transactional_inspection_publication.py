"""Opt-in actual PostgreSQL+CAS+real SDK HTTP-mock composition."""
import asyncio
import base64
import hashlib
import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import replace

import psycopg2
from psycopg2 import sql
import pytest

from app.services.governed_catalog import CatalogWriter
from app.services.governed_authentication import GovernedAuthenticationSession, password_record
from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore
from evaluation.governed_answers.live_provider_rehearsal import load_inputs, canonical
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from evaluation.governed_answers.versioned_manifests import Version,Locator,VerifiedManifest,manifest_digest
from evaluation.governed_answers.transactional_inspection_publication import InspectionPublicationBarrier,PublicationDenied
from evaluation.governed_answers.runtime_inspection_rehearsal import InspectionResult
from test_runtime_inspection_rehearsal import exercise


@pytest.fixture
def setup_catalog(tmp_path,request):
    dsn = os.environ.get('SENTINEL_ISOLATED_POSTGRES_DSN')
    if not dsn:
        pytest.skip('explicit disposable PostgreSQL required')
    def connect():
        c = psycopg2.connect(dsn,connect_timeout=5)
        with c.cursor() as cursor:
            cursor.execute('SELECT current_database()')
            assert cursor.fetchone()[0] == 'sentinel_sprint21_rehearsal'
        c.rollback()
        return c
    writer = CatalogWriter(connect,schema='sentinel_publication_'+uuid.uuid4().hex)
    writer.install()
    try:
        scope = EvidenceScope(organization_id='synthetic',collection='review',module='synthetic',topic='review')
        salt,hashed = password_record('synthetic-test-password')
        writer.provision_principal('synthetic','operator',salt,hashed)
        writer.set_grants('synthetic',expected_permission_epoch=1,scopes=[scope.model_dump(mode='json')])
        cases,labels,_ = load_inputs()
        case = next(c for c in cases if labels[c['case_id']]['statement_admissible'] and labels[c['case_id']]['answers_question'])
        for index,source in enumerate(case['sources']):
            source.update(document_id='document',chunk_index=index)
        large=getattr(request,'param',None)=='large'
        if large:case['sources'][1]['chunk_index']=256
        context = {k:case[k] for k in ('question','sources','premises','relationships')}
        root = tmp_path/'chunks';root.mkdir(mode=0o700)
        store = ContentAddressedChunkStore(str(root))
        locators=[]
        texts=[source['text'] for source in context['sources']]
        if large:texts=[texts[0]]+['Synthetic paged chunk '+str(i) for i in range(1,256)]+[texts[1]]
        for index,text in enumerate(texts):
            data=text.encode();digest=hashlib.sha256(data).hexdigest()
            path=tmp_path/f'input{index}';path.write_bytes(data)
            store.put(str(path),expected_sha256=digest,expected_byte_length=len(data))
            locators.append(Locator(index,digest,len(data),'chunk-cas-v2:'+digest))
        version=Version('version',tuple(scope.model_dump().values()),'a'*64,50,'b'*64,len(locators),1,1,1)
        manifest=VerifiedManifest(version,tuple(locators),manifest_digest(version,locators))
        writer.create_version('document',manifest,chunk_store=store,expected_manifest_sha256=manifest.manifest_sha256)
        op=writer.claim()
        writer.acknowledge(op['operation_id'],lease_token=op['lease_token'],expected_manifest_sha256=manifest.manifest_sha256)
        session=GovernedAuthenticationSession(writer)
        authorization='Basic '+base64.b64encode(b'operator:synthetic-test-password').decode()
        principal=session.authenticate(authorization_values=(authorization,),scope=scope)
        barrier=InspectionPublicationBarrier(writer,session=session,principal=principal,chunk_store=store,current_gate_sha256=lambda:'a'*64,current_context_sha256=lambda:hashlib.sha256(canonical(context).encode()).hexdigest())
        barrier.initialize()
        barrier.set_gate(expected_epoch=0,sha256='a'*64)
        proof=barrier.capture(document_id='document',context_sha256=hashlib.sha256(canonical(context).encode()).hexdigest(),gate_sha256='a'*64)
        async def invoke(**kwargs):
            await barrier.evaluate(proof,**kwargs)
            return barrier._candidate
        overrides=dict(permission_epoch=proof.permission_epoch,credential_epoch=proof.credential_epoch,catalog_epoch=proof.catalog_epoch)
        yield writer,store,barrier,proof,invoke,overrides
    finally:
        c=connect()
        with c:
            with c.cursor() as cursor:
                cursor.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(writer.schema)))
        c.close()


def candidate(setup):
    writer,store,barrier,proof,invoke,overrides=setup
    report,calls=asyncio.run(exercise(invoke=invoke,binding_override=overrides,catalog_context=True))
    assert len(calls)==3
    return barrier._candidate_handle


def test_committed_publication_and_verified_read(setup_catalog):
    writer,store,barrier,proof,_,_=setup_catalog
    result=candidate(setup_catalog)
    receipt=barrier.publish(proof,result)
    assert type(receipt) is str
    assert barrier.read(proof,receipt).to_dict()['candidate']==barrier._candidate.to_dict()['candidate']
    assert not barrier.read(proof,receipt).to_dict()['production_enabled']
    with writer.transaction() as c:
        c.execute('SELECT count(*) FROM inspection_publications')
        assert c.fetchone()['count']==1

@pytest.mark.parametrize('mutation',['grant','credential','archive','tamper_cas'])
def test_changes_after_provider_work_prevent_durable_publication(setup_catalog,mutation):
    writer,store,barrier,proof,_,_=setup_catalog
    result=candidate(setup_catalog)
    if mutation=='grant':
        writer.set_grants('synthetic',expected_permission_epoch=2,scopes=[])
    elif mutation=='credential':
        salt,hashed=password_record('rotated')
        writer.rotate_credentials('synthetic',expected_credential_epoch=1,salt=salt,password_hash=hashed)
    elif mutation=='archive':
        writer.transition('document',expected_lifecycle_epoch=1,expected_content_epoch=1,expected_index_epoch=1,operation='archive')
    else:
        with writer.transaction() as c:
            c.execute('SELECT chunk_sha256 FROM chunks ORDER BY chunk_index LIMIT 1')
            digest=c.fetchone()['chunk_sha256']
        rootfd=store._store._root_fd()
        try:
            fd=os.open(digest,os.O_WRONLY,dir_fd=rootfd)
            os.write(fd,b'corrupt');os.close(fd)
        finally:os.close(rootfd)
    with pytest.raises((PublicationDenied,ValueError)):
        barrier.publish(proof,result)
    with writer.transaction() as c:
        c.execute('SELECT count(*) FROM inspection_publications')
        assert c.fetchone()['count']==0


def test_revoked_read_and_forged_result_denied(setup_catalog):
    writer,_,barrier,proof,_,_=setup_catalog
    result=candidate(setup_catalog)
    with pytest.raises(PublicationDenied):
        barrier.publish(proof,InspectionResult(barrier._candidate.report_json))
    with pytest.raises(PublicationDenied):
        barrier.publish(replace(proof),result)
    receipt=barrier.publish(proof,result)
    writer.set_grants('synthetic',expected_permission_epoch=2,scopes=[])
    with pytest.raises(PublicationDenied):barrier.read(proof,receipt)


def test_insert_failure_rolls_back_publication(setup_catalog):
    writer,_,barrier,proof,_,_=setup_catalog
    result=candidate(setup_catalog)
    with writer.transaction() as c:
        c.execute("ALTER TABLE inspection_publications ADD CONSTRAINT reject_test CHECK(publication_id='never')")
    with pytest.raises(psycopg2.IntegrityError):barrier.publish(proof,result)
    with writer.transaction() as c:
        c.execute('SELECT count(*) FROM inspection_publications')
        assert c.fetchone()['count']==0

def test_cross_catalog_auth_session_denied(setup_catalog):
    writer,store,barrier,_,_,_=setup_catalog
    other=CatalogWriter(writer.connect,schema='different_catalog')
    with pytest.raises(PublicationDenied):
        InspectionPublicationBarrier(other,session=barrier.session,principal=barrier.principal,chunk_store=store,current_gate_sha256=barrier.current_gate_sha256,current_context_sha256=barrier.current_context_sha256)


def test_actual_qdrant_current_version_reconciliation(setup_catalog):
    from evaluation.governed_answers.catalog_index_reconciler import GovernedRehearsalIndex,CatalogIndexReconciler,ReconciliationDenied
    url=os.environ.get('SENTINEL_ISOLATED_QDRANT_URL')
    if not url:pytest.skip('explicit disposable Qdrant required')
    writer,store,barrier,proof,_,_=setup_catalog
    index=GovernedRehearsalIndex(url,collection='sentinel_s21_v2_'+uuid.uuid4().hex)
    index.initialize()
    worker=CatalogIndexReconciler(writer,chunk_store=store,index=index)
    scope=barrier.principal.scope.model_dump(mode='json')
    try:
        writer.transition('document',expected_lifecycle_epoch=1,expected_content_epoch=1,expected_index_epoch=1,operation='archive')
        assert worker.reconcile_once()['state']=='archived'
        assert index.read_all('document')==[]
        with pytest.raises(ReconciliationDenied):worker.retrieve_verified(document_id='document',scope=scope)
        writer.transition('document',expected_lifecycle_epoch=2,expected_content_epoch=1,expected_index_epoch=2,operation='restore')
        assert worker.reconcile_once()['state']=='active'
        actual=worker.retrieve_verified(document_id='document',scope=scope)
        assert len(actual['chunks'])==2
        points=worker._points(actual)
        points[0]['payload']['text']='tampered'
        index.replace('document',points)
        with pytest.raises(ReconciliationDenied,match='index_readback_mismatch'):
            worker.retrieve_verified(document_id='document',scope=scope)
        index.replace('document',worker._points(actual))
        writer.transition('document',expected_lifecycle_epoch=3,expected_content_epoch=1,expected_index_epoch=3,operation='archive')
        original=index.begin_replace
        def late_replace(document_id):
            original(document_id)
            writer.transition('document',expected_lifecycle_epoch=4,expected_content_epoch=1,expected_index_epoch=4,operation='tombstone')
        index.begin_replace=late_replace
        with pytest.raises(ValueError,match='stale_acknowledgement|stale_or_expired_lease|stale_lease'):worker.reconcile_once()
        with pytest.raises(ReconciliationDenied):worker.retrieve_verified(document_id='document',scope=scope)
    finally:index.destroy()


def test_request_or_gate_changed_prevents_publication(setup_catalog):
    _,_,barrier,proof,_,_=setup_catalog
    handle=candidate(setup_catalog)
    barrier.current_gate_sha256=lambda:'c'*64
    with pytest.raises(PublicationDenied,match='request_or_gate_changed'):
        barrier.publish(proof,handle)


def test_evaluation_is_one_shot_after_failure(setup_catalog):
    _,_,barrier,proof,_,_=setup_catalog
    async def run():
        with pytest.raises(TypeError):
            await barrier.evaluate(proof)
        with pytest.raises(PublicationDenied,match='unissued_or_used_proof'):
            await barrier.evaluate(proof)
    asyncio.run(run())


def test_complete_index_sdk_publication_flow(setup_catalog):
    from evaluation.governed_answers.catalog_index_reconciler import GovernedRehearsalIndex,CatalogIndexReconciler
    url=os.environ.get('SENTINEL_ISOLATED_QDRANT_URL')
    if not url:pytest.skip('explicit disposable Qdrant required')
    writer,store,old,oldproof,_,_=setup_catalog
    index=GovernedRehearsalIndex(url,collection='sentinel_s21_v2_'+uuid.uuid4().hex)
    index.initialize()
    worker=CatalogIndexReconciler(writer,chunk_store=store,index=index)
    try:
        writer.transition('document',expected_lifecycle_epoch=1,expected_content_epoch=1,expected_index_epoch=1,operation='archive')
        worker.reconcile_once()
        writer.transition('document',expected_lifecycle_epoch=2,expected_content_epoch=1,expected_index_epoch=2,operation='restore')
        worker.reconcile_once()
        barrier=InspectionPublicationBarrier(writer,session=old.session,principal=old.principal,chunk_store=store,current_gate_sha256=old.current_gate_sha256,current_context_sha256=old.current_context_sha256)
        proof=barrier.capture(document_id='document',context_sha256=oldproof.context_sha256,gate_sha256=oldproof.gate_sha256)
        async def invoke(**kwargs):
            original=kwargs['retrieve']
            async def retrieve():
                verified=worker.retrieve_verified(document_id='document',scope=barrier.principal.scope.model_dump(mode='json'))
                case=await original()
                assert [s['text'] for s in case['sources']]==[c['text'] for c in verified['chunks']]
                return case
            kwargs['retrieve']=retrieve
            handle=await barrier.evaluate(proof,**kwargs)
            assert not hasattr(handle,'report_json')
            receipt=barrier.publish(proof,handle)
            return barrier.read(proof,receipt)
        report,calls=asyncio.run(exercise(invoke=invoke,binding_override=dict(permission_epoch=proof.permission_epoch,credential_epoch=proof.credential_epoch,catalog_epoch=proof.catalog_epoch),catalog_context=True))
        assert len(calls)==3 and report['preview_allowed'] is True
        assert not report['production_enabled']
    finally:index.destroy()


def test_concurrent_evaluation_budget_reserved_before_await(setup_catalog,monkeypatch):
    import evaluation.governed_answers.transactional_inspection_publication as module
    _,_,barrier,proof,_,_=setup_catalog
    async def run():
        entered=asyncio.Event()
        async def blocked(**kwargs):
            entered.set()
            await asyncio.Event().wait()
        monkeypatch.setattr(module,'inspect_runtime',blocked)
        task=asyncio.create_task(barrier.evaluate(proof))
        await entered.wait()
        with pytest.raises(PublicationDenied,match='unissued_or_used_proof'):
            await barrier.evaluate(proof)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):await task
        with pytest.raises(PublicationDenied,match='unissued_or_used_proof'):
            await barrier.evaluate(proof)
    asyncio.run(run())


def test_publication_and_revocation_serialize_on_authority_lock(setup_catalog,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor,TimeoutError as FutureTimeout
    import threading
    writer,_,barrier,proof,_,_=setup_catalog
    handle=candidate(setup_catalog)
    inserted,release=threading.Event(),threading.Event()
    original=writer.transaction
    class CursorProxy:
        def __init__(self,cursor):self.cursor=cursor
        def __getattr__(self,name):return getattr(self.cursor,name)
        def execute(self,statement,parameters=None):
            self.cursor.execute(statement,parameters)
            if type(statement) is str and statement.startswith('INSERT INTO inspection_publications'):
                inserted.set()
                assert release.wait(3)
    @contextmanager
    def wrapped():
        with original() as cursor:yield CursorProxy(cursor)
    monkeypatch.setattr(writer,'transaction',wrapped)
    with ThreadPoolExecutor(max_workers=2) as pool:
        publishing=pool.submit(barrier.publish,proof,handle)
        assert inserted.wait(3)
        revoking=pool.submit(writer.set_grants,'synthetic',expected_permission_epoch=2,scopes=[])
        try:
            with pytest.raises(FutureTimeout):revoking.result(timeout=.1)
        finally:release.set()
        receipt=publishing.result(timeout=3)
        assert revoking.result(timeout=3)==3
    with pytest.raises(PublicationDenied):barrier.read(proof,receipt)


def test_gate_epoch_rotation_denies_even_same_evidence_hash(setup_catalog):
    _,_,barrier,proof,_,_=setup_catalog
    handle=candidate(setup_catalog)
    assert barrier.set_gate(expected_epoch=1,sha256='a'*64)==2
    with pytest.raises(PublicationDenied):barrier.publish(proof,handle)
    with pytest.raises(PublicationDenied):barrier.set_gate(expected_epoch=1,sha256='b'*64)


def test_missing_sql_gate_denies_capture(setup_catalog):
    writer,store,old,proof,_,_=setup_catalog
    with writer.transaction() as c:c.execute('DELETE FROM inspection_gate')
    fresh=InspectionPublicationBarrier(writer,session=old.session,principal=old.principal,chunk_store=store,current_gate_sha256=old.current_gate_sha256,current_context_sha256=old.current_context_sha256)
    with pytest.raises(PublicationDenied,match='gate_evidence_missing_or_changed'):
        fresh.capture(document_id='document',context_sha256=proof.context_sha256,gate_sha256=proof.gate_sha256)


@pytest.mark.parametrize('tamper',['scope','source_length','version_identity'])
def test_untrusted_sql_source_version_associations_deny(setup_catalog,tamper):
    from evaluation.governed_answers.catalog_index_reconciler import CatalogIndexReconciler
    writer,store,barrier,proof,_,_=setup_catalog
    handle=candidate(setup_catalog)
    with writer.transaction() as c:
        if tamper=='source_length':
            c.execute('ALTER TABLE source_objects DISABLE TRIGGER immutable_source_objects')
            c.execute('UPDATE source_objects SET byte_length=byte_length+1')
        else:
            c.execute('ALTER TABLE versions DISABLE TRIGGER immutable_versions')
            if tamper=='scope':
                c.execute("UPDATE versions SET binding_json=jsonb_set(binding_json,'{scope,0}','\"other\"'::jsonb)")
            else:
                c.execute("UPDATE versions SET binding_json=jsonb_set(binding_json,'{document_version_id}','\"other\"'::jsonb)")
    with pytest.raises(PublicationDenied):barrier.publish(proof,handle)
    worker=CatalogIndexReconciler(writer,chunk_store=store,index=None)
    with pytest.raises(ValueError):worker._snapshot('document',require_active=True)


def test_gate_update_serializes_with_publication_insert(setup_catalog,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor,TimeoutError as FutureTimeout
    import threading
    writer,_,barrier,proof,_,_=setup_catalog
    handle=candidate(setup_catalog)
    inserted,release=threading.Event(),threading.Event()
    original=writer.transaction
    class CursorProxy:
        def __init__(self,cursor):self.cursor=cursor
        def __getattr__(self,name):return getattr(self.cursor,name)
        def execute(self,statement,parameters=None):
            self.cursor.execute(statement,parameters)
            if type(statement) is str and statement.startswith('INSERT INTO inspection_publications'):
                inserted.set();assert release.wait(3)
    @contextmanager
    def wrapped():
        with original() as cursor:yield CursorProxy(cursor)
    monkeypatch.setattr(writer,'transaction',wrapped)
    with ThreadPoolExecutor(max_workers=2) as pool:
        publishing=pool.submit(barrier.publish,proof,handle)
        assert inserted.wait(3)
        changing=pool.submit(barrier.set_gate,expected_epoch=1,sha256='a'*64)
        try:
            with pytest.raises(FutureTimeout):changing.result(timeout=.1)
        finally:release.set()
        receipt=publishing.result(timeout=3)
        assert changing.result(timeout=3)==2
    with pytest.raises(PublicationDenied):barrier.read(proof,receipt)


def test_fabricated_premise_cannot_reach_publication_even_if_mock_roles_accept(setup_catalog):
    writer,store,old,_,_,_=setup_catalog
    cases,labels,_=load_inputs()
    case=next(c for c in cases if labels[c['case_id']]['statement_admissible'] and labels[c['case_id']]['answers_question'])
    for index,source in enumerate(case['sources']):source.update(document_id='document',chunk_index=index)
    case['premises'][0]['statement']='Fabricated unsupported premise for boundary regression.'
    context={k:case[k] for k in ('question','sources','premises','relationships')}
    context_digest=hashlib.sha256(canonical(context).encode()).hexdigest()
    barrier=InspectionPublicationBarrier(writer,session=old.session,principal=old.principal,chunk_store=store,current_gate_sha256=old.current_gate_sha256,current_context_sha256=lambda:context_digest)
    proof=barrier.capture(document_id='document',context_sha256=context_digest,gate_sha256='a'*64)
    async def invoke(**kwargs):
        handle=await barrier.evaluate(proof,**kwargs)
        with pytest.raises(PublicationDenied,match='extractive_premises_required'):
            barrier.publish(proof,handle)
        return barrier._candidate
    report,calls=asyncio.run(exercise(failure='fabricated_premise',invoke=invoke,binding_override=dict(permission_epoch=proof.permission_epoch,credential_epoch=proof.credential_epoch,catalog_epoch=proof.catalog_epoch),catalog_context=True))
    assert len(calls)==3 and report['preview_allowed'] is True
    with writer.transaction() as c:
        c.execute('SELECT count(*) FROM inspection_publications')
        assert c.fetchone()['count']==0


@pytest.mark.parametrize('setup_catalog',['large'],indirect=True)
def test_actual_257_chunk_pagination_configurable_vectors_and_selected_publication(setup_catalog):
    from evaluation.governed_answers.catalog_index_reconciler import GovernedRehearsalIndex,CatalogIndexReconciler,ReconciliationDenied
    url=os.environ.get('SENTINEL_ISOLATED_QDRANT_URL')
    if not url:pytest.skip('explicit disposable Qdrant required')
    writer,store,old,oldproof,_,_=setup_catalog
    class Adapter:
        dimension=2
        model_name='synthetic-test-two-dimensional'
        policy_sha256='c'*64
        def __init__(self):self.batches=[]
        def embed(self,texts):
            self.batches.append(len(texts))
            return [[1.0,0.0] for text in texts]
    adapter=Adapter()
    index=GovernedRehearsalIndex(url,collection='sentinel_s21_v2_'+uuid.uuid4().hex,dimension=2)
    index.initialize()
    worker=CatalogIndexReconciler(writer,chunk_store=store,index=index,vector_adapter=adapter)
    try:
        writer.transition('document',expected_lifecycle_epoch=1,expected_content_epoch=1,expected_index_epoch=1,operation='archive');worker.reconcile_once()
        writer.transition('document',expected_lifecycle_epoch=2,expected_content_epoch=1,expected_index_epoch=2,operation='restore');worker.reconcile_once()
        assert adapter.batches==[32]*8+[1]
        assert len(index.read_all('document'))==257
        scope=old.principal.scope.model_dump(mode='json')
        with pytest.raises(ReconciliationDenied,match='explicit_chunk_selection_required'):
            worker.retrieve_verified(document_id='document',scope=scope)
        selected=worker.retrieve_verified(document_id='document',scope=scope,chunk_indices=[0,256])
        assert len(selected['chunks'])==2 and selected['full_manifest_chunk_count']==257
        assert selected['selected_chunk_indices']==[0,256]
        wrong=Adapter();wrong.policy_sha256='d'*64
        with pytest.raises(ReconciliationDenied,match='index_readback_mismatch'):
            CatalogIndexReconciler(writer,chunk_store=store,index=index,vector_adapter=wrong).retrieve_verified(document_id='document',scope=scope,chunk_indices=[0,256])
        barrier=InspectionPublicationBarrier(writer,session=old.session,principal=old.principal,chunk_store=store,current_gate_sha256=old.current_gate_sha256,current_context_sha256=old.current_context_sha256)
        proof=barrier.capture(document_id='document',context_sha256=oldproof.context_sha256,gate_sha256=oldproof.gate_sha256)
        async def invoke(**kwargs):
            original=kwargs['retrieve']
            async def retrieve():
                verified=worker.retrieve_verified(document_id='document',scope=scope,chunk_indices=[0,256])
                case=await original()
                assert [s['text'] for s in case['sources']]==[c['text'] for c in verified['chunks']]
                return case
            kwargs['retrieve']=retrieve
            handle=await barrier.evaluate(proof,**kwargs)
            receipt=barrier.publish(proof,handle)
            return barrier.read(proof,receipt)
        report,calls=asyncio.run(exercise(invoke=invoke,binding_override=dict(permission_epoch=proof.permission_epoch,credential_epoch=proof.credential_epoch,catalog_epoch=proof.catalog_epoch),catalog_context='large'))
        assert len(calls)==3 and [s['chunk_index'] for s in report['context']['sources']]==[0,256]
        # Tamper an unselected locator: full index readback must still reject.
        points=index.read_all('document')
        target=next(p for p in points if p['payload']['chunk_index']==128)
        target['payload']['chunk_sha256']='e'*64
        index.upsert_batch([dict(id=target['id'],payload=target['payload'],vector=[1.0,0.0])])
        with pytest.raises(ReconciliationDenied,match='index_readback_mismatch'):
            worker.retrieve_verified(document_id='document',scope=scope,chunk_indices=[0,256])
    finally:index.destroy()


@pytest.mark.parametrize('failure',['deadline','expired_lease'])
def test_worker_deadline_or_expired_lease_never_acknowledges(setup_catalog,failure):
    from evaluation.governed_answers.catalog_index_reconciler import GovernedRehearsalIndex,CatalogIndexReconciler,FixtureVectorAdapter
    url=os.environ.get('SENTINEL_ISOLATED_QDRANT_URL')
    if not url:pytest.skip('explicit disposable Qdrant required')
    writer,store,_,_,_,_=setup_catalog
    index=GovernedRehearsalIndex(url,collection='sentinel_s21_v2_'+uuid.uuid4().hex)
    index.initialize()
    worker=CatalogIndexReconciler(writer,chunk_store=store,index=index)
    try:
        writer.transition('document',expected_lifecycle_epoch=1,expected_content_epoch=1,expected_index_epoch=1,operation='archive');worker.reconcile_once()
        restore=writer.transition('document',expected_lifecycle_epoch=2,expected_content_epoch=1,expected_index_epoch=2,operation='restore')
        clock=[0]
        worker._clock=lambda:clock[0]
        class BlockingAdapter(FixtureVectorAdapter):
            def embed(self,texts):
                if failure=='deadline':clock[0]=2
                else:
                    with writer.transaction() as c:c.execute("UPDATE outbox SET lease_until=clock_timestamp()-interval '1 second' WHERE operation_id=%s",(restore['operation_id'],))
                return super().embed(texts)
        worker.vector_adapter=BlockingAdapter()
        with pytest.raises(ValueError,match='worker_deadline|stale_lease_renewal'):
            worker.reconcile_once(timeout_seconds=1,lease_seconds=120)
        with writer.transaction() as c:
            c.execute('SELECT status FROM outbox WHERE operation_id=%s',(restore['operation_id'],))
            assert c.fetchone()['status']=='leased'
            c.execute("SELECT state FROM documents WHERE document_id='document'")
            assert c.fetchone()['state']=='restoring'
    finally:index.destroy()
