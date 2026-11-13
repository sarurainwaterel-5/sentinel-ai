"""Transaction-owning PostgreSQL v2 catalog writer, explicitly installed only.

This service owns connections returned by connect(). It never accesses legacy
catalog tables, enables answering, provisions a default administrator or changes
ADR acceptance. CAS objects must be verified against the independently pinned
manifest before create; filesystem and index operations stay outside SQL locks.
"""
from contextlib import contextmanager
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import uuid

from psycopg2 import sql
from psycopg2.extras import Json, execute_values, RealDictCursor
from psycopg2.extensions import TRANSACTION_STATUS_IDLE

from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from evaluation.governed_answers.versioned_manifests import (
    Version, Locator, VerifiedManifest, manifest_digest, digest, integer,
)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def exact_scope(value):
    return EvidenceScope.model_validate(value, strict=True).model_dump(mode='json')


def scope_key(value):
    return hashlib.sha256(canonical(exact_scope(value)).encode()).hexdigest()


def name(value):
    if type(value) is not str or not value.strip() or len(value.encode()) > 200:
        raise ValueError('invalid_identity')
    return value


class CatalogConflict(ValueError):
    pass


class CatalogWriter:
    def __init__(self, connect, *, schema='sentinel_governed_v2'):
        self.connect = connect
        self.schema = name(schema)

    @contextmanager
    def transaction(self):
        connection = self.connect()
        try:
            if connection.autocommit or connection.get_transaction_status() != TRANSACTION_STATUS_IDLE:
                raise ValueError('dedicated_idle_transactional_connection_required')
            with connection:
                with connection.cursor(cursor_factory=RealDictCursor) as cursor:
                    cursor.execute(sql.SQL('SET LOCAL search_path TO {}, pg_catalog').format(sql.Identifier(self.schema)))
                    cursor.execute("SET LOCAL lock_timeout='5s'")
                    cursor.execute("SET LOCAL statement_timeout='15s'")
                    yield cursor
        finally:
            connection.close()

    def install(self):
        """Explicit migration into a NEW schema; existing schema fails closed."""
        with self.transaction() as cursor:
            cursor.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(self.schema)))
            cursor.execute(Path(__file__).with_name('governance_sql').joinpath('001_catalog_v2.sql').read_text())

    @staticmethod
    def _scope(cursor, scope):
        scope = exact_scope(scope)
        key = scope_key(scope)
        cursor.execute('INSERT INTO scopes VALUES (%s,%s,1) ON CONFLICT DO NOTHING', (key, Json(scope)))
        cursor.execute('SELECT scope_json FROM scopes WHERE scope_sha256=%s FOR UPDATE', (key,))
        if cursor.fetchone()['scope_json'] != scope:
            raise CatalogConflict('scope_collision')
        return key

    def provision_principal(self, principal_id, username, salt, password_hash):
        name(principal_id); name(username)
        if type(salt) is not bytes or len(salt) != 16 or type(password_hash) is not bytes or len(password_hash) != 32:
            raise ValueError('invalid_credential_material')
        with self.transaction() as cursor:
            cursor.execute('INSERT INTO principals VALUES (%s,%s,%s,%s,1,1,FALSE)', (principal_id, username, salt, password_hash))

    def read_principal(self, username):
        name(username)
        with self.transaction() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            cursor.execute('SELECT * FROM principals WHERE username=%s', (username,))
            principal = cursor.fetchone()
            if principal is None:
                return None
            principal = dict(principal)
            cursor.execute('SELECT s.scope_json FROM grants g JOIN scopes s USING(scope_sha256) WHERE g.principal_id=%s ORDER BY g.scope_sha256', (principal['principal_id'],))
            principal['scopes'] = [row['scope_json'] for row in cursor.fetchall()]
            principal['grants'] = principal['scopes']
            principal['salt'] = bytes(principal['salt'])
            principal['password_hash'] = bytes(principal['password_hash'])
            return principal

    def set_grants(self, principal_id, *, expected_permission_epoch, scopes, disabled=False):
        name(principal_id); integer(expected_permission_epoch, 1, 2**63-2)
        if type(disabled) is not bool or type(scopes) not in (list, tuple) or len(scopes) > 100:
            raise ValueError('invalid_grants')
        scope_values = [exact_scope(scope) for scope in scopes]
        if len({scope_key(scope) for scope in scope_values}) != len(scope_values):
            raise ValueError('duplicate_grants')
        with self.transaction() as cursor:
            cursor.execute('SELECT permission_epoch FROM principals WHERE principal_id=%s FOR UPDATE', (principal_id,))
            principal = cursor.fetchone()
            if principal is None or principal['permission_epoch'] != expected_permission_epoch:
                raise CatalogConflict('stale_permission_epoch')
            cursor.execute('DELETE FROM grants WHERE principal_id=%s', (principal_id,))
            for scope in sorted(scope_values, key=scope_key):
                key = self._scope(cursor, scope)
                cursor.execute('INSERT INTO grants VALUES (%s,%s)', (principal_id, key))
            cursor.execute('UPDATE principals SET permission_epoch=permission_epoch+1,disabled=%s WHERE principal_id=%s RETURNING permission_epoch', (disabled, principal_id))
            return cursor.fetchone()['permission_epoch']

    def rotate_credentials(self, principal_id, *, expected_credential_epoch, salt, password_hash):
        name(principal_id); integer(expected_credential_epoch, 1, 2**63-2)
        if type(salt) is not bytes or len(salt) != 16 or type(password_hash) is not bytes or len(password_hash) != 32:
            raise ValueError('invalid_credential_material')
        with self.transaction() as cursor:
            cursor.execute('UPDATE principals SET salt=%s,password_hash=%s,credential_epoch=credential_epoch+1 WHERE principal_id=%s AND credential_epoch=%s RETURNING credential_epoch', (salt,password_hash,principal_id,expected_credential_epoch))
            row = cursor.fetchone()
            if row is None: raise CatalogConflict('stale_credential_epoch')
            return row['credential_epoch']

    @staticmethod
    def _enqueue(cursor, document, kind, manifest_sha256):
        operation_id = str(uuid.uuid4())
        cursor.execute('INSERT INTO outbox(operation_id,document_id,version_id,kind,lifecycle_epoch,content_epoch,index_epoch,manifest_sha256,status) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,\'pending\')',
            (operation_id, document['document_id'],document['version_id'],kind,document['lifecycle_epoch'],document['content_epoch'],document['index_epoch'],manifest_sha256))
        return operation_id

    @staticmethod
    def _authority(cursor, principal, scope):
        from app.services.governed_authentication import AuthenticatedGovernedPrincipal
        if type(principal) is not AuthenticatedGovernedPrincipal or principal.scope.model_dump(mode='json') != exact_scope(scope):
            raise CatalogConflict('authority_denied')
        cursor.execute('SELECT credential_epoch,permission_epoch,disabled FROM principals WHERE principal_id=%s AND username=%s FOR UPDATE', (principal.principal_id,principal.username))
        row = cursor.fetchone()
        if (row is None or row['disabled'] or row['credential_epoch'] != principal.credential_epoch
                or row['permission_epoch'] != principal.permission_epoch):
            raise CatalogConflict('authority_denied')
        cursor.execute('SELECT 1 FROM grants WHERE principal_id=%s AND scope_sha256=%s', (principal.principal_id,scope_key(scope)))
        if cursor.fetchone() is None: raise CatalogConflict('scope_denied')

    @staticmethod
    def _session(authentication_session, principal, catalog):
        from app.services.governed_authentication import GovernedAuthenticationSession
        if (type(authentication_session) is not GovernedAuthenticationSession
                or not authentication_session.bound_to(catalog)
                or not authentication_session.recheck(principal)):
            raise CatalogConflict('authentication_denied')

    def create_authorized_version(self, document_id, manifest, *, principal, authentication_session, chunk_store, expected_manifest_sha256):
        self._session(authentication_session,principal,self)
        return self.create_version(document_id,manifest,chunk_store=chunk_store,expected_manifest_sha256=expected_manifest_sha256,_principal=principal)

    def create_version(self, document_id, manifest, *, chunk_store, expected_manifest_sha256, _principal=None):
        """Verify CAS before transaction; create pending catalog + outbox atomically.

        Expected digest must be independently pinned. This doesn't check original
        source bytes, principal permission, index visibility or release authority.
        """
        name(document_id); digest(expected_manifest_sha256)
        if type(manifest) is not VerifiedManifest or type(manifest.version) is not Version:
            raise ValueError('verified_manifest_required')
        version = manifest.version
        version.validate()
        if type(manifest.locators) is not tuple: raise ValueError('immutable_locator_tuple_required')
        if (version.state != 'pending' or (version.lifecycle_epoch,version.content_epoch,version.index_epoch) != (1,1,1)
                or manifest.manifest_sha256 != expected_manifest_sha256
                or len(manifest.locators) != version.chunk_count
                or manifest_digest(version, manifest.locators) != expected_manifest_sha256):
            raise ValueError('invalid_initial_manifest')
        for index, row in enumerate(manifest.locators):
            if type(row) is not Locator: raise ValueError('invalid_locator')
            row.validate()
            if row.chunk_index != index: raise ValueError('noncontiguous_manifest')
            chunk_store.read(expected_sha256=row.chunk_sha256,expected_byte_length=row.chunk_byte_length)
        scope = dict(zip(('organization_id','collection','module','topic'), version.scope))
        with self.transaction() as cursor:
            if _principal is not None: self._authority(cursor,_principal,scope)
            key = self._scope(cursor, scope)
            cursor.execute('INSERT INTO source_objects VALUES (%s,%s,\'source-cas-v2\') ON CONFLICT DO NOTHING', (version.source_sha256,version.source_byte_length))
            cursor.execute('SELECT byte_length FROM source_objects WHERE source_sha256=%s', (version.source_sha256,))
            if cursor.fetchone()['byte_length'] != version.source_byte_length:
                raise CatalogConflict('source_reference_collision')
            document = dict(document_id=document_id,scope_sha256=key,version_id=version.document_version_id,lifecycle_epoch=1,content_epoch=1,index_epoch=1,state='pending')
            cursor.execute('INSERT INTO documents VALUES (%s,%s,%s,1,1,1,\'pending\')', (document_id,key,version.document_version_id))
            cursor.execute('INSERT INTO versions VALUES (%s,%s,%s,%s,%s)', (version.document_version_id,document_id,version.source_sha256,Json(asdict(version)),expected_manifest_sha256))
            if manifest.locators:
                execute_values(cursor, 'INSERT INTO chunks VALUES %s', [(version.document_version_id,row.chunk_index,row.chunk_sha256,row.chunk_byte_length,row.storage_reference) for row in manifest.locators], page_size=256)
            operation = self._enqueue(cursor, document, 'create', expected_manifest_sha256)
            cursor.execute('UPDATE scopes SET catalog_epoch=catalog_epoch+1 WHERE scope_sha256=%s', (key,))
            return dict(document, operation_id=operation, manifest_sha256=expected_manifest_sha256)

    def transition_authorized(self, document_id, *, principal, authentication_session, expected_lifecycle_epoch, expected_content_epoch, expected_index_epoch, operation):
        self._session(authentication_session,principal,self)
        return self.transition(document_id,expected_lifecycle_epoch=expected_lifecycle_epoch,expected_content_epoch=expected_content_epoch,expected_index_epoch=expected_index_epoch,operation=operation,_principal=principal)

    def transition(self, document_id, *, expected_lifecycle_epoch, expected_content_epoch, expected_index_epoch, operation, _principal=None):
        name(document_id)
        for value in (expected_lifecycle_epoch,expected_content_epoch,expected_index_epoch): integer(value,1,2**63-2)
        if operation not in ('archive','restore','tombstone'): raise ValueError('invalid_transition')
        allowed = {'archive': {'active','pending','restoring','failed'}, 'restore': {'archived'}, 'tombstone': {'pending','active','archiving','archived','restoring','failed'}}
        target = {'archive':'archiving','restore':'restoring','tombstone':'tombstoned'}[operation]
        with self.transaction() as cursor:
            cursor.execute('SELECT scope_sha256 FROM documents WHERE document_id=%s', (document_id,))
            lookup = cursor.fetchone()
            if lookup is None: raise CatalogConflict('unknown_document')
            if _principal is not None:
                cursor.execute('SELECT scope_json FROM scopes WHERE scope_sha256=%s', (lookup['scope_sha256'],))
                self._authority(cursor,_principal,cursor.fetchone()['scope_json'])
            cursor.execute('SELECT catalog_epoch FROM scopes WHERE scope_sha256=%s FOR UPDATE', (lookup['scope_sha256'],))
            cursor.execute('SELECT * FROM documents WHERE document_id=%s FOR UPDATE', (document_id,))
            row = cursor.fetchone()
            if (row is None or (row['lifecycle_epoch'],row['content_epoch'],row['index_epoch']) != (expected_lifecycle_epoch,expected_content_epoch,expected_index_epoch) or row['state'] not in allowed[operation]):
                raise CatalogConflict('stale_or_invalid_transition')
            cursor.execute("UPDATE outbox SET status='superseded',lease_token=NULL,lease_until=NULL WHERE document_id=%s AND status IN ('pending','leased')", (document_id,))
            cursor.execute('UPDATE documents SET lifecycle_epoch=lifecycle_epoch+1,index_epoch=index_epoch+1,state=%s WHERE document_id=%s RETURNING *', (target,document_id))
            document = dict(cursor.fetchone())
            cursor.execute('SELECT manifest_sha256 FROM versions WHERE version_id=%s', (document['version_id'],))
            manifest_sha256 = cursor.fetchone()['manifest_sha256']
            operation_id = self._enqueue(cursor, document, operation, manifest_sha256)
            cursor.execute('UPDATE scopes SET catalog_epoch=catalog_epoch+1 WHERE scope_sha256=%s', (document['scope_sha256'],))
            return dict(document,operation_id=operation_id,manifest_sha256=manifest_sha256)

    def claim(self, *, lease_seconds=30):
        integer(lease_seconds,1,120)
        with self.transaction() as cursor:
            cursor.execute("SELECT operation_id FROM outbox WHERE (status='pending' OR (status='leased' AND lease_until<=clock_timestamp())) AND attempts<10 ORDER BY operation_id FOR UPDATE SKIP LOCKED LIMIT 1")
            row = cursor.fetchone()
            if row is None: return None
            token = str(uuid.uuid4())
            cursor.execute("UPDATE outbox SET status='leased',lease_token=%s,lease_until=clock_timestamp()+(%s*interval '1 second'),attempts=attempts+1 WHERE operation_id=%s RETURNING *", (token,lease_seconds,row['operation_id']))
            return dict(cursor.fetchone())

    def renew_lease(self, operation_id, *, lease_token, lease_seconds=30):
        """Extend only the same live current-version claim; never revive work.

        Lock order matches lifecycle/acknowledgement. A renewal does not count as
        a new claim and does not establish remote index or publication authority.
        """
        operation_id = str(uuid.UUID(str(operation_id)))
        lease_token = str(uuid.UUID(str(lease_token)))
        integer(lease_seconds, 1, 120)
        with self.transaction() as cursor:
            cursor.execute('SELECT o.document_id,d.scope_sha256 FROM outbox o JOIN documents d USING(document_id) WHERE operation_id=%s', (operation_id,))
            lookup = cursor.fetchone()
            if lookup is None: raise CatalogConflict('unknown_operation')
            cursor.execute('SELECT catalog_epoch FROM scopes WHERE scope_sha256=%s FOR UPDATE', (lookup['scope_sha256'],))
            cursor.execute('SELECT * FROM documents WHERE document_id=%s FOR UPDATE', (lookup['document_id'],))
            document = cursor.fetchone()
            cursor.execute('SELECT *,lease_until>clock_timestamp() AS lease_valid FROM outbox WHERE operation_id=%s FOR UPDATE', (operation_id,))
            op = cursor.fetchone()
            expected_state = {'create':'pending','archive':'archiving','restore':'restoring','tombstone':'tombstoned'}[op['kind']]
            if (op['status'] != 'leased' or str(op['lease_token']) != lease_token
                    or not op['lease_valid'] or document['state'] != expected_state
                    or any(document[key] != op[key] for key in ('version_id','lifecycle_epoch','content_epoch','index_epoch'))):
                raise CatalogConflict('stale_lease_renewal')
            # Recheck lease time in the UPDATE too, so lock waits cannot revive it.
            cursor.execute("UPDATE outbox SET lease_until=GREATEST(lease_until,clock_timestamp()+(%s*interval '1 second')) WHERE operation_id=%s AND status='leased' AND lease_token=%s AND lease_until>clock_timestamp() RETURNING *", (lease_seconds,operation_id,lease_token))
            renewed = cursor.fetchone()
            if renewed is None: raise CatalogConflict('stale_lease_renewal')
            return dict(renewed)

    def acknowledge(self, operation_id, *, lease_token, expected_manifest_sha256):
        """Trusted index worker receipt only; external verification precedes this.

        Exact lease, unexpired claim, immutable manifest and all current epochs
        must still match. This is not independent proof of remote index state.
        """
        operation_id = str(uuid.UUID(str(operation_id))); lease_token = str(uuid.UUID(str(lease_token)))
        digest(expected_manifest_sha256)
        # Always lock document before outbox, matching transition lock ordering.
        with self.transaction() as cursor:
            cursor.execute('SELECT o.document_id,d.scope_sha256 FROM outbox o JOIN documents d USING(document_id) WHERE operation_id=%s', (operation_id,))
            lookup = cursor.fetchone()
            if lookup is None: raise CatalogConflict('unknown_operation')
            cursor.execute('SELECT catalog_epoch FROM scopes WHERE scope_sha256=%s FOR UPDATE', (lookup['scope_sha256'],))
            cursor.execute('SELECT * FROM documents WHERE document_id=%s FOR UPDATE', (lookup['document_id'],))
            document = cursor.fetchone()
            cursor.execute("SELECT *, lease_until>clock_timestamp() AS lease_valid FROM outbox WHERE operation_id=%s FOR UPDATE", (operation_id,))
            op = cursor.fetchone()
            fields = ('version_id','lifecycle_epoch','content_epoch','index_epoch')
            if (op['status'] != 'leased' or str(op['lease_token']) != lease_token or not op['lease_valid']
                    or op['manifest_sha256'] != expected_manifest_sha256
                    or any(document[key] != op[key] for key in fields)):
                raise CatalogConflict('stale_acknowledgement')
            cursor.execute('SELECT binding_json,manifest_sha256 FROM versions WHERE version_id=%s', (document['version_id'],))
            version = cursor.fetchone()
            expected_state = {'create':'pending','archive':'archiving','restore':'restoring','tombstone':'tombstoned'}[op['kind']]
            if (document['state'] != expected_state or version['manifest_sha256'] != expected_manifest_sha256
                    or (op['kind'] in ('create','restore') and version['binding_json']['chunk_count'] == 0)):
                raise CatalogConflict('unpublishable_version')
            state = {'create':'active','restore':'active','archive':'archived','tombstone':'tombstoned'}[op['kind']]
            cursor.execute('UPDATE documents SET state=%s WHERE document_id=%s', (state,document['document_id']))
            cursor.execute("UPDATE outbox SET status='acknowledged',lease_token=NULL,lease_until=NULL WHERE operation_id=%s AND status='leased' AND lease_token=%s AND lease_until>clock_timestamp() RETURNING operation_id", (operation_id,lease_token))
            if cursor.fetchone() is None: raise CatalogConflict('stale_acknowledgement')
            cursor.execute('UPDATE scopes SET catalog_epoch=catalog_epoch+1 WHERE scope_sha256=%s', (document['scope_sha256'],))
            return dict(document,state=state)
