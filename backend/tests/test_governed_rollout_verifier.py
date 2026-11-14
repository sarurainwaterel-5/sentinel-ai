"""Verifier tests use HTTP mocks, never the actual installation or real secrets."""
import hashlib
import json
from pathlib import Path
import re

import httpx
import pytest

from scripts.verify_governed_workspace import verify,basic,GOVERNED_HEADER,VerificationFailure,load_credentials


def credentials():
    return {'outer':{'username':'outer','password':'synthetic-outer'},
            'governed':{'username':'Rain','password':'synthetic-governed'},
            'scopes':[dict(organization_id='org',collection='scope'+str(i),module='ir',topic='sre') for i in range(9)]}


class Server:
    def __init__(self,creds):
        self.creds=creds;self.uploads=0;self.transitions=[];self.marker=None
        self.row=dict(document_id='returned-synthetic-id',state='active',lifecycle_epoch=1,content_epoch=1,index_epoch=1)
        self.failed_gate=False
    def __call__(self,request):
        outer=basic(self.creds['outer']); governed=basic(self.creds['governed'])
        if request.headers.get('Authorization')!=outer:return httpx.Response(401,json={})
        path=request.url.path
        if path.endswith('/cognition/answer/readiness'):
            return httpx.Response(200,json=dict(enabled=self.failed_gate,proposition_to_inference='closed'))
        if path.endswith('/cognition/answer'):return httpx.Response(503,json={})
        if request.headers.get_list(GOVERNED_HEADER)!=[governed]:return httpx.Response(401,json={})
        if request.method=='GET':
            scope={key:value for key,value in request.url.params.items() if key not in ('after','limit')}
            if scope not in self.creds['scopes']:return httpx.Response(401,json={})
            return httpx.Response(200,json={'documents':[self.row] if self.uploads else []})
        if path.endswith('/sources'):
            self.uploads+=1
            self.marker=re.search(rb'Sentinel isolated rollout verification [a-f0-9]{32}\.\nPreserve this synthetic source only for operational verification\.\n',request.content).group().decode()
            return httpx.Response(202,json=dict(self.row,source_sha256=hashlib.sha256(self.marker.encode()).hexdigest()))
        payload=json.loads(request.content)
        if payload['scope'] not in self.creds['scopes']:return httpx.Response(401,json={})
        if path.endswith('/inspect'):
            if self.row['state']!='active':return httpx.Response(409,json={})
            return httpx.Response(200,json=dict(sources=[dict(text=self.marker)],production_enabled=False,release_authorized=False))
        operation=path.rsplit('/',1)[1]
        assert '/documents/returned-synthetic-id/' in path
        assert payload['expected_lifecycle_epoch']==self.row['lifecycle_epoch']
        self.transitions.append(operation)
        self.row['state']={'archive':'archived','restore':'active','tombstone':'tombstoned'}[operation]
        self.row['lifecycle_epoch']+=1;self.row['index_epoch']+=1
        return httpx.Response(202,json=self.row)


def test_default_checks_all_nine_scopes_without_mutation_or_provider_calls():
    creds=credentials();server=Server(creds)
    with httpx.Client(transport=httpx.MockTransport(server),base_url='http://127.0.0.1') as client:
        result=verify(client,creds)
    assert all(r['passed'] for r in result['checks'])
    assert sum(r['check'].startswith('granted_scope_') and 'listing' not in r['check'] for r in result['checks'])==9
    assert server.uploads==0 and server.transitions==[]
    assert result['synthetic_lifecycle']=='not_requested'
    assert 'synthetic-governed' not in json.dumps(result)


def test_explicit_lifecycle_only_mutates_returned_synthetic_identity():
    creds=credentials();server=Server(creds)
    with httpx.Client(transport=httpx.MockTransport(server),base_url='http://127.0.0.1') as client:
        result=verify(client,creds,execute=True)
    assert server.uploads==1 and server.transitions==['archive','restore','tombstone']
    assert result['synthetic_document_id']=='returned-synthetic-id'
    assert result['synthetic_lifecycle']=='completed_tombstoned'
    assert all(r['passed'] for r in result['checks'])
    assert 'Preserve this synthetic source' not in json.dumps(result)


def test_enabled_answer_gate_stops_before_synthetic_upload():
    creds=credentials();server=Server(creds);server.failed_gate=True
    with httpx.Client(transport=httpx.MockTransport(server),base_url='http://127.0.0.1') as client:
        with pytest.raises(VerificationFailure,match='answer_gate_disabled'):
            verify(client,creds,execute=True)
    assert not server.uploads and not server.transitions


def test_private_credential_shape_permissions_and_scope_count(tmp_path):
    path=tmp_path/'credentials.json';path.write_text(json.dumps(credentials()));path.chmod(0o600)
    assert load_credentials(path,9)==credentials()
    with pytest.raises(ValueError,match='exact_scope_inventory_required'):load_credentials(path,8)
    path.chmod(0o644)
    with pytest.raises(ValueError,match='private_credential_file_required'):load_credentials(path,9)
    link=tmp_path/'link';link.symlink_to(path)
    with pytest.raises(OSError):load_credentials(link,9)


def test_lifecycle_finds_synthetic_identity_after_more_than_100_documents():
    creds=credentials();server=Server(creds);pages=[]
    def paginated(request):
        if (request.method=='GET' and request.url.path.endswith('/governance/v2/documents')
                and server.uploads):
            params=dict(request.url.params)
            scope={key:params[key] for key in creds['scopes'][0]}
            assert scope==creds['scopes'][0]
            after=params.get('after','');pages.append(after)
            if not after:
                existing=[dict(document_id=f'existing-{i:03d}',state='active') for i in range(100)]
                return httpx.Response(200,json=dict(documents=existing,next_cursor='existing-099'))
            assert after=='existing-099'
            return httpx.Response(200,json=dict(documents=[server.row],next_cursor=None))
        return server(request)
    with httpx.Client(transport=httpx.MockTransport(paginated),base_url='http://127.0.0.1') as client:
        result=verify(client,creds,execute=True)
    assert pages==['','existing-099']*4
    assert server.uploads==1 and server.transitions==['archive','restore','tombstone']
    assert result['synthetic_lifecycle']=='completed_tombstoned'


def test_lifecycle_rejects_nonadvancing_pagination_cursor():
    creds=credentials();server=Server(creds)
    def looping(request):
        if request.method=='GET' and request.url.path.endswith('/governance/v2/documents') and server.uploads:
            return httpx.Response(200,json=dict(documents=[],next_cursor='unchanged'))
        return server(request)
    with httpx.Client(transport=httpx.MockTransport(looping),base_url='http://127.0.0.1') as client:
        with pytest.raises(VerificationFailure,match='lifecycle_poll_cursor'):
            verify(client,creds,execute=True)
    assert server.uploads==1 and server.transitions==[]
