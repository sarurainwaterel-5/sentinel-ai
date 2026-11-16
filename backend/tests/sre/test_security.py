"""Independent adversarial tests for authenticated local SRE boundaries."""
import base64
from dataclasses import replace
import sqlite3
import pytest
from app.services.governed_authentication import GovernedAuthenticationSession, password_record
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from app.services.sre.authorization import Access, Grant, SREAuthorizer, ACTIONS
from app.services.sre.contracts import SREError
from app.services.sre.store import SREStore

SCOPE=EvidenceScope(organization_id='test-org',collection='sre',module='operations',topic='local')
AT='2026-11-16T12:00:00Z'
REF='sha256:'+'a'*64

class Catalog:
    def __init__(self):
        salt,hashed=password_record('synthetic-test-only')
        self.row=dict(principal_id='operator',username='operator',credential_epoch=1,permission_epoch=1,disabled=False,salt=salt,password_hash=hashed,scopes=[SCOPE.model_dump()])
    def read_principal(self,username):
        return self.row.copy() if username=='operator' else None

def authenticate(catalog):
    session=GovernedAuthenticationSession(catalog)
    h='Basic '+base64.b64encode(b'operator:synthetic-test-only').decode()
    principal=session.authenticate(authorization_values=(h,),scope=SCOPE)
    return Access(session,principal)

def service(**changes):
    value=dict(schema_version=1,tenant_id='tenant-a',application_id='sentinel-ai',service_id='sentinel-api',service_name='Sentinel API',service_type='API',environment='development',monitoring_enabled=True,health_policy={'required_checks':['process-liveness'],'max_age_seconds':60},registered_at=AT,updated_at=AT,configuration_ref=REF)
    value.update(changes);return value

def observation(**changes):
    value=dict(schema_version=1,tenant_id='tenant-a',application_id='sentinel-ai',service_id='sentinel-api',observation_id='obs-1',observation_type='SERVICE_HEALTH',source_id='local-check',source_timestamp=AT,ingested_at=AT,evidence_ref=REF,severity='INFO',data_quality='SOURCE_CLAIM',correlation_id='correlation-1',payload={'check_id':'process-liveness','outcome':'PASS'})
    value.update(changes);return value

@pytest.fixture
def secure(tmp_path):
    tmp_path.chmod(0o700)
    catalog=Catalog();access=authenticate(catalog)
    grant=Grant('operator',SCOPE,'tenant-a','sentinel-ai',ACTIONS)
    authorizer=SREAuthorizer(catalog,(grant,))
    store=SREStore.create(tmp_path/'sre.db',authorizer)
    store.register_service(access,service())
    yield store,catalog,access,authorizer
    store.close()

@pytest.mark.parametrize('tenant,app',[('tenant-b','sentinel-ai'),('tenant-a','other-app')])
@pytest.mark.parametrize('operation',['services','observations','dependencies','incidents','audit','verify_integrity','health','investigation_package'])
def test_all_read_interfaces_scope_denied(secure,tenant,app,operation):
    store,_,access,_=secure
    args=[access,tenant,app]
    if operation in ('observations','health','investigation_package'):args.append('sentinel-api')
    kwargs={'evaluated_at':AT} if operation=='health' else {}
    with pytest.raises(SREError,match='ACCESS_DENIED'):getattr(store,operation)(*args,**kwargs)

@pytest.mark.parametrize('mutation',[{'disabled':True},{'permission_epoch':2},{'credential_epoch':2},{'scopes':[]}])
def test_current_catalog_revocation_denies(secure,mutation):
    store,catalog,access,_=secure;catalog.row.update(mutation)
    with pytest.raises(SREError,match='ACCESS_DENIED'):store.services(access,'tenant-a','sentinel-ai')

@pytest.mark.parametrize('kind',['none','copied-principal','other-catalog','unissued-principal'])
def test_forged_or_unbound_handles_denied(secure,kind):
    store,_,access,_=secure
    invalid=None if kind=='none' else Access(access.session,replace(access.principal))
    if kind=='other-catalog':invalid=authenticate(Catalog())
    if kind=='unissued-principal':invalid=Access(GovernedAuthenticationSession(Catalog()),access.principal)
    with pytest.raises(SREError,match='ACCESS_DENIED'):store.services(invalid,'tenant-a','sentinel-ai')

def test_read_grant_cannot_change_configuration_or_validate(secure):
    store,catalog,access,_=secure
    store.authorizer=SREAuthorizer(catalog,(Grant('operator',SCOPE,'tenant-a','sentinel-ai',frozenset({'read'})),))
    assert len(store.services(access,'tenant-a','sentinel-ai'))==1
    with pytest.raises(SREError,match='ACCESS_DENIED'):store.register_service(access,service(service_id='other'))
    with pytest.raises(SREError,match='ACCESS_DENIED'):store.ingest(access,observation())
    with pytest.raises(SREError,match='ACCESS_DENIED'):store.validate_observation(access,'tenant-a','sentinel-ai','obs-1',AT,REF)

@pytest.mark.parametrize('changes',[{'data_quality':'VALIDATED'},{'evidence_ref':''},{'source_id':'sk-'+'a'*20},{'payload':{'check_id':'process-liveness','outcome':'PASS','password':'secret'}},{'payload':{'check_id':'Bearer token','outcome':'PASS'}}])
def test_untrusted_quality_provenance_and_secrets_rejected(secure,changes):
    store,_,access,_=secure
    with pytest.raises(SREError):store.ingest(access,observation(**changes))
    assert store.observations(access,'tenant-a','sentinel-ai','sentinel-api')==[]
    assert len(store.audit(access,'tenant-a','sentinel-ai'))==1

@pytest.mark.parametrize('sql',[
    "UPDATE sre_audit SET document='{}'",
    "UPDATE sre_services SET document='{}'",
    "UPDATE sre_services SET revision=99",
    "UPDATE sre_observations SET source_time='2020-01-01T00:00:00.000000Z'",
    "UPDATE sre_observations SET ingested_at='2020-01-01T00:00:00.000000Z'",
    "UPDATE sre_observations SET service='other-service'",
    "DELETE FROM sre_audit",
    "DELETE FROM sre_observations",
])
def test_direct_database_mutation_fails_closed(secure,sql):
    store,_,access,_=secure
    store.register_service(access,service(service_id='other-service'))
    store.ingest(access,observation())
    with sqlite3.connect(store.path) as db:db.execute(sql)
    with pytest.raises(SREError):store.verify_integrity(access,'tenant-a','sentinel-ai')
    with pytest.raises(SREError):store.services(access,'tenant-a','sentinel-ai')

def test_denied_cross_application_ingest_has_no_side_effect(secure):
    store,_,access,_=secure
    before=store.audit(access,'tenant-a','sentinel-ai')
    with pytest.raises(SREError,match='ACCESS_DENIED'):store.ingest(access,observation(application_id='other-app'))
    assert store.audit(access,'tenant-a','sentinel-ai')==before

def test_unknown_principal_mapping_has_no_supervisor_default(secure):
    store,catalog,access,_=secure;store.authorizer=SREAuthorizer(catalog,())
    with pytest.raises(SREError,match='ACCESS_DENIED'):store.services(access,'tenant-a','sentinel-ai')
