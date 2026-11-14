"""Synthetic migration plans and dedicated PostgreSQL copies, no live sources."""
import base64
import copy
from dataclasses import replace
import hashlib
import os
from pathlib import Path
import uuid

import psycopg2
from psycopg2 import sql
import pytest

from app.services.governed_authentication import GovernedAuthenticationSession,password_record
from app.services.governed_catalog import CatalogWriter,CatalogConflict
from app.services.governed_legacy_migration import (
    GovernedLegacyMigrator,MigrationDenied,build_migration_plan,plan_digest,sha,validate_plan,
    MANDATORY_QUARANTINES,CATALOG_FIELDS,
)
from evaluation.governed_answers.content_addressed_sources import ContentAddressedSourceStore
from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore
from evaluation.governed_answers.legacy_extraction_checkpoint import create_checkpoint
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope

SCOPE=dict(organization_id='org',collection='manuals',module='ir',topic='sre')
DSN=os.getenv('SENTINEL_ISOLATED_POSTGRES_DSN')


@pytest.fixture
def fixture_plan(tmp_path):
    original=tmp_path/'original';original.write_bytes(b'Exact preserved original')
    source_hash=hashlib.sha256(original.read_bytes()).hexdigest()
    texts=['First verified source chunk.','Second verified chunk.']
    row=dict(id='legacy-document',file_hash=source_hash,chunk_count=2,status='indexed',embedding_model='synthetic',**SCOPE)
    points=[dict(document_id=row['id'],file_hash=source_hash,chunk_index=i,status=row['status'],embedding_model=row['embedding_model'],point_id=str(uuid.uuid4()),chunk_sha256=hashlib.sha256(text.encode()).hexdigest(),chunk_byte_length=len(text.encode()),**SCOPE) for i,text in enumerate(texts)]
    checkpoint=create_checkpoint(source_sha256=source_hash,byte_length=original.stat().st_size,policy_digest='b'*64,extraction_chunk_hashes=[point['chunk_sha256'] for point in points])
    inventory=dict(capture=dict(catalog_complete=True,points_complete=True),catalog=[row],points=points)
    arguments=dict(inventory=inventory,checkpoints=[checkpoint],allowed_policy_digests=['b'*64],source_paths={source_hash:str(original)},approved_scopes=[SCOPE])
    raw=[dict(id=point['point_id'],payload={**{k:v for k,v in point.items() if k not in ('point_id','chunk_sha256','chunk_byte_length')},'text':text}) for point,text in zip(points,texts)]
    return arguments,raw,original


def test_plan_identity_deterministic_and_no_implicit_scopes(fixture_plan):
    arguments,raw,original=fixture_plan
    plan=build_migration_plan(**arguments)
    other=build_migration_plan(**copy.deepcopy(arguments))
    assert plan==other and len(plan['entries'])==1
    validate_plan(plan,expected_plan_sha256=plan['plan_sha256'])
    args=dict(arguments,approved_scopes=[dict(SCOPE,topic='other')])
    denied=build_migration_plan(**args)
    assert not denied['entries'] and denied['excluded'][0]['reason']=='scope_not_reviewed'


@pytest.mark.parametrize('field,value',[('status','archiving'),('chunk_count',3)])
def test_ineligible_state_and_mismatch_excluded(fixture_plan,field,value):
    arguments,_,_=fixture_plan
    arguments['inventory']['catalog'][0][field]=value
    plan=build_migration_plan(**arguments)
    assert not plan['entries'] and plan['excluded']


def test_quarantines_cannot_be_removed_by_caller(fixture_plan):
    args,_,_=fixture_plan
    quarantine=next(iter(MANDATORY_QUARANTINES))
    old=args['inventory']['catalog'][0]['file_hash']
    args['inventory']['catalog'][0]['file_hash']=quarantine
    args['source_paths'][quarantine]=args['source_paths'][old]
    plan=build_migration_plan(**args)
    assert plan['excluded'][0]['reason']=='source_quarantined' and not plan['entries']


@pytest.mark.parametrize('mutation',['hash','metadata','missing','reorder_index'])
def test_checkpoint_point_disagreement_excluded(fixture_plan,mutation):
    args,_,_=fixture_plan
    points=args['inventory']['points']
    if mutation=='hash': points[0]['chunk_sha256']='e'*64
    elif mutation=='metadata': points[0]['topic']='other'
    elif mutation=='missing': points.pop()
    else: points[1]['chunk_index']=0
    plan=build_migration_plan(**args)
    assert not plan['entries'] and plan['excluded']


def test_pinned_plan_rejects_mutation(fixture_plan):
    args,_,_=fixture_plan
    plan=build_migration_plan(**args)
    pin=plan['plan_sha256'];plan['entries'][0]['source_path']='/tmp/elsewhere'
    with pytest.raises(MigrationDenied):validate_plan(plan,expected_plan_sha256=pin)


@pytest.fixture
def application(tmp_path,fixture_plan):
    if not DSN:pytest.skip('explicit disposable PostgreSQL DSN required')
    connection=psycopg2.connect(DSN)
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database(),current_setting('server_version_num')")
        database,version=cursor.fetchone()
        assert database=='sentinel_sprint21_rehearsal' and 160000<=int(version)<170000
    connection.close()
    schema='sentinel_migration_test_'+uuid.uuid4().hex
    legacy_schema='sentinel_legacy_test_'+uuid.uuid4().hex
    writer=CatalogWriter(lambda:psycopg2.connect(DSN),schema=schema);writer.install()
    args,raw,original=fixture_plan
    # Source is synthetic and lives in a separately scoped legacy schema.
    with writer.transaction() as cursor:
        cursor.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(legacy_schema)))
        cursor.execute(sql.SQL('CREATE TABLE {}.documents(id TEXT PRIMARY KEY,file_hash TEXT,organization_id TEXT,collection TEXT,module TEXT,topic TEXT,status TEXT,embedding_model TEXT,chunk_count INTEGER)').format(sql.Identifier(legacy_schema)))
        cursor.execute(sql.SQL('INSERT INTO {}.documents ({}) VALUES ({})').format(sql.Identifier(legacy_schema),sql.SQL(',').join(sql.Identifier(k) for k in CATALOG_FIELDS),sql.SQL(',').join(sql.Placeholder() for _ in CATALOG_FIELDS)),[args['inventory']['catalog'][0][k] for k in CATALOG_FIELDS])
    salt,password=password_record('synthetic-password')
    writer.provision_principal('principal','operator',salt,password)
    writer.set_grants('principal',expected_permission_epoch=1,scopes=[SCOPE])
    def authenticate(scope):
        session=GovernedAuthenticationSession(writer)
        principal=session.authenticate(authorization_values=('Basic '+base64.b64encode(b'operator:synthetic-password').decode(),),scope=EvidenceScope(**scope))
        return session,principal
    source_root=tmp_path/'source-cas';source_root.mkdir(mode=0o700)
    chunk_root=tmp_path/'chunk-cas';chunk_root.mkdir(mode=0o700)
    def read_points(ids):return [copy.deepcopy(point) for point in reversed(raw) if point['id'] in ids]
    migrator=GovernedLegacyMigrator(catalog=writer,source_store=ContentAddressedSourceStore(source_root),chunk_store=ContentAddressedChunkStore(chunk_root),read_points=read_points,authenticate_scope=authenticate,legacy_schema=legacy_schema)
    migrator.initialize()
    try:yield writer,migrator,args,raw,original
    finally:
        connection=psycopg2.connect(DSN)
        with connection:
            with connection.cursor() as cursor:
                for value in (schema,legacy_schema):cursor.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(value)))
        connection.close()


def test_actual_copy_resume_verifies_sql_cas_without_duplicates(application):
    writer,migrator,args,raw,original=application
    plan=build_migration_plan(**args)
    first=migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])
    assert first['migrated']==1 and not first['production_enabled']
    second=migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])
    assert second['verified_existing']==1 and second['migrated']==0
    with writer.transaction() as cursor:
        for table,count in [('documents',1),('versions',1),('chunks',2),('outbox',1),('legacy_migration_v1',1)]:
            cursor.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(sql.Identifier(table)))
            assert cursor.fetchone()['n']==count
        cursor.execute('SELECT state FROM documents');assert cursor.fetchone()['state']=='pending'
    assert original.read_bytes()==b'Exact preserved original'


def test_archived_source_never_has_committed_activation_intent(application):
    writer,migrator,args,raw,_=application
    args['inventory']['catalog'][0]['status']='archived'
    for point in args['inventory']['points']:point['status']='archived'
    for point in raw:point['payload']['status']='archived'
    with writer.transaction() as cursor:
        cursor.execute(sql.SQL("UPDATE {}.documents SET status='archived'").format(sql.Identifier(migrator.legacy_schema)))
    plan=build_migration_plan(**args)
    migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])
    with writer.transaction() as cursor:
        cursor.execute('SELECT state,lifecycle_epoch,index_epoch FROM documents')
        assert tuple(cursor.fetchone().values())==('archiving',2,2)
        cursor.execute('SELECT kind,status FROM outbox ORDER BY kind')
        assert [tuple(row.values()) for row in cursor.fetchall()]==[('archive','pending'),('create','superseded')]
    operation=writer.claim();assert operation['kind']=='archive'
    assert writer.acknowledge(operation['operation_id'],lease_token=operation['lease_token'],expected_manifest_sha256=operation['manifest_sha256'])['state']=='archived'
    assert migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])['verified_existing']==1


@pytest.mark.parametrize('mutation',['text','metadata','missing','duplicate'])
def test_current_point_change_cannot_create_catalog_rows(application,mutation):
    writer,migrator,args,raw,_=application
    plan=build_migration_plan(**args)
    if mutation=='text':raw[0]['payload']['text']='Altered bytes'
    elif mutation=='metadata':raw[0]['payload']['topic']='other'
    elif mutation=='missing':raw.pop()
    else:migrator.read_points=lambda ids:[raw[0],raw[0]]
    with pytest.raises(MigrationDenied):migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])
    with writer.transaction() as cursor:
        cursor.execute('SELECT count(*) AS n FROM documents');assert cursor.fetchone()['n']==0
        cursor.execute('SELECT count(*) AS n FROM legacy_migration_v1');assert cursor.fetchone()['n']==0


def test_legacy_catalog_change_is_checked_inside_atomic_write(application):
    writer,migrator,args,raw,_=application
    plan=build_migration_plan(**args)
    with writer.transaction() as cursor:
        cursor.execute(sql.SQL("UPDATE {}.documents SET status='archived'").format(sql.Identifier(migrator.legacy_schema)))
    with pytest.raises(MigrationDenied,match='legacy_catalog_changed'):
        migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])
    with writer.transaction() as cursor:
        cursor.execute('SELECT count(*) AS n FROM documents');assert cursor.fetchone()['n']==0


def test_sql_interruption_rolls_back_mapping_and_outbox_then_resume(application):
    writer,migrator,args,_,_=application
    plan=build_migration_plan(**args)
    original=writer._enqueue
    def fail(*arguments):
        original(*arguments)
        raise RuntimeError('synthetic lost operation')
    writer._enqueue=fail
    with pytest.raises(RuntimeError):migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])
    writer._enqueue=original
    with writer.transaction() as cursor:
        for table in ('documents','versions','chunks','outbox','legacy_migration_v1'):
            cursor.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(sql.Identifier(table)))
            assert cursor.fetchone()['n']==0
    assert migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])['migrated']==1


def test_permission_revocation_during_cas_io_denies_write(application):
    writer,migrator,args,_,_=application
    plan=build_migration_plan(**args)
    original=migrator.read_points
    def revoke(ids):
        result=original(ids)
        writer.set_grants('principal',expected_permission_epoch=2,scopes=[])
        return result
    migrator.read_points=revoke
    with pytest.raises((CatalogConflict,MigrationDenied)):
        migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])
    with writer.transaction() as cursor:
        cursor.execute('SELECT count(*) AS n FROM documents');assert cursor.fetchone()['n']==0


def test_resume_rejects_mapping_drift(application):
    writer,migrator,args,_,_=application
    plan=build_migration_plan(**args)
    migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])
    with writer.transaction() as cursor:cursor.execute("UPDATE legacy_migration_v1 SET plan_sha256=%s",('e'*64,))
    with pytest.raises(MigrationDenied,match='existing_mapping_conflict'):
        migrator.run(plan,expected_plan_sha256=plan['plan_sha256'])
