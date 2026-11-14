"""Bibliographic acceptance must never remove extraction quarantine."""
import hashlib
from pathlib import Path
import pytest
from app.services.governed_source_identity import (
    approved_smith_identity, OWNER_ACCEPTANCE_SHA256, SMITH_SHA256,
    prepare_cook_source,
)
from app.services.governed_legacy_migration import MANDATORY_QUARANTINES
ACCEPTANCE = Path(__file__).resolve().parents[2] / 'docs/governance/sprint21-owner-packet.accepted-20261113.json'


def arguments():
    return dict(acceptance=ACCEPTANCE, acceptance_sha256=OWNER_ACCEPTANCE_SHA256,
        original_filename='preserved-original.pdf', original_source_sha256=SMITH_SHA256)


def test_exact_accepted_identity_preserves_locator_and_quarantine():
    result = approved_smith_identity(**arguments())
    assert result['canonical_title'] == 'A Manual of Equity Jurisprudence'
    assert result['original_filename'] == 'preserved-original.pdf'
    assert result['source_sha256'] in MANDATORY_QUARANTINES
    assert result['promotes_to_search'] is False
    assert result['changes_source_bytes'] is False


def test_rewritten_approval_even_with_matching_caller_digest_denied(tmp_path):
    path = tmp_path / 'approval.json'
    path.write_text(ACCEPTANCE.read_text().replace('"disposition": "accepted"', '"disposition": "deferred"'))
    args = arguments()
    args.update(acceptance=path, acceptance_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match='acceptance_digest_mismatch'):
        approved_smith_identity(**args)


@pytest.mark.parametrize('field,value', [('original_source_sha256', '0'*64),
    ('original_filename','../renamed.pdf'), ('original_filename','')])
def test_source_or_locator_rebinding_denied(field,value):
    args=arguments();args[field]=value
    with pytest.raises(ValueError):approved_smith_identity(**args)


def test_cook_wrong_original_never_calls_extractor(tmp_path):
    path = tmp_path / 'cook.pdf'; path.write_bytes(b'wrong original')
    def extractor(*args):raise AssertionError('extractor must not run')
    with pytest.raises(ValueError, match='cook_original_required'):
        prepare_cook_source(path,extractor=extractor)


def test_overlay_receipts_are_immutable_in_postgres():
    import os
    import uuid
    import psycopg2
    from psycopg2 import sql
    from app.services.governed_catalog import CatalogWriter
    from app.services.governed_source_identity import SourceIdentityOverlay
    dsn=os.getenv('SENTINEL_ISOLATED_POSTGRES_DSN')
    if not dsn:pytest.skip('dedicated PostgreSQL required')
    schema='test_identity_'+uuid.uuid4().hex
    catalog=CatalogWriter(lambda:psycopg2.connect(dsn),schema=schema)
    catalog.install()
    try:
        overlay=SourceIdentityOverlay(catalog);overlay.install()
        first=overlay.record_smith(**arguments())
        assert first==overlay.record_smith(**arguments())
        conflict=arguments();conflict['original_filename']='other.pdf'
        with pytest.raises(ValueError,match='source_identity_conflict'):
            overlay.record_smith(**conflict)
        for statement in ('UPDATE source_identity_receipts SET receipt=receipt',
                          'DELETE FROM source_identity_receipts',
                          'TRUNCATE source_identity_receipts'):
            with pytest.raises(psycopg2.Error,match='immutable'):
                with catalog.transaction() as cursor:cursor.execute(statement)
    finally:
        with psycopg2.connect(dsn) as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


@pytest.fixture
def smith_inventory():
    from app.services.governed_source_identity import SMITH_LEGACY_ID
    from evaluation.governed_answers.legacy_extraction_checkpoint import create_checkpoint
    scope=dict(organization_id='default',collection='law',module='law',topic='general')
    hashes=[hashlib.sha256(str(i).encode()).hexdigest() for i in range(1130)]
    row=dict(id=SMITH_LEGACY_ID,file_hash=SMITH_SHA256,status='indexed',embedding_model='legacy',chunk_count=1130,**scope)
    points=[dict(document_id=SMITH_LEGACY_ID,file_hash=SMITH_SHA256,status='indexed',embedding_model='legacy',chunk_index=i,point_id=str(i),chunk_sha256=h,chunk_byte_length=len(str(i)),**scope) for i,h in enumerate(hashes)]
    checkpoint=create_checkpoint(source_sha256=SMITH_SHA256,byte_length=14737587,policy_digest='a'*64,extraction_chunk_hashes=hashes)
    return dict(inventory=dict(capture=dict(catalog_complete=True,points_complete=True),catalog=[row],points=points),checkpoint=checkpoint,source_path='/private/original.pdf',expected_policy_sha256='a'*64)


def test_separate_smith_admission_keeps_every_ordered_hash(smith_inventory):
    from app.services.governed_source_identity import build_smith_admission_entry
    entry=build_smith_admission_entry(**smith_inventory)
    assert len(entry['points'])==1130
    assert [p['chunk_sha256'] for p in entry['points']]==smith_inventory['checkpoint']['extraction_chunk_hashes']
    assert SMITH_SHA256 in MANDATORY_QUARANTINES


@pytest.mark.parametrize('tamper',['hash','scope','order','count','policy','capture'])
def test_smith_remediation_denies_current_drift(smith_inventory,tamper):
    from app.services.governed_source_identity import build_smith_admission_entry
    row=smith_inventory['inventory']['catalog'][0]
    if tamper=='hash':row['file_hash']='f'*64
    if tamper=='scope':row['topic']='other'
    if tamper=='order':smith_inventory['inventory']['points'][0]['chunk_index']=1
    if tamper=='count':smith_inventory['inventory']['points'].pop()
    if tamper=='policy':smith_inventory['expected_policy_sha256']='b'*64
    if tamper=='capture':smith_inventory['inventory']['capture']['points_complete']=False
    with pytest.raises(ValueError):build_smith_admission_entry(**smith_inventory)


def test_reviewed_admission_real_sql_and_transactional_locator_check(smith_inventory,monkeypatch):
    """Synthetic manifest seam; real authority, SQL locks and outbox writes."""
    import os,uuid,base64,psycopg2
    from psycopg2 import sql
    from app.services.governed_catalog import CatalogWriter
    from app.services.governed_authentication import GovernedAuthenticationSession,password_record
    from app.services.governed_source_identity import SourceIdentityOverlay,admit_smith_after_identity
    from app.services.governed_legacy_migration import GovernedLegacyMigrator,CATALOG_FIELDS
    from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
    from evaluation.governed_answers.versioned_manifests import Version,Locator,VerifiedManifest,manifest_digest
    dsn=os.getenv('SENTINEL_ISOLATED_POSTGRES_DSN')
    if not dsn:pytest.skip('dedicated PostgreSQL required')
    schema='test_admit_'+uuid.uuid4().hex;legacy='test_legacy_'+uuid.uuid4().hex
    writer=CatalogWriter(lambda:psycopg2.connect(dsn),schema=schema);writer.install()
    try:
        overlay=SourceIdentityOverlay(writer);overlay.install();receipt=overlay.record_smith(**arguments())
        row=smith_inventory['inventory']['catalog'][0];scope={k:row[k] for k in ('organization_id','collection','module','topic')}
        with writer.transaction() as cursor:
            cursor.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(legacy)))
            cursor.execute(sql.SQL('CREATE TABLE {}.documents(id TEXT PRIMARY KEY,file_hash TEXT,organization_id TEXT,collection TEXT,module TEXT,topic TEXT,status TEXT,embedding_model TEXT,chunk_count INTEGER,filename TEXT)').format(sql.Identifier(legacy)))
            fields=(*CATALOG_FIELDS,'filename')
            cursor.execute(sql.SQL('INSERT INTO {}.documents ({}) VALUES ({})').format(sql.Identifier(legacy),sql.SQL(',').join(map(sql.Identifier,fields)),sql.SQL(',').join(sql.Placeholder() for _ in fields)),[row[k] for k in CATALOG_FIELDS]+['preserved-original.pdf'])
        salt,password=password_record('synthetic-password');writer.provision_principal('p','operator',salt,password);writer.set_grants('p',expected_permission_epoch=1,scopes=[scope])
        def auth(scope):
            session=GovernedAuthenticationSession(writer)
            return session,session.authenticate(authorization_values=('Basic '+base64.b64encode(b'operator:synthetic-password').decode(),),scope=EvidenceScope(**scope))
        def objects(self,entry):
            version=Version(entry['governed_version_id'],tuple(scope[k] for k in ('organization_id','collection','module','topic')),SMITH_SHA256,14737587,'a'*64,1130,1,1,1)
            locators=tuple(Locator(p['chunk_index'],p['chunk_sha256'],p['chunk_byte_length'],'chunk-cas-v2:'+p['chunk_sha256']) for p in entry['points'])
            return VerifiedManifest(version,locators,manifest_digest(version,locators))
        monkeypatch.setattr(GovernedLegacyMigrator,'_objects',objects)
        migrator=GovernedLegacyMigrator(catalog=writer,source_store=None,chunk_store=None,read_points=None,authenticate_scope=auth,legacy_schema=legacy);migrator.initialize()
        args=dict(migrator=migrator,expected_receipt_sha256=receipt['receipt_sha256'],**smith_inventory)
        assert admit_smith_after_identity(**args)['status']=='migrated'
        assert admit_smith_after_identity(**args)['status']=='verified_existing'
        with writer.transaction() as cursor:
            from app.governed_workspace_application import _document_page
            from app.services.governed_catalog import scope_key
            rows=_document_page(cursor,scope_key(scope),'',100)
            assert len(rows)==1
            assert rows[0]['display_identity']['canonical_title']=='A Manual of Equity Jurisprudence'
            assert rows[0]['identity_receipt_sha256']==receipt['receipt_sha256']
            assert 'original_filename' not in rows[0]['display_identity']
            assert _document_page(cursor,'0'*64,'',100)==[]
            cursor.execute('SELECT count(*) AS n FROM chunks');assert cursor.fetchone()['n']==1130
            cursor.execute(sql.SQL("UPDATE {}.documents SET filename='changed.pdf'").format(sql.Identifier(legacy)))
        with pytest.raises(ValueError,match='smith_original_locator_changed'):admit_smith_after_identity(**args)
    finally:
        with psycopg2.connect(dsn) as connection:
            with connection.cursor() as cursor:
                for value in (schema,legacy):cursor.execute(sql.SQL('DROP SCHEMA IF EXISTS {} CASCADE').format(sql.Identifier(value)))
