"""Loopback rollout checks; never load credentials from argv or print responses.

Default is read-only. --execute-synthetic-lifecycle additionally uploads exactly
one marker source and archives/restores/tombstones only the returned identity.
No provider call, legacy write or approval change is performed by this script.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile
import time
from urllib.parse import urlsplit
import uuid

import httpx

from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope

GOVERNED_HEADER = 'X-Sentinel-Governed-Authorization'


class VerificationFailure(Exception):
    def __init__(self, check):
        self.check = check
        super().__init__(check)


def load_credentials(path, expected_scope_count):
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > 65536):
            raise ValueError('private_credential_file_required')
        with os.fdopen(fd, 'r', encoding='utf-8') as stream:
            fd = None
            value = json.load(stream)
    finally:
        if fd is not None: os.close(fd)
    if type(value) is not dict or set(value) != {'outer','governed','scopes'}:
        raise ValueError('credential_file_shape')
    for role in ('outer','governed'):
        record = value[role]
        if type(record) is not dict or set(record) != {'username','password'}:
            raise ValueError('credential_role_shape')
        for field in ('username','password'):
            if type(record[field]) is not str or not 1 <= len(record[field]) <= 1024 or any(c in record[field] for c in '\r\n'):
                raise ValueError('invalid_credential_field')
        if ':' in record['username']: raise ValueError('invalid_basic_username')
    if type(value['scopes']) is not list or len(value['scopes']) != expected_scope_count:
        raise ValueError('exact_scope_inventory_required')
    value['scopes'] = [EvidenceScope.model_validate(s, strict=True).model_dump(mode='json') for s in value['scopes']]
    if len({json.dumps(s,sort_keys=True) for s in value['scopes']}) != len(value['scopes']):
        raise ValueError('duplicate_scope_inventory')
    return value


def basic(record):
    return 'Basic '+base64.b64encode((record['username']+':'+record['password']).encode()).decode()


def verify(client, credentials, *, execute=False, report=None, checkpoint=lambda:None,
           wait_seconds=120, monotonic=time.monotonic, sleeper=time.sleep):
    report = report if report is not None else {'checks':[]}
    headers = {'Authorization':basic(credentials['outer']), GOVERNED_HEADER:basic(credentials['governed'])}
    def check(label, condition, **facts):
        report['checks'].append(dict(check=label,passed=bool(condition),**facts));checkpoint()
        if not condition: raise VerificationFailure(label)
    def request(method, path, **kwargs):
        return client.request(method,path,headers=kwargs.pop('headers',headers),**kwargs)
    def rows(response):
        value=response.json()
        result=value.get('documents') if type(value) is dict else value
        if type(result) is not list or any(type(r) is not dict for r in result):
            raise VerificationFailure('document_listing_shape')
        return result
    for index,scope in enumerate(credentials['scopes']):
        response=request('GET','/governance/v2/documents',params=scope)
        check('granted_scope_'+str(index+1),response.status_code==200,http_status=response.status_code)
        check('granted_scope_listing_'+str(index+1),type(rows(response)) is list)
    scope=credentials['scopes'][0]
    wrong_outer=dict(credentials['outer'],password='verification-wrong-'+uuid.uuid4().hex)
    response=request('GET','/governance/v2/documents',params=scope,headers=dict(headers,Authorization=basic(wrong_outer)))
    check('wrong_outer_password_denied',response.status_code==401,http_status=response.status_code)
    ungranted=dict(scope,organization_id='verification-ungranted-'+uuid.uuid4().hex)
    response=request('GET','/governance/v2/documents',params=ungranted)
    check('ungranted_scope_denied',response.status_code in (401,403),http_status=response.status_code)
    response=request('GET','/governance/v2/documents',params=scope,headers={'Authorization':headers['Authorization']})
    check('outer_credentials_do_not_grant_v2',response.status_code==401,http_status=response.status_code)
    wrong=dict(credentials['governed'],password='verification-wrong-'+uuid.uuid4().hex)
    response=request('GET','/governance/v2/documents',params=scope,headers=dict(headers,**{GOVERNED_HEADER:basic(wrong)}))
    check('wrong_governed_password_denied',response.status_code==401,http_status=response.status_code)
    response=request('GET','/governance/v2/documents',params=scope,headers=[*headers.items(),(GOVERNED_HEADER,headers[GOVERNED_HEADER])])
    check('duplicate_governed_credentials_denied',response.status_code==401,http_status=response.status_code)
    response=request('GET','/cognition/answer/readiness')
    check('answer_readiness_http',response.status_code==200,http_status=response.status_code)
    readiness=response.json()
    check('answer_gate_disabled',readiness.get('enabled') is False and readiness.get('proposition_to_inference')=='closed')
    response=request('POST','/cognition/answer',json={'question':'Rollout verification: answer gate must remain closed.','organization_id':'default','module':'engineering','topic':'general','limit':1,'score_threshold':0.45})
    check('answer_gate_returns_503',response.status_code==503,http_status=response.status_code)
    if not execute:
        report['synthetic_lifecycle']='not_requested';checkpoint();return report
    marker='Sentinel isolated rollout verification '+uuid.uuid4().hex+'.\nPreserve this synthetic source only for operational verification.\n'
    response=request('POST','/governance/v2/sources',data=scope,files={'file':('sentinel-rollout-verification.txt',marker.encode(),'text/plain')})
    check('synthetic_source_accepted',response.status_code==202,http_status=response.status_code)
    accepted=response.json();document_id=accepted.get('document_id')
    check('accepted_source_hash_matches',accepted.get('source_sha256')==hashlib.sha256(marker.encode()).hexdigest())
    check('synthetic_identity_returned',type(document_id) is str and bool(document_id))
    report['synthetic_document_id']=document_id
    report['synthetic_source_sha256']=hashlib.sha256(marker.encode()).hexdigest();checkpoint()
    current=None
    def await_state(expected):
        nonlocal current
        deadline=monotonic()+wait_seconds
        while monotonic()<deadline:
            after=''
            for page in range(1000):
                if monotonic()>=deadline:break
                params=dict(scope,after=after,limit=100)
                response=request('GET','/governance/v2/documents',params=params)
                if response.status_code != 200: raise VerificationFailure('lifecycle_poll_http')
                matches=[r for r in rows(response) if r.get('document_id')==document_id]
                if len(matches)>1:raise VerificationFailure('duplicate_synthetic_identity')
                if matches:
                    current=matches[0]
                    if current.get('state')==expected:return current
                    break
                value=response.json()
                cursor=value.get('next_cursor') if type(value) is dict else None
                if cursor is None:break
                if type(cursor) is not str or not 1<=len(cursor)<=200 or cursor<=after:
                    raise VerificationFailure('lifecycle_poll_cursor')
                after=cursor
            else:raise VerificationFailure('lifecycle_poll_page_budget')
            sleeper(.5)
        raise VerificationFailure('await_'+expected)
    def transition(operation):
        if current is None: raise VerificationFailure('synthetic_state_missing')
        payload=dict(scope=scope,**{'expected_'+key:current[key] for key in ('lifecycle_epoch','content_epoch','index_epoch')})
        response=request('POST','/governance/v2/documents/'+document_id+'/'+operation,json=payload)
        check('synthetic_'+operation+'_accepted',response.status_code==202,http_status=response.status_code)
    def inspect(expected_success):
        response=request('POST','/governance/v2/inspect',json={'document_id':document_id,'scope':scope,'chunk_indices':[0]})
        if not expected_success:
            check('archived_inspection_denied',response.status_code in (403,409),http_status=response.status_code);return
        check('verified_inspection_http',response.status_code==200,http_status=response.status_code)
        value=response.json();sources=value.get('sources')
        check('verified_exact_synthetic_text',type(sources) is list and len(sources)==1 and sources[0].get('text')==marker)
        check('inspection_has_no_release_authority',value.get('production_enabled') is False and value.get('release_authorized') is False)
    await_state('active');check('synthetic_became_active',True);inspect(True)
    response=request('POST','/governance/v2/inspect',json={'document_id':document_id,'scope':ungranted,'chunk_indices':[0]})
    check('mismatched_scope_inspection_denied',response.status_code in (401,403),http_status=response.status_code)
    transition('archive');await_state('archived');inspect(False)
    transition('restore');await_state('active');inspect(True)
    transition('tombstone');await_state('tombstoned')
    check('synthetic_tombstone_cleanup',True)
    report['synthetic_lifecycle']='completed_tombstoned';checkpoint();return report


class PrivateReport:
    def __init__(self,path):
        self.path=Path(path)
        info=self.path.parent.stat()
        if self.path.parent.is_symlink() or info.st_uid!=os.getuid() or stat.S_IMODE(info.st_mode)!=0o700:
            raise ValueError('private_output_directory_required')
        fd=os.open(self.path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.close(fd)
        self.report={'version':'governed-workspace-rollout-verification-v1','status':'running','checks':[],
                     'provider_calls':0,'production_activation':False,'human_approval_recorded':False}
        self.checkpoint()
    def checkpoint(self):
        fd,name=tempfile.mkstemp(prefix='.verification-',dir=self.path.parent)
        try:
            with os.fdopen(fd,'w') as stream:
                json.dump(self.report,stream,sort_keys=True,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
            os.replace(name,self.path)
        finally:
            if os.path.exists(name):os.unlink(name)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',required=True,help='Loopback API base, e.g. http://127.0.0.1:8080/api')
    parser.add_argument('--credentials',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    parser.add_argument('--expected-scope-count',type=int,default=9)
    parser.add_argument('--execute-synthetic-lifecycle',action='store_true')
    args=parser.parse_args()
    url=urlsplit(args.base_url)
    if url.scheme not in ('http','https') or url.hostname not in ('127.0.0.1','localhost','::1') or url.username or url.password or url.query or url.fragment:
        raise ValueError('explicit_loopback_url_required')
    if not 1<=args.expected_scope_count<=100:raise ValueError('bounded_scope_count_required')
    credentials=load_credentials(args.credentials,args.expected_scope_count)
    result=PrivateReport(args.output)
    try:
        # A trailing slash and relative request paths preserve /api through Caddy.
        with httpx.Client(base_url=args.base_url.rstrip('/')+'/',timeout=30,follow_redirects=False,trust_env=False) as client:
            class RelativeClient:
                def request(self,method,path,**kwargs):return client.request(method,path.lstrip('/'),**kwargs)
            verify(RelativeClient(),credentials,execute=args.execute_synthetic_lifecycle,report=result.report,checkpoint=result.checkpoint)
        result.report['status']='passed'
    except Exception as exc:
        result.report['status']='failed';result.report['error_type']=type(exc).__name__
        if isinstance(exc,VerificationFailure):result.report['failed_check']=exc.check
        if result.report.get('synthetic_document_id') and result.report.get('synthetic_lifecycle')!='completed_tombstoned':
            result.report['synthetic_cleanup_required']=True
    finally:result.checkpoint()
    print(json.dumps({'status':result.report['status'],'checks':len(result.report['checks'])}))
    return 0 if result.report['status']=='passed' else 1


if __name__=='__main__':raise SystemExit(main())
