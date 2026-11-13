"""Dedicated PostgreSQL16 integration tests; no live catalog modification."""
import base64
from dataclasses import replace
import hashlib
import os
import uuid

import psycopg2
from psycopg2 import sql
import pytest

from app.services.governed_catalog import CatalogWriter, CatalogConflict, scope_key
from app.services.governed_authentication import GovernedAuthenticationSession, password_record
from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from evaluation.governed_answers.versioned_manifests import Version, Locator, VerifiedManifest, manifest_digest

SCOPE = dict(organization_id='org',collection='manuals',module='ir',topic='sre')
DSN = os.getenv('SENTINEL_ISOLATED_POSTGRES_DSN')


@pytest.fixture
def catalog():
    if not DSN: pytest.skip('explicit disposable PostgreSQL DSN required')
    probe = psycopg2.connect(DSN)
    try:
        with probe.cursor() as cursor:
            cursor.execute('SELECT current_database(),current_setting(\'server_version_num\')')
            database,version = cursor.fetchone()
            assert database == 'sentinel_sprint21_rehearsal' and 160000 <= int(version) < 170000
    finally: probe.close()
    schema = 'sentinel_catalog_test_' + uuid.uuid4().hex
    writer = CatalogWriter(lambda: psycopg2.connect(DSN),schema=schema)
    writer.install()
    try: yield writer
    finally:
        conn = psycopg2.connect(DSN)
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
        finally: conn.close()


@pytest.fixture
def prepared(tmp_path):
    root = tmp_path / 'chunks'; root.mkdir(mode=0o700)
    source = tmp_path / 'chunk'; source.write_bytes(b'Verified exact text.')
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    store = ContentAddressedChunkStore(str(root))
    store.put(str(source),expected_sha256=sha,expected_byte_length=source.stat().st_size)
    version = Version('version-1',tuple(SCOPE.values()),'a'*64,100,'b'*64,1,1,1,1)
    rows = (Locator(0,sha,source.stat().st_size,'chunk-cas-v2:'+sha),)
    manifest = VerifiedManifest(version,rows,manifest_digest(version,rows))
    return manifest,store


def create(catalog,prepared):
    manifest,store = prepared
    return catalog.create_version('document-1',manifest,chunk_store=store,expected_manifest_sha256=manifest.manifest_sha256)


def ack(catalog):
    op = catalog.claim()
    assert op
    return catalog.acknowledge(op['operation_id'],lease_token=op['lease_token'],expected_manifest_sha256=op['manifest_sha256'])


def transition(catalog,document,operation):
    return catalog.transition(document['document_id'],expected_lifecycle_epoch=document['lifecycle_epoch'],expected_content_epoch=document['content_epoch'],expected_index_epoch=document['index_epoch'],operation=operation)


def test_create_archive_restore_tombstone(catalog,prepared):
    pending = create(catalog,prepared)
    assert pending['state']=='pending'
    active = ack(catalog); assert active['state']=='active'
    archiving=transition(catalog,active,'archive'); assert archiving['state']=='archiving'
    archived=ack(catalog); assert archived['state']=='archived'
    restoring=transition(catalog,archived,'restore'); assert restoring['lifecycle_epoch']==3
    restored=ack(catalog); assert restored['state']=='active'
    tombstone=transition(catalog,restored,'tombstone'); assert tombstone['state']=='tombstoned'
    assert ack(catalog)['state']=='tombstoned'
    with pytest.raises(CatalogConflict): transition(catalog,tombstone,'restore')
    with catalog.transaction() as cursor:
        cursor.execute('SELECT count(*) AS n FROM versions'); assert cursor.fetchone()['n']==1
        cursor.execute('SELECT count(*) AS n FROM outbox WHERE status=\'acknowledged\''); assert cursor.fetchone()['n']==4


def test_stale_lease_epoch_and_receipt_are_denied(catalog,prepared):
    pending=create(catalog,prepared)
    op=catalog.claim()
    for token,sha in [(str(uuid.uuid4()),op['manifest_sha256']),(op['lease_token'],'c'*64)]:
        with pytest.raises(CatalogConflict):
            catalog.acknowledge(op['operation_id'],lease_token=token,expected_manifest_sha256=sha)
    transition(catalog,pending,'archive')
    with pytest.raises(CatalogConflict):
        catalog.acknowledge(op['operation_id'],lease_token=op['lease_token'],expected_manifest_sha256=op['manifest_sha256'])
    with pytest.raises(CatalogConflict): transition(catalog,pending,'tombstone')
    assert ack(catalog)['state']=='archived'


def test_atomic_collision_rollback_and_immutable_references(catalog,prepared):
    create(catalog,prepared)
    manifest,store=prepared
    altered=replace(manifest.version,source_sha256='e'*64,document_version_id='version-2')
    changed=replace(manifest,version=altered,manifest_sha256=manifest_digest(altered,manifest.locators))
    with pytest.raises(psycopg2.IntegrityError):
        catalog.create_version('document-1',changed,chunk_store=store,expected_manifest_sha256=changed.manifest_sha256)
    with catalog.transaction() as cursor:
        cursor.execute('SELECT count(*) AS n FROM source_objects'); assert cursor.fetchone()['n']==1
        cursor.execute('SELECT count(*) AS n FROM outbox'); assert cursor.fetchone()['n']==1
    for table in ['versions','chunks','source_objects']:
        with pytest.raises(psycopg2.DatabaseError):
            with catalog.transaction() as cursor:
                cursor.execute(sql.SQL('DELETE FROM {}').format(sql.Identifier(table)))


def test_empty_version_never_active(catalog,prepared):
    manifest,store=prepared
    version=replace(manifest.version,chunk_count=0)
    empty=VerifiedManifest(version,(),manifest_digest(version,()))
    catalog.create_version('empty',empty,chunk_store=store,expected_manifest_sha256=empty.manifest_sha256)
    op=catalog.claim()
    with pytest.raises(CatalogConflict,match='unpublishable'):
        catalog.acknowledge(op['operation_id'],lease_token=op['lease_token'],expected_manifest_sha256=op['manifest_sha256'])


def test_expired_lease_reclaim_and_attempt_limit(catalog,prepared):
    create(catalog,prepared); old=catalog.claim()
    with catalog.transaction() as cursor:
        cursor.execute("UPDATE outbox SET lease_until=clock_timestamp()-interval '1 second' WHERE operation_id=%s",(old['operation_id'],))
    new=catalog.claim(); assert new['lease_token'] != old['lease_token'] and new['attempts']==2
    with pytest.raises(CatalogConflict): catalog.acknowledge(old['operation_id'],lease_token=old['lease_token'],expected_manifest_sha256=old['manifest_sha256'])
    with catalog.transaction() as cursor:
        cursor.execute("UPDATE outbox SET lease_until=clock_timestamp()-interval '1 second',attempts=10 WHERE operation_id=%s",(new['operation_id'],))
    assert catalog.claim() is None


def test_actual_auth_permission_and_rotation_transactions(catalog):
    salt,hashed=password_record('synthetic-password')
    catalog.provision_principal('principal','operator',salt,hashed)
    assert catalog.set_grants('principal',expected_permission_epoch=1,scopes=[SCOPE])==2
    session=GovernedAuthenticationSession(catalog)
    headers=('Basic '+base64.b64encode(b'operator:synthetic-password').decode(),)
    principal=session.authenticate(authorization_values=headers,scope=EvidenceScope(**SCOPE))
    assert principal and session.recheck(principal)
    assert catalog.read_principal('operator')['permission_epoch']==2
    with pytest.raises(CatalogConflict): catalog.set_grants('principal',expected_permission_epoch=1,scopes=[])
    assert catalog.set_grants('principal',expected_permission_epoch=2,scopes=[])==3
    assert not session.recheck(principal)
    catalog.set_grants('principal',expected_permission_epoch=3,scopes=[SCOPE])
    rotated=GovernedAuthenticationSession(catalog)
    principal=rotated.authenticate(authorization_values=headers,scope=EvidenceScope(**SCOPE)); assert principal
    salt,new=password_record('new-password')
    assert catalog.rotate_credentials('principal',expected_credential_epoch=1,salt=salt,password_hash=new)==2
    assert not rotated.recheck(principal)
    assert GovernedAuthenticationSession(catalog).authenticate(authorization_values=headers,scope=EvidenceScope(**SCOPE)) is None
    catalog.set_grants('principal',expected_permission_epoch=4,scopes=[SCOPE],disabled=True)
    assert catalog.read_principal('operator')['disabled']


def authenticate(catalog):
    salt,hashed=password_record('synthetic-password')
    catalog.provision_principal('principal','operator',salt,hashed)
    catalog.set_grants('principal',expected_permission_epoch=1,scopes=[SCOPE])
    session=GovernedAuthenticationSession(catalog)
    headers=('Basic '+base64.b64encode(b'operator:synthetic-password').decode(),)
    principal=session.authenticate(authorization_values=headers,scope=EvidenceScope(**SCOPE))
    assert principal
    return principal,session


def test_authorized_create_rechecks_after_cas_io_and_rolls_back(catalog,prepared):
    principal,session=authenticate(catalog)
    manifest,store=prepared
    class RevokingStore:
        def read(self,**kwargs):
            data=store.read(**kwargs)
            catalog.set_grants('principal',expected_permission_epoch=2,scopes=[])
            return data
    with pytest.raises(CatalogConflict,match='authority_denied'):
        catalog.create_authorized_version('denied',manifest,principal=principal,authentication_session=session,chunk_store=RevokingStore(),expected_manifest_sha256=manifest.manifest_sha256)
    with catalog.transaction() as cursor:
        for table in ('documents','versions','chunks','outbox','source_objects'):
            cursor.execute(sql.SQL('SELECT count(*) AS n FROM {}').format(sql.Identifier(table)))
            assert cursor.fetchone()['n']==0


def test_authorized_lifecycle_denies_stale_or_missing_handle(catalog,prepared):
    principal,session=authenticate(catalog)
    manifest,store=prepared
    doc=catalog.create_authorized_version('document-1',manifest,principal=principal,authentication_session=session,chunk_store=store,expected_manifest_sha256=manifest.manifest_sha256)
    with pytest.raises(CatalogConflict):
        catalog.create_authorized_version('other',manifest,principal=None,authentication_session=session,chunk_store=store,expected_manifest_sha256=manifest.manifest_sha256)
    catalog.set_grants('principal',expected_permission_epoch=2,scopes=[])
    with pytest.raises(CatalogConflict):
        catalog.transition_authorized('document-1',principal=principal,authentication_session=session,operation='archive',expected_lifecycle_epoch=1,expected_content_epoch=1,expected_index_epoch=1)
    with catalog.transaction() as cursor:
        cursor.execute('SELECT state FROM documents'); assert cursor.fetchone()['state']=='pending'


def test_concurrent_lifecycle_only_one_expected_epoch_wins(catalog,prepared):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    active=ack_after_create(catalog,prepared)
    barrier=threading.Barrier(2)
    def worker(operation):
        barrier.wait()
        try:
            return transition(catalog,active,operation)['state']
        except CatalogConflict:
            return 'denied'
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(worker,['archive','tombstone']))
    assert results.count('denied')==1
    with catalog.transaction() as cursor:
        cursor.execute("SELECT count(*) AS n FROM outbox WHERE status IN ('pending','leased')")
        assert cursor.fetchone()['n']==1


def ack_after_create(catalog,prepared):
    create(catalog,prepared)
    return ack(catalog)


def test_failed_sql_does_not_leak_partial_lifecycle_or_outbox(catalog,prepared):
    active=ack_after_create(catalog,prepared)
    original=catalog._enqueue
    def failing(*args):
        original(*args)
        raise RuntimeError('synthetic interruption before commit')
    catalog._enqueue=failing
    with pytest.raises(RuntimeError): transition(catalog,active,'archive')
    with catalog.transaction() as cursor:
        cursor.execute('SELECT state,lifecycle_epoch FROM documents')
        assert tuple(cursor.fetchone().values())==('active',1)
        cursor.execute('SELECT count(*) AS n FROM outbox'); assert cursor.fetchone()['n']==1


def test_install_never_replaces_existing_schema(catalog):
    with pytest.raises(psycopg2.DatabaseError): catalog.install()
    with catalog.transaction() as cursor:
        cursor.execute('SELECT count(*) AS n FROM documents'); assert cursor.fetchone()['n']==0


def test_forged_handle_or_other_catalog_session_denied(catalog,prepared):
    principal,session=authenticate(catalog)
    manifest,store=prepared
    with pytest.raises(CatalogConflict,match='authentication_denied'):
        catalog.create_authorized_version('denied',manifest,principal=replace(principal),authentication_session=session,chunk_store=store,expected_manifest_sha256=manifest.manifest_sha256)
    # A different catalog instance is a different capability even over the same DB.
    other=CatalogWriter(catalog.connect,schema=catalog.schema)
    other_session=GovernedAuthenticationSession(other)
    headers=('Basic '+base64.b64encode(b'operator:synthetic-password').decode(),)
    other_principal=other_session.authenticate(authorization_values=headers,scope=EvidenceScope(**SCOPE))
    assert other_principal
    with pytest.raises(CatalogConflict,match='authentication_denied'):
        catalog.create_authorized_version('denied',manifest,principal=other_principal,authentication_session=other_session,chunk_store=store,expected_manifest_sha256=manifest.manifest_sha256)


def test_relational_version_cannot_point_to_another_document(catalog,prepared):
    create(catalog,prepared)
    manifest,store=prepared
    other_version=replace(manifest.version,document_version_id='other-version')
    other=replace(manifest,version=other_version,manifest_sha256=manifest_digest(other_version,manifest.locators))
    catalog.create_version('other-document',other,chunk_store=store,expected_manifest_sha256=other.manifest_sha256)
    with pytest.raises(psycopg2.IntegrityError):
        with catalog.transaction() as cursor:
            # Constraint is deferred until commit and enforces document ownership.
            cursor.execute("UPDATE documents SET version_id='other-version' WHERE document_id='document-1'")


def test_authority_lock_serializes_revocation_with_create(catalog,prepared):
    import threading
    from concurrent.futures import ThreadPoolExecutor
    principal,session=authenticate(catalog)
    manifest,store=prepared
    locked=threading.Event(); release=threading.Event()
    original=catalog._authority
    def blocking(cursor,handle,scope):
        original(cursor,handle,scope)
        locked.set()
        assert release.wait(3)
    catalog._authority=blocking
    with ThreadPoolExecutor(max_workers=2) as pool:
        writing=pool.submit(catalog.create_authorized_version,'document-1',manifest,principal=principal,authentication_session=session,chunk_store=store,expected_manifest_sha256=manifest.manifest_sha256)
        assert locked.wait(3)
        revoking=pool.submit(catalog.set_grants,'principal',expected_permission_epoch=2,scopes=[])
        assert not revoking.done()
        release.set()
        assert writing.result(timeout=5)['state']=='pending'
        assert revoking.result(timeout=5)==3
    # The write linearized before revoke, and its old handle is now denied.
    assert not session.recheck(principal)


def test_actual_ingestion_originals_chunks_auth_and_pending_outbox(catalog,tmp_path):
    from app.services.governed_ingestion import GovernedIngestionService
    from evaluation.governed_answers.content_addressed_sources import ContentAddressedSourceStore
    from evaluation.governed_answers.versioned_manifests import Version,Locator,manifest_digest
    principal,session=authenticate(catalog)
    source=tmp_path/'original.txt'
    original=b'Exact source original retained.'
    source.write_bytes(original)
    source_root=tmp_path/'source-cas'; source_root.mkdir(mode=0o700)
    chunk_root=tmp_path/'chunk-cas'; chunk_root.mkdir(mode=0o700)
    store=ContentAddressedChunkStore(chunk_root)
    service=GovernedIngestionService(catalog=catalog,source_store=ContentAddressedSourceStore(source_root),chunk_store=store)
    # Cross a chunk boundary; prove both objects/references are preserved.
    text='Queue depth and worker health. '*60
    result=service.ingest(session=session,principal=principal,source_path=source,
        extracted_text=text,extraction_policy_sha256='d'*64,document_id='ingested',version_id='ingested-version')
    assert result['state']=='pending' and result['chunk_count']>1
    assert result['production_enabled'] is False and result['release_authorized'] is False
    sha=hashlib.sha256(original).hexdigest()
    assert source.read_bytes()==original and (source_root/sha).read_bytes()==original
    with catalog.transaction() as cursor:
        cursor.execute("SELECT * FROM documents WHERE document_id='ingested'")
        document=cursor.fetchone(); assert document['state']=='pending'
        cursor.execute("SELECT * FROM outbox WHERE document_id='ingested'")
        op=cursor.fetchone(); assert op['status']=='pending' and op['attempts']==0
        cursor.execute("SELECT binding_json,manifest_sha256 FROM versions WHERE version_id='ingested-version'")
        saved=cursor.fetchone(); binding=saved['binding_json']; binding['scope']=tuple(binding['scope'])
        version=Version(**binding); version.validate()
        cursor.execute("SELECT * FROM chunks WHERE version_id='ingested-version' ORDER BY chunk_index")
        rows=cursor.fetchall()
        locators=tuple(Locator(row['chunk_index'],row['chunk_sha256'],row['byte_length'],row['storage_reference']) for row in rows)
        assert manifest_digest(version,locators)==saved['manifest_sha256']==op['manifest_sha256']
        assert version.source_sha256==sha and version.source_byte_length==len(original)
        assert [row.chunk_index for row in locators]==list(range(result['chunk_count']))
        for locator in locators:
            data=store.read(expected_sha256=locator.chunk_sha256,expected_byte_length=locator.chunk_byte_length)
            assert data.decode() in text


def test_same_current_lease_can_renew_without_reclaim(catalog,prepared):
    create(catalog,prepared)
    original=catalog.claim(lease_seconds=1)
    renewed=catalog.renew_lease(original['operation_id'],lease_token=original['lease_token'],lease_seconds=120)
    assert renewed['lease_token']==original['lease_token']
    assert renewed['attempts']==original['attempts']==1
    assert renewed['lease_until']>original['lease_until']
    assert catalog.acknowledge(renewed['operation_id'],lease_token=renewed['lease_token'],expected_manifest_sha256=renewed['manifest_sha256'])['state']=='active'
    with pytest.raises(CatalogConflict):
        catalog.renew_lease(original['operation_id'],lease_token=original['lease_token'])


def test_renewal_cannot_revive_expired_or_replaced_lease(catalog,prepared):
    create(catalog,prepared)
    expired=catalog.claim()
    with catalog.transaction() as cursor:
        cursor.execute("UPDATE outbox SET lease_until=clock_timestamp()-interval '1 second' WHERE operation_id=%s",(expired['operation_id'],))
    with pytest.raises(CatalogConflict,match='stale_lease_renewal'):
        catalog.renew_lease(expired['operation_id'],lease_token=expired['lease_token'])
    replacement=catalog.claim()
    with pytest.raises(CatalogConflict,match='stale_lease_renewal'):
        catalog.renew_lease(expired['operation_id'],lease_token=expired['lease_token'])
    assert catalog.renew_lease(replacement['operation_id'],lease_token=replacement['lease_token'])['attempts']==2


def test_superseded_claim_cannot_renew_after_archive(catalog,prepared):
    pending=create(catalog,prepared)
    stale=catalog.claim()
    transition(catalog,pending,'archive')
    with pytest.raises(CatalogConflict,match='stale_lease_renewal'):
        catalog.renew_lease(stale['operation_id'],lease_token=stale['lease_token'])
    archive=catalog.claim()
    renewed=catalog.renew_lease(archive['operation_id'],lease_token=archive['lease_token'])
    assert renewed['kind']=='archive'
    assert catalog.acknowledge(renewed['operation_id'],lease_token=renewed['lease_token'],expected_manifest_sha256=renewed['manifest_sha256'])['state']=='archived'


@pytest.mark.parametrize('seconds',[True,0,121,1.5])
def test_lease_renewal_budget_invalid_before_sql(seconds):
    def forbidden(): raise AssertionError('must reject before connection')
    with pytest.raises(ValueError):
        CatalogWriter(forbidden).renew_lease(str(uuid.uuid4()),lease_token=str(uuid.uuid4()),lease_seconds=seconds)


def test_expiry_during_ack_transaction_cannot_activate(catalog,prepared):
    create(catalog,prepared)
    claim=catalog.claim(lease_seconds=1)
    # Force a real server wait between initial lease check and final update.
    with catalog.transaction() as cursor:
        cursor.execute("CREATE FUNCTION slow_document_activation() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN IF NEW.state='active' THEN PERFORM pg_sleep(1.1); END IF; RETURN NEW; END $$")
        cursor.execute('CREATE TRIGGER slow_ack BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION slow_document_activation()')
    with pytest.raises(CatalogConflict,match='stale_acknowledgement'):
        catalog.acknowledge(claim['operation_id'],lease_token=claim['lease_token'],expected_manifest_sha256=claim['manifest_sha256'])
    with catalog.transaction() as cursor:
        cursor.execute("SELECT state FROM documents WHERE document_id='document-1'")
        assert cursor.fetchone()['state']=='pending'
