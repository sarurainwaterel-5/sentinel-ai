"""Additive, immutable bibliographic receipts; no source or search promotion.

Installation is explicit in the already installed governed schema. Records bind
owner-approved identity to exact bytes and the preserved legacy locator. This
service neither changes legacy filenames nor removes migration quarantines.
"""
import hashlib
import json
from pathlib import Path

from psycopg2.extras import Json
from app.services.governed_catalog import canonical, name

SMITH_SHA256 = 'f2dbc04c342058d33b29948f31aea64f3752d974325e26610dff0f158e7140dc'
SMITH_LEGACY_ID = 'f29a29c6-0abb-45a4-b1d3-ecce65fb95ba'
COOK_SHA256 = '57e76c5de835a1deb0f6cf715f99adbd910133ea05ad61b4bd821c41537dacff'
OWNER_ACCEPTANCE_SHA256 = '81838ee3378231e054420ea195797f39e657ed98697c516b016b86f8f6d8064a'
SOURCE_PLAN_SHA256 = '29b29036b7c662eef0e3e5dd4fab2235c782050509106060e23c07108807576e'


def approved_smith_identity(*, acceptance, acceptance_sha256, original_filename, original_source_sha256):
    """Validate the exact saved decision, producing no authorization session."""
    encoded = Path(acceptance).read_bytes()
    if acceptance_sha256 != OWNER_ACCEPTANCE_SHA256 or hashlib.sha256(encoded).hexdigest() != acceptance_sha256:
        raise ValueError('acceptance_digest_mismatch')
    record = json.loads(encoded)
    decisions = [item for item in record.get('decisions', []) if item.get('group') == 'smith_identity']
    if (record.get('version') != 'sprint21-owner-packet-acceptance-v1'
        or record.get('artifact_sha256', {}).get('source-correction-plan.proposed.json') != SOURCE_PLAN_SHA256
        or len(decisions) != 1 or decisions[0].get('disposition') != 'accepted'):
        raise ValueError('exact_smith_acceptance_required')
    if original_source_sha256 != SMITH_SHA256:
        raise ValueError('smith_source_mismatch')
    name(original_filename)
    if Path(original_filename).name != original_filename:
        raise ValueError('original_filename_only')
    return dict(version='sentinel-source-identity-v1', source_sha256=SMITH_SHA256,
        legacy_document_id=SMITH_LEGACY_ID, original_filename=original_filename,
        canonical_title='A Manual of Equity Jurisprudence', author='Josiah W. Smith',
        edition='Fifteenth edition by Sydney E. Williams', year=1900,
        acceptance_sha256=acceptance_sha256, source_plan_sha256=SOURCE_PLAN_SHA256,
        promotes_to_search=False, changes_source_bytes=False)


class SourceIdentityOverlay:
    def __init__(self, catalog):
        self.catalog = catalog

    def install(self):
        """New table only; existing table fails closed rather than being replaced."""
        with self.catalog.transaction() as cursor:
            cursor.execute('''CREATE TABLE source_identity_receipts (
                source_sha256 TEXT PRIMARY KEY CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
                receipt_sha256 TEXT NOT NULL UNIQUE CHECK (receipt_sha256 ~ '^[0-9a-f]{64}$'),
                receipt JSONB NOT NULL,
                recorded_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp())''')
            cursor.execute('''CREATE FUNCTION reject_source_identity_mutation() RETURNS trigger
                LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'source identity receipts are immutable'; END $$''')
            cursor.execute('''CREATE TRIGGER source_identity_immutable BEFORE UPDATE OR DELETE
                ON source_identity_receipts FOR EACH ROW EXECUTE FUNCTION reject_source_identity_mutation()''')
            cursor.execute('''CREATE TRIGGER source_identity_no_truncate BEFORE TRUNCATE
                ON source_identity_receipts FOR EACH STATEMENT EXECUTE FUNCTION reject_source_identity_mutation()''')

    def record_smith(self, *, acceptance, acceptance_sha256, original_filename, original_source_sha256):
        value = approved_smith_identity(acceptance=acceptance, acceptance_sha256=acceptance_sha256,
            original_filename=original_filename, original_source_sha256=original_source_sha256)
        receipt_sha256 = hashlib.sha256(canonical(value).encode()).hexdigest()
        with self.catalog.transaction() as cursor:
            cursor.execute('INSERT INTO source_identity_receipts(source_sha256,receipt_sha256,receipt) '
                'VALUES (%s,%s,%s) ON CONFLICT DO NOTHING', (SMITH_SHA256, receipt_sha256, Json(value)))
            cursor.execute('SELECT receipt_sha256,receipt FROM source_identity_receipts WHERE source_sha256=%s', (SMITH_SHA256,))
            saved = cursor.fetchone()
            if not saved or saved['receipt_sha256'] != receipt_sha256 or saved['receipt'] != value:
                raise ValueError('source_identity_conflict')
        return dict(source_sha256=SMITH_SHA256, receipt_sha256=receipt_sha256,
                    source_quarantine_unchanged=True, production_enabled=False)


def prepare_cook_source(source_path, *, extractor):
    """Hash-bound new intake preparation; text is never a replacement for Smith.

    Caller must supply the installed server extractor, pin its policy, and use
    normal authenticated ingestion. This preparation does not write SQL or CAS.
    """
    path = Path(source_path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size != 32840724:
        raise ValueError('cook_original_required')
    before = path.stat()
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1024 * 1024):
            hasher.update(block)
    if hasher.hexdigest() != COOK_SHA256:
        raise ValueError('cook_source_mismatch')
    text = extractor(path, 'suretyship-stearns-cook-1922-archive.pdf')
    after = path.stat()
    if path.is_symlink() or any(getattr(before, key) != getattr(after, key) for key in ('st_dev','st_ino','st_size','st_mtime_ns','st_ctime_ns')):
        raise ValueError('cook_source_changed')
    if not isinstance(text, str) or not text.strip() or len(text.encode('utf-8')) > 64 * 1024**2:
        raise ValueError('cook_extraction_requires_review')
    return text, dict(source_sha256=COOK_SHA256, byte_length=32840724,
        canonical_title='The Law of Suretyship', author='Arthur Adelbert Stearns',
        edition='Third edition by Wells M. Cook', year=1922,
        separate_new_document_required=True, reuse_smith_vectors=False,
        extracted_text_sha256=hashlib.sha256(text.encode('utf-8')).hexdigest())


CHART_SHA256 = '43a28f3bd51c303dd69a2e1c9aa19c79638d0a0d18d102d6cc13c291467427c4'


def build_smith_admission_entry(*, inventory, checkpoint, source_path, expected_policy_sha256):
    """Separate single-source remediation, never relax the bulk quarantine."""
    import uuid
    from app.services.governed_legacy_migration import (
        CATALOG_FIELDS, POINT_FIELDS, SCOPE_FIELDS, PLAN_NAMESPACE, sha, MigrationDenied,
    )
    from app.services.governed_catalog import exact_scope, scope_key
    from evaluation.governed_answers.legacy_extraction_checkpoint import reusable_chunk_hashes
    from evaluation.governed_answers.versioned_manifests import digest, integer
    digest(expected_policy_sha256)
    if inventory.get('capture',{}).get('catalog_complete') is not True or inventory.get('capture',{}).get('points_complete') is not True:
        raise MigrationDenied('complete_inventory_required')
    rows=[row for row in inventory['catalog'] if row.get('id')==SMITH_LEGACY_ID]
    if len(rows)!=1:raise MigrationDenied('exact_smith_catalog_required')
    row=rows[0]
    if row.get('file_hash')!=SMITH_SHA256 or row.get('chunk_count')!=1130 or row.get('status') not in ('indexed','archived'):
        raise MigrationDenied('smith_legacy_identity_changed')
    if checkpoint.get('source_sha256')!=SMITH_SHA256 or checkpoint.get('byte_length')!=14737587 or checkpoint.get('policy_digest')!=expected_policy_sha256:
        raise MigrationDenied('smith_checkpoint_identity_mismatch')
    hashes=reusable_chunk_hashes(checkpoint,source_sha256=SMITH_SHA256,byte_length=14737587,policy_digest=expected_policy_sha256)
    if hashes is None or len(hashes)!=1130:raise MigrationDenied('complete_smith_checkpoint_required')
    scope=exact_scope({key:row[key] for key in SCOPE_FIELDS})
    if scope!=dict(organization_id='default',collection='law',module='law',topic='general'):
        raise MigrationDenied('smith_scope_changed')
    points=sorted([point for point in inventory['points'] if point.get('document_id')==SMITH_LEGACY_ID],key=lambda p:p['chunk_index'])
    if len(points)!=1130 or len({str(p['point_id']) for p in points})!=1130:
        raise MigrationDenied('smith_point_count_or_identity_mismatch')
    normalized=[]
    for index,(point,chunk_hash) in enumerate(zip(points,hashes)):
        integer(point['chunk_index'],0,1129);integer(point['chunk_byte_length'],1,65536)
        if point['chunk_index']!=index or point['chunk_sha256']!=chunk_hash:
            raise MigrationDenied('smith_checkpoint_index_mismatch')
        for key in POINT_FIELDS:
            if key!='chunk_index' and point.get(key)!=(SMITH_LEGACY_ID if key=='document_id' else row.get(key)):
                raise MigrationDenied('smith_point_metadata_mismatch')
        normalized.append({key:point[key] for key in (*POINT_FIELDS,'point_id','chunk_sha256','chunk_byte_length')})
    if not Path(source_path).is_absolute():raise MigrationDenied('absolute_source_path_required')
    governed_id=str(uuid.uuid5(PLAN_NAMESPACE,scope_key(scope)+':'+SMITH_LEGACY_ID))
    version_id=str(uuid.uuid5(PLAN_NAMESPACE,governed_id+':'+SMITH_SHA256+':'+expected_policy_sha256+':'+sha(hashes)))
    entry=dict(legacy_document_id=SMITH_LEGACY_ID,governed_document_id=governed_id,
        governed_version_id=version_id,scope=scope,source_path=str(source_path),
        legacy_binding={key:row[key] for key in CATALOG_FIELDS},checkpoint=checkpoint,points=normalized)
    entry['entry_sha256']=sha(entry)
    return entry


def admit_smith_after_identity(*, migrator, inventory, checkpoint, source_path,
                                expected_policy_sha256, expected_receipt_sha256):
    """Exact current receipt+legacy check, then normal authenticated atomic copy."""
    from psycopg2 import sql
    from app.services.governed_legacy_migration import sha, MigrationDenied
    from evaluation.governed_answers.versioned_manifests import digest
    digest(expected_receipt_sha256)
    entry=build_smith_admission_entry(inventory=inventory,checkpoint=checkpoint,
        source_path=source_path,expected_policy_sha256=expected_policy_sha256)
    with migrator.catalog.transaction() as cursor:
        cursor.execute('SELECT receipt_sha256,receipt FROM source_identity_receipts WHERE source_sha256=%s',(SMITH_SHA256,))
        row=cursor.fetchone()
        if row is None or row['receipt_sha256']!=expected_receipt_sha256 or sha(row['receipt'])!=expected_receipt_sha256:
            raise MigrationDenied('reviewed_identity_receipt_required')
        receipt=row['receipt']
        expected=approved_smith_identity(acceptance=Path(__file__).resolve().parents[3]/'docs/governance/sprint21-owner-packet.accepted-20261113.json',
            acceptance_sha256=OWNER_ACCEPTANCE_SHA256,original_filename=receipt.get('original_filename'),original_source_sha256=SMITH_SHA256)
        if receipt!=expected:raise MigrationDenied('smith_reviewed_identity_mismatch')
        cursor.execute(sql.SQL('SELECT filename,file_hash FROM {}.documents WHERE id=%s FOR UPDATE').format(sql.Identifier(migrator.legacy_schema)),(SMITH_LEGACY_ID,))
        original=cursor.fetchone()
        if original is None or original['filename']!=receipt['original_filename'] or original['file_hash']!=SMITH_SHA256:
            raise MigrationDenied('smith_original_locator_changed')
    # Receipt is immutable. The migrator rechecks all bytes, point hashes, current
    # locked catalog identity, scoped authentication and atomic outbox itself.
    admission_sha256=sha(dict(version='sentinel-smith-remediation-admission-v1',
        identity_receipt_sha256=expected_receipt_sha256,entry_sha256=entry['entry_sha256']))
    from app.services.governed_legacy_migration import GovernedLegacyMigrator
    class ReviewedSmithMigrator(GovernedLegacyMigrator):
        def _legacy_locked(self, cursor, selected):
            super()._legacy_locked(cursor, selected)
            cursor.execute('SELECT receipt_sha256,receipt FROM source_identity_receipts WHERE source_sha256=%s', (SMITH_SHA256,))
            current=cursor.fetchone()
            if current is None or current['receipt_sha256']!=expected_receipt_sha256 or current['receipt']!=receipt:
                raise MigrationDenied('smith_identity_receipt_changed')
            cursor.execute(sql.SQL('SELECT filename FROM {}.documents WHERE id=%s FOR UPDATE').format(sql.Identifier(self.legacy_schema)),(SMITH_LEGACY_ID,))
            if cursor.fetchone()['filename']!=receipt['original_filename']:
                raise MigrationDenied('smith_original_locator_changed')
    guarded=ReviewedSmithMigrator(catalog=migrator.catalog,source_store=migrator.source_store,
        chunk_store=migrator.chunk_store,read_points=migrator.read_points,
        authenticate_scope=migrator.authenticate_scope,legacy_schema=migrator.legacy_schema)
    return guarded._migrate_entry(entry,expected_plan_sha256=admission_sha256)


def record_chart_held(*, overlay, original_path, label_text_path, original_filename):
    """Preserve exact PNG+label derivative identity without searchable promotion."""
    original=Path(original_path);labels=Path(label_text_path)
    if original.is_symlink() or original.stat().st_size!=116774 or hashlib.sha256(original.read_bytes()).hexdigest()!=CHART_SHA256:
        raise ValueError('exact_chart_original_required')
    text=labels.read_text(encoding='utf-8')
    if len(text)!=68 or hashlib.sha256(labels.read_bytes()).hexdigest()!='3caabaed0fc1a704199fe0e06a02382bc7add9c6fbd4ea6a8afe985517d49373':raise ValueError('exact_label_derivative_required')
    name(original_filename)
    receipt=dict(version='sentinel-chart-labels-held-v1',source_sha256=CHART_SHA256,
        original_filename=original_filename,derivative_sha256=hashlib.sha256(labels.read_bytes()).hexdigest(),
        label_characters=68,searchable=False,label_only=True,geometry_verified=False,
        numerical_series_verified=False,market_claims_verified=False,
        acceptance_sha256=OWNER_ACCEPTANCE_SHA256,requires_reviewed_derivative_for_search=True)
    receipt_sha256=hashlib.sha256(canonical(receipt).encode()).hexdigest()
    with overlay.catalog.transaction() as cursor:
        cursor.execute('INSERT INTO source_identity_receipts(source_sha256,receipt_sha256,receipt) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING',
            (CHART_SHA256,receipt_sha256,Json(receipt)))
        cursor.execute('SELECT receipt_sha256,receipt FROM source_identity_receipts WHERE source_sha256=%s',(CHART_SHA256,))
        saved=cursor.fetchone()
        if saved is None or saved['receipt_sha256']!=receipt_sha256 or saved['receipt']!=receipt:raise ValueError('chart_identity_conflict')
    return dict(source_sha256=CHART_SHA256,receipt_sha256=receipt_sha256,searchable=False)
