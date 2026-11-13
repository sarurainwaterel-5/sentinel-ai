"""HTTP behavior with real credentials and private CAS; no live route mounting."""
import base64
from pathlib import Path
import re

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.routes.governed_workspace_v2 import create_governed_workspace_router
from app.services.governed_authentication import GovernedAuthenticationSession, password_record
from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore
from evaluation.governed_answers.content_addressed_sources import ContentAddressedSourceStore
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope

SCOPE=dict(organization_id='org',collection='manuals',module='ir',topic='sre')
AUTH='Basic '+base64.b64encode(b'operator:synthetic-password').decode()


class Catalog:
    def __init__(self):
        salt,hashed=password_record('synthetic-password')
        self.record=dict(principal_id='principal',username='operator',credential_epoch=1,
            permission_epoch=1,disabled=False,salt=salt,password_hash=hashed,scopes=[SCOPE])
        self.creates=[]; self.transitions=[]; self.fail=False
    def read_principal(self,username):
        return self.record.copy() if username=='operator' else None
    def create_authorized_version(self,document_id,manifest,**kwargs):
        assert type(kwargs['authentication_session']) is GovernedAuthenticationSession
        assert kwargs['authentication_session'].bound_to(self)
        assert kwargs['authentication_session'].recheck(kwargs['principal'])
        assert manifest.manifest_sha256==kwargs['expected_manifest_sha256']
        self.creates.append((document_id,manifest,kwargs))
        if self.fail: raise ValueError('synthetic stale state')
        return dict(document_id=document_id,version_id=manifest.version.document_version_id,state='pending',operation_id='synthetic-operation')
    def transition_authorized(self,document_id,**kwargs):
        assert type(kwargs['authentication_session']) is GovernedAuthenticationSession
        assert kwargs['authentication_session'].bound_to(self)
        assert kwargs['authentication_session'].recheck(kwargs['principal'])
        self.transitions.append((document_id,kwargs))
        if self.fail: raise ValueError('synthetic stale state')
        return dict(document_id=document_id,state={'archive':'archiving','restore':'restoring','tombstone':'tombstoned'}[kwargs['operation']])


@pytest.fixture
def workspace(tmp_path):
    roots={name:tmp_path/name for name in ('accepted','sources','chunks')}
    for path in roots.values(): path.mkdir(mode=0o700)
    catalog=Catalog(); extracted=[]
    def extractor(path,name):
        extracted.append((path,name,path.read_bytes()))
        return 'Server-derived evidence text.'
    app=FastAPI()
    app.include_router(create_governed_workspace_router(catalog=catalog,
        source_store=ContentAddressedSourceStore(roots['sources']),
        chunk_store=ContentAddressedChunkStore(roots['chunks']),accepted_source_root=roots['accepted'],
        extraction_policy_sha256='d'*64,extractor=extractor))
    with TestClient(app) as client:
        yield client,catalog,roots,extracted


def upload(client,*,headers=None,scope=None,filename='original.txt',data=b'Exact original bytes.'):
    return client.post('/governance/v2/sources',headers=headers if headers is not None else {'Authorization':AUTH},
        data=scope or SCOPE,files={'file':(filename,data,'application/octet-stream')})


def test_http_intake_uses_server_extractor_and_real_cas(workspace):
    client,catalog,roots,extracted=workspace
    response=upload(client)
    assert response.status_code==202
    result=response.json()
    assert result['state']=='pending' and result['chunk_count']==1
    assert not result['production_enabled'] and not result['release_authorized']
    assert len(catalog.creates)==1 and len(extracted)==1
    path,name,data=extracted[0]
    assert path.parent==roots['accepted'] and name=='original.txt' and data==b'Exact original bytes.'
    assert path.stat().st_mode & 0o777==0o600
    manifest=catalog.creates[0][1]
    assert manifest.version.extraction_policy_sha256=='d'*64
    assert (roots['sources']/manifest.version.source_sha256).read_bytes()==data
    row=manifest.locators[0]
    assert (roots['chunks']/row.chunk_sha256).read_text()=='Server-derived evidence text.'


@pytest.mark.parametrize('headers', [[], [('Authorization',AUTH),('Authorization',AUTH)], {'X-Forwarded-User':'operator'}, {'Authorization':'Basic '+base64.b64encode(b'operator:wrong').decode()}])
def test_bad_or_duplicate_auth_denies_before_accepted_file_or_sql(workspace,headers):
    client,catalog,roots,extracted=workspace
    response=upload(client,headers=headers)
    assert response.status_code==401
    assert response.headers['www-authenticate'].startswith('Basic')
    assert not catalog.creates and not extracted
    assert list(roots['accepted'].iterdir())==[]
    assert list(roots['sources'].iterdir())==[]


def test_ungranted_exact_scope_denied_before_writes(workspace):
    client,catalog,roots,extracted=workspace
    assert upload(client,scope=dict(SCOPE,topic='other')).status_code==401
    assert not catalog.creates and not extracted and not list(roots['accepted'].iterdir())


@pytest.mark.parametrize('filename', ['../../escape.txt','/tmp/escape.txt',r'..\..\escape.txt','../../strange.𝘱𝘥𝘧','../../bad.verylongextension'])
def test_client_filename_cannot_control_accepted_path(workspace,filename):
    client,catalog,roots,extracted=workspace
    response=upload(client,filename=filename)
    assert response.status_code==202
    path=extracted[0][0]
    assert path.parent==roots['accepted']
    assert re.fullmatch('[a-f0-9]{32}(\\.[a-z0-9]{1,11})?',path.name)
    assert path.read_bytes()==b'Exact original bytes.'
    assert not (roots['accepted'].parent/'escape.txt').exists()


def test_catalog_rejection_returns_fixed_error_and_keeps_original(workspace):
    client,catalog,roots,extracted=workspace
    catalog.fail=True
    response=upload(client)
    assert response.status_code==409
    assert response.json()=={'detail':'Intake withheld; accepted source retained for inspection.'}
    assert len(list(roots['accepted'].iterdir()))==1
    assert list(roots['accepted'].iterdir())[0].read_bytes()==b'Exact original bytes.'


def test_empty_original_has_no_extraction_or_sql(workspace):
    client,catalog,roots,extracted=workspace
    response=upload(client,data=b'')
    assert response.status_code==422 and not catalog.creates and not extracted


@pytest.mark.parametrize('operation,expected', [('archive','archiving'),('restore','restoring'),('tombstone','tombstoned')])
def test_http_lifecycle_passes_issued_session_and_exact_epochs(workspace,operation,expected):
    client,catalog,_,_=workspace
    response=client.post('/governance/v2/documents/document-1/'+operation,
        headers={'Authorization':AUTH},json=dict(scope=SCOPE,expected_lifecycle_epoch=3,expected_content_epoch=2,expected_index_epoch=4))
    assert response.status_code==202 and response.json()['state']==expected
    document,args=catalog.transitions[0]
    assert document=='document-1' and args['operation']==operation
    assert (args['expected_lifecycle_epoch'],args['expected_content_epoch'],args['expected_index_epoch'])==(3,2,4)
    assert args['principal'].scope==EvidenceScope(**SCOPE)
    assert response.json()['production_enabled'] is False


def test_unsupported_operation_and_malformed_epochs_never_mutate(workspace):
    client,catalog,_,_=workspace
    body=dict(scope=SCOPE,expected_lifecycle_epoch=1,expected_content_epoch=1,expected_index_epoch=1)
    assert client.post('/governance/v2/documents/doc/delete',headers={'Authorization':AUTH},json=body).status_code==422
    assert client.post('/governance/v2/documents/doc/archive',headers={'Authorization':AUTH},json=dict(body,expected_lifecycle_epoch=True)).status_code==422
    assert not catalog.transitions


def test_lifecycle_denial_before_writer_and_stale_conflict(workspace):
    client,catalog,_,_=workspace
    body=dict(scope=SCOPE,expected_lifecycle_epoch=1,expected_content_epoch=1,expected_index_epoch=1)
    assert client.post('/governance/v2/documents/doc/archive',headers=[('Authorization',AUTH),('Authorization',AUTH)],json=body).status_code==401
    assert not catalog.transitions
    catalog.fail=True
    assert client.post('/governance/v2/documents/doc/archive',headers={'Authorization':AUTH},json=body).status_code==409


def test_bad_headers_rejected_before_multipart_parser(workspace,monkeypatch):
    import starlette.formparsers
    def forbidden(*args,**kwargs):
        raise AssertionError('Unauthenticated parser must never spool a file')
    monkeypatch.setattr(starlette.formparsers,'SpooledTemporaryFile',forbidden)
    response=upload(workspace[0],headers=[])
    assert response.status_code==401


def test_declared_oversize_denied_before_multipart_parser(workspace,monkeypatch):
    import starlette.formparsers
    def forbidden(*args,**kwargs):
        raise AssertionError('Oversized request must never spool a file')
    monkeypatch.setattr(starlette.formparsers,'SpooledTemporaryFile',forbidden)
    response=upload(workspace[0],headers={'Authorization':AUTH,'Content-Length':str(1024**3+2*1024**2+1)})
    assert response.status_code==413


def test_streaming_body_limit_without_content_length(workspace):
    _,catalog,roots,_=workspace
    app=FastAPI()
    app.include_router(create_governed_workspace_router(catalog=catalog,
        source_store=ContentAddressedSourceStore(roots['sources']),chunk_store=ContentAddressedChunkStore(roots['chunks']),
        accepted_source_root=roots['accepted'],extraction_policy_sha256='d'*64,extractor=lambda *_:'text',max_request_bytes=256))
    body=b'--boundary\r\nContent-Disposition: form-data; name="file"; filename="source.txt"\r\n\r\n'+b'x'*1024+b'\r\n--boundary--\r\n'
    with TestClient(app) as client:
        response=client.post('/governance/v2/sources',headers={'Authorization':AUTH,'Content-Type':'multipart/form-data; boundary=boundary'},content=iter([body[:128],body[128:]]))
    assert response.status_code==413
    assert not list(roots['accepted'].iterdir())
