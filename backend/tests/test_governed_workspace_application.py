"""Configured sidecar startup/auth contracts; fake model bytes never accuracy proof."""
import hashlib
import json
from types import SimpleNamespace as NS

from fastapi.testclient import TestClient
import pytest
from qdrant_client import models

import app.governed_workspace_application as host
from app.governed_workspace_worker import run_worker
from evaluation.governed_answers.content_addressed_sources import ContentAddressedSourceStore
from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore
from test_governed_workspace_v2 import Catalog,AUTH,SCOPE


@pytest.fixture
def configuration(tmp_path):
    roots={key:tmp_path/key for key in ('sources','chunks','accepted','model')}
    for root in roots.values():root.mkdir(mode=0o700)
    data=b'Synthetic model artifact, not model weights.'
    (roots['model']/'weights').write_bytes(data)
    manifest=dict(version='sentinel-model-artifacts-v1',model_name='synthetic-model',dimension=4,files=[dict(path='weights',sha256=hashlib.sha256(data).hexdigest(),byte_length=len(data))])
    path=tmp_path/'model-manifest.json';path.write_text(json.dumps(manifest,sort_keys=True));path.chmod(0o600)
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    values=dict(version='sentinel-governed-workspace-v1',database_env='SENTINEL_TEST_ONLY_DSN',schema='sentinel_governed_testing',source_root=str(roots['sources']),chunk_root=str(roots['chunks']),accepted_source_root=str(roots['accepted']),qdrant_url='http://127.0.0.1:16333',collection='governed_v2_test',collection_identity=dict(sentinel_workspace_identity='a'*32,embedding_policy_sha256=digest,schema='governed-v2'),model_root=str(roots['model']),model_artifact_manifest=str(path),model_manifest_sha256=digest,model_name='synthetic-model',dimension=4,extraction_policy_sha256='b'*64,max_request_bytes=1075838976,max_concurrent_requests=2,worker=dict(max_seconds=100,lease_seconds=120,poll_seconds=1,max_operations=2))
    config=tmp_path/'workspace.json';config.write_text(json.dumps(values));config.chmod(0o600)
    return config,roots,values


def test_strict_configuration_and_complete_artifact_verification(configuration):
    path,roots,_=configuration
    config=host.load_configuration(str(path))
    assert host.verify_model_artifacts(config)['file_count']==1
    (roots['model']/'weights').write_bytes(b'changed')
    with pytest.raises(ValueError):host.verify_model_artifacts(config)


@pytest.mark.parametrize('change',['extra_file','symlink','manifest_hash','duplicate_config','public_config'])
def test_startup_refuses_unreviewed_or_changed_bytes(configuration,change):
    path,roots,values=configuration
    if change=='extra_file':(roots['model']/'extra').write_bytes(b'new')
    elif change=='symlink':(roots['model']/'link').symlink_to(roots['model']/'weights')
    elif change=='manifest_hash':values['model_manifest_sha256']='c'*64;path.write_text(json.dumps(values))
    elif change=='duplicate_config':path.write_text(path.read_text()[:-1]+',"dimension":4}')
    else:path.chmod(0o644)
    with pytest.raises(ValueError):host.verify_model_artifacts(host.load_configuration(str(path)))


def test_collection_adoption_requires_exact_reviewed_metadata_and_dimensions(configuration):
    path,_,_=configuration;config=host.load_configuration(str(path))
    info=NS(config=NS(params=NS(vectors=models.VectorParams(size=4,distance=models.Distance.COSINE)),metadata=config.collection_identity.copy()))
    client=NS(collection_exists=lambda _:True,get_collection=lambda _:info)
    host.verify_collection(client,config)
    info.config.metadata['sentinel_workspace_identity']='d'*32
    with pytest.raises(ValueError):host.verify_collection(client,config)
    info.config.metadata=config.collection_identity.copy();info.config.params.vectors=models.VectorParams(size=3,distance=models.Distance.COSINE)
    with pytest.raises(ValueError):host.verify_collection(client,config)


@pytest.fixture
def client(configuration,monkeypatch):
    path,roots,_=configuration;config=host.load_configuration(str(path));catalog=Catalog()
    runtime=NS(config=config,catalog=catalog,source_store=ContentAddressedSourceStore(roots['sources']),chunk_store=ContentAddressedChunkStore(roots['chunks']),model_verification={'file_count':1},close=lambda:None)
    monkeypatch.setattr(host,'build_runtime',lambda _:runtime)
    monkeypatch.setattr(host,'_extract',lambda path,name:'Server-derived clean text.')
    with TestClient(host.create_app(str(path))) as client:yield client,catalog,roots


def test_live_host_only_accepts_dedicated_header(client):
    c,catalog,roots=client
    assert c.get('/governance/v2/status').json()['provider_calls']==0
    response=c.post('/governance/v2/sources',headers={'Authorization':AUTH},data=SCOPE,files={'file':('source.txt',b'original')})
    assert response.status_code==401 and list(roots['accepted'].iterdir())==[]
    response=c.post('/governance/v2/sources',headers={host.AUTH_HEADER:AUTH,'Authorization':'Basic unrelated-outer-admin'},data=SCOPE,files={'file':('source.txt',b'original')})
    assert response.status_code==202 and len(catalog.creates)==1
    assert response.json()['production_enabled'] is False


def test_duplicate_custom_header_and_unauthorized_json_rejected_before_parse(client):
    c,_,_=client
    response=c.post('/governance/v2/inspect',headers=[(host.AUTH_HEADER,AUTH),(host.AUTH_HEADER,AUTH)],content=b'not JSON')
    assert response.status_code==401
    assert c.post('/governance/v2/inspect',headers={'Authorization':AUTH},content=b'x'*70000).status_code==401
    assert c.post('/governance/v2/inspect',headers={host.AUTH_HEADER:AUTH},content=b'x'*70000).status_code==413


def test_worker_limits_errors_and_does_not_leak_exception(configuration):
    config=host.load_configuration(str(configuration[0]))
    calls=[]
    def denied(**kwargs):calls.append(kwargs);raise ValueError('SECRET-DSN-MUST-NOT-ESCAPE')
    stop=NS(is_set=lambda:False,wait=lambda _:None)
    result=run_worker(NS(config=config,reconciler=NS(reconcile_once=denied)),stop=stop,clock=lambda:0)
    assert result['status']=='blocked' and result['denied_operations']==5
    assert 'SECRET' not in json.dumps(result)
    assert all(c['lease_seconds']==120 and c['timeout_seconds']==100 for c in calls)


def test_worker_success_budget_and_once(configuration):
    config=host.load_configuration(str(configuration[0]));calls=[]
    def success(**kwargs):calls.append(kwargs);return {'state':'active'}
    runtime=NS(config=config,reconciler=NS(reconcile_once=success))
    assert run_worker(runtime,clock=lambda:0)['completed_operations']==2
    assert run_worker(runtime,clock=lambda:0,once=True)['completed_operations']==1


def test_server_extraction_policy_is_stable_and_binds_runtime(configuration):
    digest=host.server_extraction_policy_sha256()
    assert len(digest)==64 and digest==host.server_extraction_policy_sha256()
    config=host.load_configuration(str(configuration[0]))
    with pytest.raises(ValueError,match='server_extraction_policy_mismatch'):
        host.build_runtime(config)


def test_real_dimension_adapter_does_not_use_fixture_default(configuration):
    from app.services.governed_embeddings import GovernedEmbeddingAdapter
    from evaluation.governed_answers.catalog_index_reconciler import CatalogIndexReconciler
    backend=NS(get_model_name=lambda:'verified-local-test',get_dimension=lambda:384,
               generate_embeddings=lambda texts:[[1.0]*384 for text in texts])
    adapter=GovernedEmbeddingAdapter(backend=backend,dimension=384,policy_sha256='a'*64)
    runtime=CatalogIndexReconciler(NS(),chunk_store=NS(),index=NS(dimension=384),vector_adapter=adapter)
    assert runtime.vector_adapter.embed(['test'])==[[1.0]*384]


def test_extraction_policy_changes_when_installed_dependency_changes(monkeypatch):
    import importlib.metadata
    before=host.server_extraction_policy_sha256()
    original=importlib.metadata.version
    monkeypatch.setattr(importlib.metadata,'version',lambda package:'changed-parser-version' if package=='pypdf' else original(package))
    assert host.server_extraction_policy_sha256()!=before

@pytest.mark.parametrize('filename',['source.png','source.JPG','source.mp4','source.wav'])
def test_governed_intake_holds_ocr_and_transcription_before_extraction(tmp_path,monkeypatch,filename):
    import app.services.media_extraction as media
    monkeypatch.setattr(media,'extract_source_text',lambda *_:pytest.fail('unreviewed derivative extractor invoked'))
    source=tmp_path/'retained-original';source.write_bytes(b'retained source')
    with pytest.raises(ValueError,match='extraction_requires_review'):
        host._extract(source,filename)
    assert source.read_bytes()==b'retained source'
