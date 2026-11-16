"""Explicit private development registry/restart rehearsal; no installed services.

Run with PYTHONPATH=backend. Creates a NEW private output directory and local DB.
Uses a short-lived local process identity (fresh credential only in memory), not
Rain's installed administrator, PostgreSQL credentials or external collectors.
"""
import argparse
import base64
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import secrets
from app.services.governed_authentication import GovernedAuthenticationSession,password_record
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from app.services.sre.authorization import Access,Grant,SREAuthorizer,ACTIONS
from app.services.sre.contracts import digest
from app.services.sre.store import SREStore


def run(output):
    output=Path(output)
    if not output.is_absolute() or output.resolve()!=output:raise ValueError('explicit_absolute_private_output_required')
    output.mkdir(mode=0o700,exist_ok=False)
    at=datetime.now(timezone.utc).isoformat()
    scope=EvidenceScope(organization_id='sentinel-local',collection='local-sre-development',module='sre',topic='registry')
    password=secrets.token_urlsafe(32);salt,hashed=password_record(password)
    class LocalProcessCatalog:
        def read_principal(self,username):
            if username!='local-sre-process':return None
            return dict(principal_id='local-sre-process',username=username,salt=salt,password_hash=hashed,credential_epoch=1,permission_epoch=1,disabled=False,scopes=[scope])
    catalog=LocalProcessCatalog();auth=GovernedAuthenticationSession(catalog)
    principal=auth.authenticate(authorization_values=('Basic '+base64.b64encode(('local-sre-process:'+password).encode()).decode(),),scope=scope)
    del password
    access=Access(auth,principal);authority=SREAuthorizer(catalog,(Grant(principal.principal_id,scope,'sentinel-local','sentinel-ai',ACTIONS),))
    store=SREStore.create(output/'sentinel-development-sre.sqlite',authority)
    configuration=dict(schema_version=1,tenant_id='sentinel-local',application_id='sentinel-ai',service_id='sentinel-api',service_name='Sentinel AI local process liveness',service_type='API',environment='development',monitoring_enabled=True,health_policy={'required_checks':['process-liveness'],'max_age_seconds':60},registered_at=at,updated_at=at,configuration_ref='sha256:'+digest({'policy':'explicit-development-process-liveness-only','freshness_seconds':60}))
    store.register_service(access,configuration)
    before=store.health(access,'sentinel-local','sentinel-ai','sentinel-api',evaluated_at=at)
    assert before['state']=='UNKNOWN'
    store.collect_local(access,'sentinel-local','sentinel-ai',observed_at=at,observation_id='development-liveness-1',correlation_id='sprint22a-local-rehearsal')
    health=store.health(access,'sentinel-local','sentinel-ai','sentinel-api',evaluated_at=at)
    package=store.investigation_package(access,'sentinel-local','sentinel-ai','sentinel-api')
    observations=store.observations(access,'sentinel-local','sentinel-ai','sentinel-api')
    audit=store.audit(access,'sentinel-local','sentinel-ai');store.close()
    restored=SREStore.open(output/'sentinel-development-sre.sqlite',authority)
    assert restored.health(access,'sentinel-local','sentinel-ai','sentinel-api',evaluated_at=at)==health
    assert restored.investigation_package(access,'sentinel-local','sentinel-ai','sentinel-api')==package
    assert restored.observations(access,'sentinel-local','sentinel-ai','sentinel-api')==observations
    integrity=restored.verify_integrity(access,'sentinel-local','sentinel-ai');restored.close()
    result=dict(schema_version=1,observed_at=at,application_id='sentinel-ai',tenant_id='sentinel-local',initial_health=before,health=health,observations=observations,audit=audit,restart_identical=True,integrity=integrity,package_sha256=package['sha256'],evidence_scope='CURRENT_PROCESS_CALLABLE_LIVENESS_ONLY_NOT_RUNNING_DAEMON_READINESS',authentication_basis='EXPLICIT_EPHEMERAL_LOCAL_PROCESS_IDENTITY_NOT_INSTALLED_OPERATOR',governance=package['package']['governance'])
    fd=os.open(output/'rehearsal-result.json',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:json.dump(result,f,indent=2);f.write('\n')
    return {'status':'LOCAL_REHEARSAL_COMPLETE','application_id':'sentinel-ai','health':health['state'],'restart_identical':True,'report':str(output/'rehearsal-result.json')}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args();print(json.dumps(run(args.output)))
