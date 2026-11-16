import json
import os
import sqlite3
import subprocess
import sys
import pytest
from app.services.sre.store import SREStore,Limits
from app.services.sre.contracts import SREError,digest


def test_registry_registration_idempotent_update_and_restart(sre_setup):
    f=sre_setup;s=f['store'];a=f['access'];r=f['service']()
    assert s.register_service(a,r)['status']=='REGISTERED'
    assert s.register_service(a,r)['status']=='DUPLICATE'
    r['service_name']='Changed'
    with pytest.raises(SREError,match='CONFLICT'):s.register_service(a,r)
    assert s.update_service(a,'tenant-a','sentinel-ai','sentinel-api',{'service_name':'Changed'},1,f['at'])['revision']==2
    with pytest.raises(SREError,match='STALE'):s.update_service(a,'tenant-a','sentinel-ai','sentinel-api',{'service_name':'Again'},1,f['at'])
    expected=s.services(a,'tenant-a','sentinel-ai');s.close()
    with_store=SREStore.open(f['path'],f['authorizer']);assert with_store.services(a,'tenant-a','sentinel-ai')==expected;with_store.close()


def test_source_claim_validation_is_separate_and_temporal(sre_setup):
    f=sre_setup;s=f['store'];a=f['access'];s.register_service(a,f['service']());r=f['observation']();s.ingest(a,r)
    assert s.health(a,'tenant-a','sentinel-ai','sentinel-api',evaluated_at=f['at'])['state']=='UNKNOWN'
    s.validate_observation(a,'tenant-a','sentinel-ai',r['observation_id'],'2026-11-16T12:00:01Z',f['ref'])
    assert s.health(a,'tenant-a','sentinel-ai','sentinel-api',evaluated_at=f['at'])['state']=='UNKNOWN'
    assert s.health(a,'tenant-a','sentinel-ai','sentinel-api',evaluated_at='2026-11-16T12:00:01Z')['state']=='HEALTHY'
    obs=s.observations(a,'tenant-a','sentinel-ai','sentinel-api')[0]
    assert obs['source_data_quality']=='SOURCE_CLAIM' and obs['data_quality']=='VALIDATED'


def test_ingestion_conflict_out_of_order_and_determinism(sre_setup):
    f=sre_setup;s=f['store'];a=f['access'];s.register_service(a,f['service']())
    newer=f['observation']('newer');older=f['observation']('older',source_time='2026-11-16T11:59:00Z')
    s.ingest(a,newer);s.ingest(a,older);before=s.audit(a,'tenant-a','sentinel-ai')
    assert s.ingest(a,newer)['status']=='DUPLICATE';assert s.audit(a,'tenant-a','sentinel-ai')==before
    newer['payload']['outcome']='FAIL'
    with pytest.raises(SREError,match='CONFLICT'):s.ingest(a,newer)
    assert [x['observation_id'] for x in s.observations(a,'tenant-a','sentinel-ai','sentinel-api')]==['older','newer']


def test_dependency_cycle_missing_reference_and_persistence(sre_setup):
    f=sre_setup;s=f['store'];a=f['access'];s.register_service(a,f['service']());s.register_service(a,f['service']('database'))
    s.add_dependency(a,f['dependency']());assert s.services(a,'tenant-a','sentinel-ai')[1]['dependency_references']==['db-api']
    with pytest.raises(SREError,match='CYCLE'):s.add_dependency(a,f['dependency']('reverse','sentinel-api','database'))
    with pytest.raises(SREError,match='CYCLE'):s.add_dependency(a,f['dependency']('self','database','database'))
    with pytest.raises(SREError,match='UNAVAILABLE'):s.add_dependency(a,f['dependency']('missing','not-registered','database'))
    expected=s.dependencies(a,'tenant-a','sentinel-ai');s.close();new=SREStore.open(f['path'],f['authorizer']);assert new.dependencies(a,'tenant-a','sentinel-ai')==expected;new.close()


def test_manual_incident_readiness_and_no_automatic_incident(sre_setup):
    f=sre_setup;s=f['store'];a=f['access'];s.register_service(a,f['service']());s.ingest(a,f['observation']())
    assert s.incidents(a,'tenant-a','sentinel-ai')==[]
    incident=dict(schema_version=1,tenant_id='tenant-a',application_id='sentinel-ai',service_id='sentinel-api',incident_id='incident-1',initial_observation_ids=['observation-1'],evidence_refs=[f['ref']],status='DRAFT',created_at=f['at'],updated_at=f['at'])
    s.create_incident(a,incident);assert s.create_incident(a,incident)['status']=='DUPLICATE'
    assert s.incidents(a,'tenant-a','sentinel-ai')[0]['status']=='DRAFT'
    incident['status']='EXECUTE_RECOVERY'
    with pytest.raises(SREError):s.create_incident(a,incident)


def test_explicit_migration_preserves_v1_records(sre_setup,tmp_path):
    f=sre_setup;path=tmp_path/'old.sqlite';old=SREStore.create(path,f['authorizer'],version=1)
    # Simulate an actual v1 predecessor record/audit before index-only v2 upgrade.
    from app.services.sre.contracts import service_record,canonical
    r=service_record(f['service']())
    old._db.execute('INSERT INTO sre_services VALUES (?,?,?,?,?,1)',('tenant-a','sentinel-ai','sentinel-api',canonical(r),digest(r)))
    old._audit('tenant-a','sentinel-ai','operator-sre','REGISTER','service','sentinel-api',digest(r),r['registered_at'])
    old.close()
    with pytest.raises(SREError):SREStore.open(path,f['authorizer'])
    new=SREStore.upgrade(path,f['authorizer']);assert new.services(f['access'],'tenant-a','sentinel-ai')[0]['service_id']=='sentinel-api';new.close()
    again=SREStore.open(path,f['authorizer']);assert again.services(f['access'],'tenant-a','sentinel-ai');again.close()


def test_transaction_failure_rolls_back_record_and_audit(sre_setup,monkeypatch):
    f=sre_setup;s=f['store'];original=s._audit
    def fail(*args):raise RuntimeError('synthetic injected interruption')
    monkeypatch.setattr(s,'_audit',fail)
    with pytest.raises(SREError):s.register_service(f['access'],f['service']())
    monkeypatch.setattr(s,'_audit',original)
    assert s.services(f['access'],'tenant-a','sentinel-ai')==[] and s.audit(f['access'],'tenant-a','sentinel-ai')==[]


def test_actual_child_process_interrupted_sql_write_recovers(sre_setup):
    f=sre_setup;s=f['store'];s.register_service(f['access'],f['service']());s.close()
    script="import os,sqlite3,sys;db=sqlite3.connect(sys.argv[1]);db.execute('BEGIN IMMEDIATE');db.execute('DELETE FROM sre_services');os._exit(19)"
    child=subprocess.run([sys.executable,'-c',script,str(f['path'])],timeout=10)
    assert child.returncode==19
    reopened=SREStore.open(f['path'],f['authorizer']);assert len(reopened.services(f['access'],'tenant-a','sentinel-ai'))==1;reopened.close()


def test_local_observation_and_scoped_future_package(sre_setup):
    f=sre_setup;s=f['store'];a=f['access'];s.register_service(a,f['service']())
    result=s.collect_local(a,'tenant-a','sentinel-ai',observed_at=f['at'],observation_id='local-1',correlation_id='local-run')
    assert result['EXTERNAL_MONITORING']=='DISABLED'
    assert s.health(a,'tenant-a','sentinel-ai','sentinel-api',evaluated_at=f['at'])['state']=='HEALTHY'
    p=s.investigation_package(a,'tenant-a','sentinel-ai','sentinel-api');assert p['sha256']==digest(p['package']);assert not p['package']['capabilities_active']


def test_capacity_fails_without_evidence_deletion(sre_setup):
    f=sre_setup;s=f['store'];s.limits=Limits(services=1);s.register_service(f['access'],f['service']())
    with pytest.raises(SREError,match='CAPACITY'):s.register_service(f['access'],f['service']('other'))
    assert len(s.services(f['access'],'tenant-a','sentinel-ai'))==1


@pytest.mark.parametrize('kind',['APPLICATION_ERROR','STRUCTURED_LOG','PERFORMANCE_METRIC','DEPENDENCY_FAILURE','DEPLOYMENT_EVENT','RESOURCE_USAGE','SECURITY_EVENT'])
def test_foundational_future_event_types(sre_setup,kind):
    f=sre_setup;s=f['store'];s.register_service(f['access'],f['service']());r=f['observation']();r['observation_type']=kind;r['payload']={'event_code':'synthetic-event','metric_name':'latency','value':2.5,'unit':'milliseconds'}
    assert s.ingest(f['access'],r)['status']=='INGESTED'


def test_foreign_database_refused_without_journal_configuration_mutation(sre_setup,tmp_path):
    path=tmp_path/'foreign.sqlite'
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE user_data(value TEXT)');db.execute("INSERT INTO user_data VALUES ('preserve')")
    path.chmod(0o600);before=path.read_bytes()
    with pytest.raises(SREError):SREStore.open(path,sre_setup['authorizer'])
    assert path.read_bytes()==before


@pytest.mark.parametrize('checks',[[{}],[[]],[1],['same','same'],[]])
def test_malformed_policy_is_bounded_error(sre_setup,checks):
    r=sre_setup['service']();r['health_policy']['required_checks']=checks
    with pytest.raises(SREError):sre_setup['store'].register_service(sre_setup['access'],r)


def test_no_authority_creates_no_database(sre_setup,tmp_path):
    path=tmp_path/'denied.sqlite'
    with pytest.raises(SREError):SREStore.create(path,None)
    assert not path.exists()


def test_same_scope_overlapping_handles_conflict_atomically(sre_setup):
    f=sre_setup;s=f['store'];a=f['access'];s.register_service(a,f['service']());other=SREStore.open(f['path'],f['authorizer'])
    s.update_service(a,'tenant-a','sentinel-ai','sentinel-api',{'service_name':'First'},1,f['at'])
    with pytest.raises(SREError,match='STALE'):other.update_service(a,'tenant-a','sentinel-ai','sentinel-api',{'service_name':'Second'},1,f['at'])
    assert other.services(a,'tenant-a','sentinel-ai')[0]['service_name']=='First';other.close()


def test_separate_process_opens_persisted_schema_and_ordered_state(sre_setup):
    f=sre_setup;s=f['store'];a=f['access'];s.register_service(a,f['service']());s.ingest(a,f['observation']());s.close()
    script="import json,sqlite3,sys;db=sqlite3.connect('file:'+sys.argv[1]+'?mode=ro',uri=True);print(json.dumps({'version':db.execute('SELECT max(version) FROM sre_metadata').fetchone()[0],'observations':db.execute('SELECT id,source_time FROM sre_observations ORDER BY source_time,id').fetchall(),'services':db.execute('SELECT id FROM sre_services ORDER BY id').fetchall()}))"
    child=subprocess.run([sys.executable,'-c',script,str(f['path'])],timeout=10,text=True,capture_output=True)
    assert child.returncode==0
    value=json.loads(child.stdout);assert value['version']==2 and value['services']==[['sentinel-api']] and value['observations'][0][0]=='observation-1'
