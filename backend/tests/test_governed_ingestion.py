import base64
import pytest
from app.services.governed_ingestion import GovernedIngestionService
from app.services.governed_authentication import GovernedAuthenticationSession, password_record
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from evaluation.governed_answers.content_addressed_sources import ContentAddressedSourceStore
from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore

SCOPE=EvidenceScope(organization_id='org',collection='manuals',module='ir',topic='sre')
class Catalog:
    def __init__(self, fail=False):
        self.calls=[];self.fail=fail
        salt,hashed=password_record('synthetic-password')
        self.row=dict(principal_id='principal',username='operator',credential_epoch=1,permission_epoch=1,
                      disabled=False,salt=salt,password_hash=hashed,scopes=[SCOPE.model_dump()])
    def read_principal(self, username): return self.row.copy()
    def create_authorized_version(self, document, manifest, **kwargs):
        if self.fail: raise ValueError('stale_permission_epoch')
        self.calls.append((document,manifest,kwargs))
        return dict(document_id=document,status='pending')

@pytest.fixture
def configured(tmp_path):
    source=tmp_path/'original';source.write_bytes(b'original source')
    for name in ('source-cas','chunk-cas'): (tmp_path/name).mkdir(mode=0o700)
    catalog=Catalog()
    service=GovernedIngestionService(catalog=catalog,
        source_store=ContentAddressedSourceStore(tmp_path/'source-cas'),
        chunk_store=ContentAddressedChunkStore(tmp_path/'chunk-cas'))
    session=GovernedAuthenticationSession(catalog)
    principal=session.authenticate(authorization_values=('Basic '+base64.b64encode(b'operator:synthetic-password').decode(),),scope=SCOPE)
    return service,catalog,source,principal,session

def invoke(configured, session=None, text='Check the queue before restart.'):
    service,catalog,source,principal,original_session=configured
    return service.ingest(session=session or original_session,principal=principal,source_path=source,
        extracted_text=text,extraction_policy_sha256='a'*64,document_id='document',version_id='version')

def test_source_and_chunks_verified_before_pending_sql(configured):
    result=invoke(configured)
    assert result['status']=='pending' and result['chunk_count']==1
    assert not result['production_enabled']
    _,catalog,source,principal,session=configured
    assert source.read_bytes()==b'original source'
    _,manifest,kwargs=catalog.calls[0]
    assert kwargs['principal'] is principal and kwargs['authentication_session'] is session
    assert kwargs['expected_manifest_sha256']==manifest.manifest_sha256
    assert manifest.version.scope==('org','manuals','ir','sre')
    assert manifest.version.state=='pending'

@pytest.mark.parametrize('reject_at',[1,2])
def test_permission_change_never_creates_catalog_reference(configured,reject_at):
    session=configured[-1];original=session.recheck;calls=[]
    def racing(principal):
        calls.append(1)
        if len(calls)==reject_at: configured[1].row['permission_epoch']+=1
        return original(principal)
    session.recheck=racing
    with pytest.raises(ValueError): invoke(configured)
    assert configured[1].calls==[]

def test_cross_catalog_authentication_denied(configured):
    other=GovernedAuthenticationSession(Catalog())
    with pytest.raises(ValueError):invoke(configured,session=other)
    assert configured[1].calls==[]

def test_empty_extraction_is_pending_zero_chunks(configured):
    result=invoke(configured,text='  ')
    assert result['chunk_count']==0 and result['status']=='pending'

def test_sql_rejection_keeps_complete_objects_and_original(configured):
    configured[1].fail=True
    with pytest.raises(ValueError,match='stale_permission_epoch'): invoke(configured)
    assert configured[2].exists()
    assert list((configured[2].parent/'source-cas').iterdir())
    assert configured[1].calls==[]
