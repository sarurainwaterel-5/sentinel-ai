"""Explicit approved legacy-copy migration; no extraction, embeddings or deletion.

A pinned plan binds reviewed scopes, original source identities, complete saved
extraction checkpoints and exact retained point metadata. Existing text is copied
only after matching every ordered checkpoint hash. SQL records mapping and full
lifecycle intent atomically, allowing recovery after a lost response without
creating duplicate documents or briefly activating archived sources.
"""
from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import tempfile
import uuid

from psycopg2 import sql
from psycopg2.extras import Json, execute_values

from app.services.governed_authentication import GovernedAuthenticationSession
from app.services.governed_catalog import CatalogConflict, canonical, exact_scope, name, scope_key
from evaluation.governed_answers.legacy_extraction_checkpoint import reusable_chunk_hashes
from evaluation.governed_answers.versioned_manifests import (
    Version, Locator, VerifiedManifest, manifest_digest, digest, integer,
)

PLAN_NAMESPACE = uuid.UUID('522b92f6-45e8-48f9-b51c-ad3b0477cfbb')
POINT_FIELDS = ('document_id','file_hash','organization_id','collection','module','topic','status','embedding_model','chunk_index')
CATALOG_FIELDS = ('id','file_hash','organization_id','collection','module','topic','status','embedding_model','chunk_count')
SCOPE_FIELDS = ('organization_id','collection','module','topic')
# Known source identity/title and unreviewed image-only extraction quarantines.
MANDATORY_QUARANTINES = frozenset({
    'f2dbc04c342058d33b29948f31aea64f3752d974325e26610dff0f158e7140dc',
    'fc6e847c46494d2f75d934e878291d9706ef01c5d9c1d10d3686d421ce86604f',
})
MAX_PLAN_BYTES = 128 * 1024**2
MAX_DOCUMENTS = 1000


class MigrationDenied(ValueError):
    pass


def sha(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def plan_digest(plan):
    return sha({key:value for key,value in plan.items() if key != 'plan_sha256'})


def build_migration_plan(*, inventory, checkpoints, allowed_policy_digests,
                         source_paths, approved_scopes, quarantined_source_hashes=()):
    """Pure plan creation; explicit reviewed scopes are never inferred as grants.

    Callers must review/pin the resulting plan before execution. Inventory and
    checkpoints contain hashes/metadata, not authenticated approval or source text.
    Exclusions are explicit and preserved in the plan rather than silently lost.
    """
    if type(inventory) is not dict or inventory.get('capture',{}).get('catalog_complete') is not True or inventory.get('capture',{}).get('points_complete') is not True:
        raise MigrationDenied('complete_inventory_required')
    catalog = inventory['catalog']; points = inventory['points']
    if type(catalog) is not list or not 0 < len(catalog) <= MAX_DOCUMENTS or type(points) is not list:
        raise MigrationDenied('inventory_budget')
    scopes = [exact_scope(value) for value in approved_scopes]
    scope_keys = {scope_key(value) for value in scopes}
    if len(scopes) != len(scope_keys) or not scopes or len(scopes) > 100:
        raise MigrationDenied('explicit_unique_scopes_required')
    policies = set(allowed_policy_digests)
    for policy in policies: digest(policy)
    quarantines = set(quarantined_source_hashes) | MANDATORY_QUARANTINES
    for value in quarantines: digest(value)
    complete = {}
    for record in checkpoints:
        if type(record) is not dict or record.get('policy_digest') not in policies:
            raise MigrationDenied('unapproved_checkpoint_policy')
        binding = {key:record.get(key) for key in ('source_sha256','byte_length','policy_digest')}
        hashes = reusable_chunk_hashes(record,**binding)
        if hashes is None: raise MigrationDenied('invalid_checkpoint')
        source = record['source_sha256']
        if source in complete and complete[source] != record:
            # Different exact policies must be selected explicitly by the planner.
            raise MigrationDenied('ambiguous_checkpoint')
        complete[source] = record
    by_document = {}
    ids = set()
    for point in points:
        by_document.setdefault(point.get('document_id'),[]).append(point)
    entries = []; excluded = []
    for row in catalog:
        document_id = name(row['id'])
        if document_id in ids: raise MigrationDenied('duplicate_legacy_identity')
        ids.add(document_id)
        source = row['file_hash']; digest(source)
        scope = exact_scope({key:row[key] for key in SCOPE_FIELDS})
        reason = None
        record = complete.get(source)
        if source in quarantines: reason = 'source_quarantined'
        elif row['status'] not in ('indexed','archived'): reason = 'unsupported_legacy_state'
        elif scope_key(scope) not in scope_keys: reason = 'scope_not_reviewed'
        elif record is None: reason = 'no_complete_checkpoint'
        elif source not in source_paths: reason = 'source_path_unavailable'
        if reason:
            excluded.append(dict(legacy_document_id=document_id,source_sha256=source,reason=reason));continue
        selected = sorted(by_document.get(document_id,[]),key=lambda item:item['chunk_index'])
        expected = record['extraction_chunk_hashes']
        integer(row['chunk_count'],1,100000)
        if len(selected) != row['chunk_count'] or len(selected) != len(expected):
            excluded.append(dict(legacy_document_id=document_id,source_sha256=source,reason='checkpoint_index_count_mismatch'));continue
        normalized = []
        mismatch = False
        for index,(point,expected_hash) in enumerate(zip(selected,expected)):
            if type(point.get('chunk_index')) is not int or point['chunk_index'] != index or point.get('chunk_sha256') != expected_hash:
                mismatch = True;break
            for key in POINT_FIELDS:
                wanted = document_id if key == 'document_id' else row.get(key)
                if key != 'chunk_index' and point.get(key) != wanted: mismatch = True
            integer(point['chunk_byte_length'],1,65536)
            normalized.append({key:point[key] for key in (*POINT_FIELDS,'point_id','chunk_sha256','chunk_byte_length')})
        if mismatch or len({str(point['point_id']) for point in selected}) != len(selected):
            excluded.append(dict(legacy_document_id=document_id,source_sha256=source,reason='checkpoint_index_identity_mismatch'));continue
        path = Path(source_paths[source])
        if not path.is_absolute(): raise MigrationDenied('absolute_source_path_required')
        governed_id = str(uuid.uuid5(PLAN_NAMESPACE,scope_key(scope)+':'+document_id))
        version_id = str(uuid.uuid5(PLAN_NAMESPACE,governed_id+':'+source+':'+record['policy_digest']+':'+sha(expected)))
        entry = dict(legacy_document_id=document_id,governed_document_id=governed_id,
            governed_version_id=version_id,scope=scope,source_path=str(path),
            legacy_binding={key:row[key] for key in CATALOG_FIELDS},checkpoint=record,points=normalized)
        entry['entry_sha256'] = sha(entry)
        entries.append(entry)
    plan = dict(schema_version=1,namespace=str(PLAN_NAMESPACE),inventory_sha256=sha(inventory),
        approved_scopes=sorted(scopes,key=scope_key),entries=sorted(entries,key=lambda item:item['governed_document_id']),
        excluded=sorted(excluded,key=lambda item:item['legacy_document_id']))
    plan['plan_sha256'] = plan_digest(plan)
    validate_plan(plan,expected_plan_sha256=plan['plan_sha256'])
    return plan


def validate_plan(plan, *, expected_plan_sha256):
    digest(expected_plan_sha256)
    if (type(plan) is not dict or type(plan.get('schema_version')) is not int or plan['schema_version'] != 1
            or plan.get('namespace') != str(PLAN_NAMESPACE) or plan.get('plan_sha256') != expected_plan_sha256
            or plan_digest(plan) != expected_plan_sha256):
        raise MigrationDenied('plan_digest_mismatch')
    if len(canonical(plan).encode()) > MAX_PLAN_BYTES or type(plan.get('entries')) is not list or len(plan['entries']) > MAX_DOCUMENTS:
        raise MigrationDenied('plan_budget')
    approved = {scope_key(scope) for scope in plan['approved_scopes']}
    seen = set()
    for entry in plan['entries']:
        if (type(entry) is not dict or sha({k:v for k,v in entry.items() if k != 'entry_sha256'}) != entry.get('entry_sha256')
                or entry['checkpoint']['source_sha256'] in MANDATORY_QUARANTINES
                or scope_key(entry['scope']) not in approved):
            raise MigrationDenied('invalid_plan_entry')
        document_id = entry['governed_document_id']
        if document_id in seen: raise MigrationDenied('duplicate_governed_identity')
        seen.add(document_id)
        legacy = entry['legacy_binding']; checkpoint = entry['checkpoint']
        expected_doc = str(uuid.uuid5(PLAN_NAMESPACE,scope_key(entry['scope'])+':'+entry['legacy_document_id']))
        expected_version = str(uuid.uuid5(PLAN_NAMESPACE,expected_doc+':'+checkpoint['source_sha256']+':'+checkpoint['policy_digest']+':'+sha(checkpoint['extraction_chunk_hashes'])))
        if document_id != expected_doc or entry['governed_version_id'] != expected_version or legacy['id'] != entry['legacy_document_id']:
            raise MigrationDenied('deterministic_identity_mismatch')
        if legacy['status'] not in ('indexed','archived') or exact_scope({k:legacy[k] for k in SCOPE_FIELDS}) != exact_scope(entry['scope']):
            raise MigrationDenied('legacy_binding_mismatch')
        hashes = reusable_chunk_hashes(checkpoint,**{k:checkpoint[k] for k in ('source_sha256','byte_length','policy_digest')})
        if hashes is None or legacy['file_hash'] != checkpoint['source_sha256'] or len(hashes) != legacy['chunk_count'] or len(entry['points']) != len(hashes):
            raise MigrationDenied('checkpoint_binding_mismatch')
        for index,(point,expected_hash) in enumerate(zip(entry['points'],hashes)):
            integer(point['chunk_index'],0,99999);integer(point['chunk_byte_length'],1,65536)
            if point['chunk_index'] != index or point['chunk_sha256'] != expected_hash:
                raise MigrationDenied('checkpoint_chunk_mismatch')
            for key in POINT_FIELDS:
                if key != 'chunk_index' and point[key] != (legacy['id'] if key == 'document_id' else legacy[key]):
                    raise MigrationDenied('point_metadata_mismatch')
        if len({str(point['point_id']) for point in entry['points']}) != len(hashes):
            raise MigrationDenied('duplicate_point_identity')
        if not Path(entry['source_path']).is_absolute(): raise MigrationDenied('absolute_source_path_required')
    return plan


class GovernedLegacyMigrator:
    """Caller-owned credentials and read-only legacy point adapter, no paid calls.

    read_points(point_ids) returns complete {id,payload} dictionaries for those
    IDs only; payload includes exact current legacy metadata plus text. A SQL row
    lock rechecks public legacy catalog identity/state before the atomic copy.
    """
    def __init__(self, *, catalog, source_store, chunk_store, read_points,
                 authenticate_scope, legacy_schema='public'):
        self.catalog,self.source_store,self.chunk_store = catalog,source_store,chunk_store
        self.read_points,self.authenticate_scope = read_points,authenticate_scope
        self.legacy_schema = name(legacy_schema)

    def initialize(self):
        with self.catalog.transaction() as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS legacy_migration_v1 (
                governed_document_id TEXT PRIMARY KEY REFERENCES documents(document_id),
                governed_version_id TEXT NOT NULL REFERENCES versions(version_id),
                legacy_document_id TEXT NOT NULL,scope_sha256 TEXT NOT NULL,
                plan_sha256 TEXT NOT NULL,entry_sha256 TEXT NOT NULL,
                manifest_sha256 TEXT NOT NULL,source_sha256 TEXT NOT NULL,
                original_status TEXT NOT NULL CHECK(original_status IN ('indexed','archived')),
                created_at TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
                UNIQUE(legacy_document_id,scope_sha256))''')

    def _objects(self, entry):
        checkpoint = entry['checkpoint']
        self.source_store.put(entry['source_path'],expected_sha256=checkpoint['source_sha256'],
                              expected_byte_length=checkpoint['byte_length'])
        locators = []
        with tempfile.TemporaryDirectory(prefix='sentinel-migration-chunks-') as directory:
            path = Path(directory)/'chunk'
            for start in range(0,len(entry['points']),256):
                expected = entry['points'][start:start+256]
                observed = self.read_points([point['point_id'] for point in expected])
                if type(observed) is not list or len(observed) != len(expected):
                    raise MigrationDenied('point_batch_count_mismatch')
                by_id = {str(point['id']):point for point in observed}
                if len(by_id) != len(observed): raise MigrationDenied('duplicate_point_return')
                for point in expected:
                    raw = by_id.get(str(point['point_id']))
                    if raw is None or type(raw.get('payload')) is not dict: raise MigrationDenied('point_missing')
                    payload = raw['payload']
                    if any(type(payload.get(k)) is not type(point[k]) or payload.get(k) != point[k] for k in POINT_FIELDS):
                        raise MigrationDenied('current_point_metadata_changed')
                    text = payload.get('text')
                    if type(text) is not str: raise MigrationDenied('point_text_required')
                    data = text.encode('utf-8',errors='strict')
                    if len(data) != point['chunk_byte_length'] or hashlib.sha256(data).hexdigest() != point['chunk_sha256']:
                        raise MigrationDenied('point_bytes_changed')
                    path.write_bytes(data)
                    self.chunk_store.put(path,expected_sha256=point['chunk_sha256'],expected_byte_length=len(data))
                    locators.append(Locator(point['chunk_index'],point['chunk_sha256'],len(data),'chunk-cas-v2:'+point['chunk_sha256']))
        version = Version(entry['governed_version_id'],tuple(entry['scope'][k] for k in SCOPE_FIELDS),
            checkpoint['source_sha256'],checkpoint['byte_length'],checkpoint['policy_digest'],len(locators),1,1,1)
        version.validate()
        return VerifiedManifest(version,tuple(locators),manifest_digest(version,locators))

    def _legacy_locked(self, cursor, entry):
        cursor.execute(sql.SQL('SELECT {} FROM {}.documents WHERE id=%s FOR UPDATE').format(
            sql.SQL(',').join(sql.Identifier(k) for k in CATALOG_FIELDS),sql.Identifier(self.legacy_schema)),(entry['legacy_document_id'],))
        row = cursor.fetchone()
        if row is None or canonical(dict(row)) != canonical(entry['legacy_binding']):
            raise MigrationDenied('legacy_catalog_changed')

    def _verify_existing(self, cursor, entry, manifest, plan_sha256):
        cursor.execute('SELECT * FROM legacy_migration_v1 WHERE governed_document_id=%s', (entry['governed_document_id'],))
        mapping = cursor.fetchone()
        if mapping is None: return False
        expected = dict(governed_document_id=entry['governed_document_id'],governed_version_id=entry['governed_version_id'],
            legacy_document_id=entry['legacy_document_id'],scope_sha256=scope_key(entry['scope']),plan_sha256=plan_sha256,
            entry_sha256=entry['entry_sha256'],manifest_sha256=manifest.manifest_sha256,
            source_sha256=manifest.version.source_sha256,original_status=entry['legacy_binding']['status'])
        if any(mapping[key] != value for key,value in expected.items()): raise MigrationDenied('existing_mapping_conflict')
        cursor.execute('SELECT * FROM documents WHERE document_id=%s FOR UPDATE',(entry['governed_document_id'],))
        doc = cursor.fetchone()
        if doc is None or doc['version_id'] != entry['governed_version_id'] or doc['scope_sha256'] != expected['scope_sha256']:
            raise MigrationDenied('existing_document_conflict')
        if expected['original_status'] == 'archived' and doc['state'] not in ('archiving','archived','tombstoned'):
            raise MigrationDenied('archived_intent_lost')
        cursor.execute('SELECT binding_json,manifest_sha256,source_sha256,document_id FROM versions WHERE version_id=%s',(entry['governed_version_id'],))
        stored=cursor.fetchone()
        if (stored is None or stored['document_id'] != entry['governed_document_id']
                or stored['manifest_sha256'] != manifest.manifest_sha256
                or canonical(stored['binding_json']) != canonical(asdict(manifest.version))
                or stored['source_sha256'] != manifest.version.source_sha256):
            raise MigrationDenied('existing_version_conflict')
        cursor.execute('SELECT byte_length,store_version FROM source_objects WHERE source_sha256=%s',(manifest.version.source_sha256,))
        source=cursor.fetchone()
        if source is None or source['byte_length'] != manifest.version.source_byte_length or source['store_version'] != 'source-cas-v2':
            raise MigrationDenied('existing_source_conflict')
        cursor.execute('SELECT * FROM chunks WHERE version_id=%s ORDER BY chunk_index',(entry['governed_version_id'],))
        chunks=cursor.fetchall()
        if len(chunks) != len(manifest.locators): raise MigrationDenied('existing_manifest_conflict')
        for row,locator in zip(chunks,manifest.locators):
            if (row['chunk_index'],row['chunk_sha256'],row['byte_length'],row['storage_reference']) != (locator.chunk_index,locator.chunk_sha256,locator.chunk_byte_length,locator.storage_reference):
                raise MigrationDenied('existing_manifest_conflict')
        # Ensure original atomic intent still has an outbox record; it may have
        # advanced legitimately under normal governed lifecycle since migration.
        cursor.execute("SELECT 1 FROM outbox WHERE document_id=%s AND version_id=%s AND lifecycle_epoch=%s AND content_epoch=%s AND index_epoch=%s AND manifest_sha256=%s AND status IN ('pending','leased','acknowledged') LIMIT 1",(entry['governed_document_id'],entry['governed_version_id'],doc['lifecycle_epoch'],doc['content_epoch'],doc['index_epoch'],manifest.manifest_sha256))
        if cursor.fetchone() is None: raise MigrationDenied('existing_outbox_missing')
        return True

    def migrate_entry(self, plan, entry, *, expected_plan_sha256):
        validate_plan(plan,expected_plan_sha256=expected_plan_sha256)
        if entry not in plan['entries']: raise MigrationDenied('unplanned_entry')
        entry=json.loads(canonical(entry))
        return self._migrate_entry(entry,expected_plan_sha256=expected_plan_sha256)

    def _migrate_entry(self, entry, *, expected_plan_sha256):
        session,principal = self.authenticate_scope(exact_scope(entry['scope']))
        if type(session) is not GovernedAuthenticationSession or not session.bound_to(self.catalog) or not session.recheck(principal):
            raise MigrationDenied('authentication_denied')
        manifest = self._objects(entry)
        # Recheck after every external source/index/CAS operation, then lock the
        # same principal authority and catalog scope in the insertion transaction.
        self.catalog._session(session,principal,self.catalog)
        with self.catalog.transaction() as cursor:
            self.catalog._authority(cursor,principal,entry['scope'])
            key = self.catalog._scope(cursor,entry['scope'])
            # Legacy row is read/locked only; no filename/title/status mutation.
            self._legacy_locked(cursor,entry)
            if self._verify_existing(cursor,entry,manifest,expected_plan_sha256):
                return dict(legacy_document_id=entry['legacy_document_id'],governed_document_id=entry['governed_document_id'],status='verified_existing',manifest_sha256=manifest.manifest_sha256)
            version=manifest.version
            cursor.execute("INSERT INTO source_objects VALUES (%s,%s,'source-cas-v2') ON CONFLICT DO NOTHING",(version.source_sha256,version.source_byte_length))
            cursor.execute('SELECT byte_length FROM source_objects WHERE source_sha256=%s',(version.source_sha256,))
            if cursor.fetchone()['byte_length'] != version.source_byte_length: raise MigrationDenied('source_reference_conflict')
            document=dict(document_id=entry['governed_document_id'],scope_sha256=key,version_id=entry['governed_version_id'],lifecycle_epoch=1,content_epoch=1,index_epoch=1,state='pending')
            cursor.execute("INSERT INTO documents VALUES (%s,%s,%s,1,1,1,'pending')",(document['document_id'],key,document['version_id']))
            cursor.execute('INSERT INTO versions VALUES (%s,%s,%s,%s,%s)',(document['version_id'],document['document_id'],version.source_sha256,Json(asdict(version)),manifest.manifest_sha256))
            execute_values(cursor,'INSERT INTO chunks VALUES %s',[(document['version_id'],row.chunk_index,row.chunk_sha256,row.chunk_byte_length,row.storage_reference) for row in manifest.locators],page_size=256)
            operation_id=self.catalog._enqueue(cursor,document,'create',manifest.manifest_sha256)
            if entry['legacy_binding']['status']=='archived':
                cursor.execute("UPDATE outbox SET status='superseded' WHERE operation_id=%s",(operation_id,))
                cursor.execute("UPDATE documents SET state='archiving',lifecycle_epoch=2,index_epoch=2 WHERE document_id=%s RETURNING *",(document['document_id'],))
                document=dict(cursor.fetchone())
                self.catalog._enqueue(cursor,document,'archive',manifest.manifest_sha256)
            cursor.execute('INSERT INTO legacy_migration_v1(governed_document_id,governed_version_id,legacy_document_id,scope_sha256,plan_sha256,entry_sha256,manifest_sha256,source_sha256,original_status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)',
                (document['document_id'],document['version_id'],entry['legacy_document_id'],key,expected_plan_sha256,entry['entry_sha256'],manifest.manifest_sha256,version.source_sha256,entry['legacy_binding']['status']))
            cursor.execute('UPDATE scopes SET catalog_epoch=catalog_epoch+1 WHERE scope_sha256=%s',(key,))
            return dict(legacy_document_id=entry['legacy_document_id'],governed_document_id=document['document_id'],status='migrated',state=document['state'],manifest_sha256=manifest.manifest_sha256)

    def run(self, plan, *, expected_plan_sha256, max_documents=MAX_DOCUMENTS):
        validate_plan(plan,expected_plan_sha256=expected_plan_sha256)
        integer(max_documents,1,MAX_DOCUMENTS)
        # Retain one private immutable-by-ownership snapshot across callbacks.
        plan=json.loads(canonical(plan))
        results=[]
        for entry in plan['entries'][:max_documents]:
            results.append(self._migrate_entry(entry,expected_plan_sha256=expected_plan_sha256))
        return dict(plan_sha256=expected_plan_sha256,migrated=sum(row['status']=='migrated' for row in results),
            verified_existing=sum(row['status']=='verified_existing' for row in results),excluded=len(plan['excluded']),
            remaining=max(0,len(plan['entries'])-max_documents),results=results,production_enabled=False,release_authorized=False)


def main():
    """Explicit private-plan executor; secrets remain environment-only."""
    import argparse
    import psycopg2
    from qdrant_client import QdrantClient
    from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
    from app.services.governed_catalog import CatalogWriter
    from evaluation.governed_answers.content_addressed_sources import ContentAddressedSourceStore
    from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute',action='store_true',required=True)
    parser.add_argument('--plan',required=True);parser.add_argument('--expected-plan-sha256',required=True)
    parser.add_argument('--schema',required=True);parser.add_argument('--source-cas',required=True);parser.add_argument('--chunk-cas',required=True)
    parser.add_argument('--legacy-schema',default='public');parser.add_argument('--legacy-collection',default='incident_knowledge')
    parser.add_argument('--max-documents',type=int,default=MAX_DOCUMENTS)
    args=parser.parse_args()
    path=Path(args.plan)
    if path.stat().st_size>MAX_PLAN_BYTES: raise MigrationDenied('plan_budget')
    plan=json.loads(path.read_text());validate_plan(plan,expected_plan_sha256=args.expected_plan_sha256)
    writer=CatalogWriter(lambda:psycopg2.connect(os.environ['SENTINEL_MIGRATION_DSN']),schema=args.schema)
    client=QdrantClient(url=os.environ['QDRANT_URL'],api_key=os.getenv('QDRANT_API_KEY'),timeout=30)
    def points(ids):
        return [dict(id=str(row.id),payload=row.payload) for row in client.retrieve(collection_name=args.legacy_collection,ids=ids,with_payload=True,with_vectors=False)]
    def authenticate(scope):
        session=GovernedAuthenticationSession(writer)
        principal=session.authenticate(authorization_values=(os.environ['SENTINEL_MIGRATION_AUTHORIZATION'],),scope=EvidenceScope(**scope))
        return session,principal
    migrator=GovernedLegacyMigrator(catalog=writer,source_store=ContentAddressedSourceStore(args.source_cas),chunk_store=ContentAddressedChunkStore(args.chunk_cas),read_points=points,authenticate_scope=authenticate,legacy_schema=args.legacy_schema)
    try:
        migrator.initialize()
        result=migrator.run(plan,expected_plan_sha256=args.expected_plan_sha256,max_documents=args.max_documents)
        print(canonical({key:value for key,value in result.items() if key != 'results'}))
    finally: client.close()


if __name__=='__main__': main()
