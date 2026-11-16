import base64
import hashlib
import pytest
from app.services.governed_authentication import GovernedAuthenticationSession, password_record
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from app.services.sre.authorization import Access,Grant,SREAuthorizer,ACTIONS
from app.services.sre.store import SREStore

AT='2026-11-16T12:00:00Z'
REF='sha256:'+hashlib.sha256(b'explicit-synthetic-configuration').hexdigest()

def service(id='sentinel-api',app='sentinel-ai',tenant='tenant-a'):
    return dict(schema_version=1,tenant_id=tenant,application_id=app,service_id=id,service_name='Sentinel API',service_type='API',environment='development',monitoring_enabled=True,health_policy={'required_checks':['process-liveness'],'max_age_seconds':60},registered_at=AT,updated_at=AT,configuration_ref=REF)

def observation(id='observation-1',service_id='sentinel-api',app='sentinel-ai',tenant='tenant-a',source_time=AT):
    return dict(schema_version=1,tenant_id=tenant,application_id=app,service_id=service_id,observation_id=id,observation_type='SERVICE_HEALTH',source_id='synthetic-test-source',source_timestamp=source_time,ingested_at=AT,evidence_ref=REF,severity='INFO',data_quality='SOURCE_CLAIM',correlation_id='correlation-1',payload={'check_id':'process-liveness','outcome':'PASS'})

def dependency(id='db-api',source='database',dependent='sentinel-api'):
    return dict(schema_version=1,tenant_id='tenant-a',application_id='sentinel-ai',dependency_id=id,source_service_id=source,dependent_service_id=dependent,relationship_type='REQUIRES',created_at=AT,evidence_ref=REF)

class Catalog:
    def __init__(self,scope):
        salt,hashed=password_record('synthetic-sre-password')
        self.row=dict(principal_id='operator-sre',username='synthetic-sre',credential_epoch=1,permission_epoch=1,disabled=False,salt=salt,password_hash=hashed,scopes=[scope])
    def read_principal(self,username):return dict(self.row) if username=='synthetic-sre' else None

@pytest.fixture
def sre_setup(tmp_path):
    scope=EvidenceScope(organization_id='synthetic-org',collection='synthetic-sre',module='sre',topic='registry')
    catalog=Catalog(scope);grant=Grant('operator-sre',scope,'tenant-a','sentinel-ai',ACTIONS)
    authorizer=SREAuthorizer(catalog,(grant,));session=GovernedAuthenticationSession(catalog)
    principal=session.authenticate(authorization_values=('Basic '+base64.b64encode(b'synthetic-sre:synthetic-sre-password').decode(),),scope=scope)
    access=Access(session,principal);path=tmp_path/'sre.sqlite';store=SREStore.create(path,authorizer)
    value=dict(store=store,authorizer=authorizer,catalog=catalog,access=access,grant=grant,path=path,service=service,observation=observation,dependency=dependency,at=AT,ref=REF)
    yield value
    try:store.close()
    except Exception:pass
