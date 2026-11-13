"""Disposable PostgreSQL/Qdrant composition; never runtime eligibility.

Uses tiny synthetic bytes and fixed synthetic vectors, not embeddings, semantic
retrieval, application authentication, or a legacy migration. No providers run.
"""
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
import uuid

import psycopg2
from psycopg2 import sql

from . import postgres_rehearsal as pg

PREFIX = 'sentinel_sprint21_rehearsal_'
SCOPE = dict(organization_id='organization', collection='manuals', module='ir', topic='sre')
CHUNKS = (b'Check queue depth before restart.', b'Escalate sustained backlog.')


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def _sha(value):
    return hashlib.sha256(value).hexdigest()


class InspectionDenied(ValueError):
    """Fixed diagnostic only; never contains source bytes or connection data."""


class _Index:
    def __init__(self, url):
        parsed = urllib.parse.urlsplit(url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ('', '/') or not parsed.port or parsed.port == 6333):
            raise ValueError('dedicated_loopback_qdrant_required')
        self.url = url.rstrip('/')
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def call(self, method, path, body=None):
        data = None if body is None else _json(body).encode()
        request = urllib.request.Request(self.url + path, data=data, method=method,
                                         headers={'Content-Type': 'application/json'})
        with self.opener.open(request, timeout=5) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise InspectionDenied('index_response_over_limit')
        return json.loads(raw)['result']


def _snapshot(connection, schema, *, reconciled=True):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            pg._search_path(cursor, schema)
            cursor.execute("SELECT permission_epoch,disabled FROM principals WHERE principal_id='principal'")
            principal = cursor.fetchone()
            cursor.execute("SELECT 1 FROM grants WHERE principal_id='principal' AND scope_id='scope'")
            grant = cursor.fetchone()
            cursor.execute("SELECT lifecycle,content,state,scope_id FROM identities WHERE document_id='document'")
            identity = cursor.fetchone()
            if not principal or principal[1] or not grant or not identity or identity[2:] != ('pending', 'scope'):
                raise InspectionDenied('authority_or_lifecycle_denied')
            cursor.execute("SELECT organization_id,collection,module,topic,revision FROM scopes WHERE scope_id='scope'")
            scope = cursor.fetchone()
            if dict(zip(SCOPE, scope[:4])) != SCOPE:
                raise InspectionDenied('scope_changed')
            cursor.execute("SELECT source,source_sha256,manifest_sha256 FROM versions WHERE document_id='document' AND content=%s", (identity[1],))
            source, source_hash, manifest_hash = cursor.fetchone()
            if _sha(bytes(source)) != source_hash:
                raise InspectionDenied('source_hash_mismatch')
            cursor.execute("SELECT locator,bytes,sha256 FROM chunks WHERE document_id='document' AND content=%s ORDER BY locator", (identity[1],))
            chunks = [(locator, bytes(data), digest) for locator, data, digest in cursor.fetchall()]
            manifest = [{'locator': locator, 'sha256': digest, 'length': len(data)} for locator, data, digest in chunks]
            if (not chunks or [row[0] for row in chunks] != list(range(len(chunks)))
                    or any(_sha(data) != digest for _, data, digest in chunks)
                    or _sha(_json(manifest).encode()) != manifest_hash):
                raise InspectionDenied('manifest_mismatch')
            # Synthetic extraction policy: the source is exactly newline-joined
            # supplied chunks, not an assertion about arbitrary PDF extraction.
            if bytes(source) != b'\n'.join(data for _, data, _ in chunks):
                raise InspectionDenied('synthetic_source_binding_mismatch')
            if reconciled:
                cursor.execute("SELECT status FROM outbox WHERE operation_id='create'")
                if cursor.fetchone() != ('reconciled',):
                    raise InspectionDenied('index_not_reconciled')
            return dict(permission_epoch=principal[0], revision=scope[4], lifecycle=identity[0],
                        content=identity[1], source_sha256=source_hash,
                        manifest_sha256=manifest_hash, chunks=chunks)


def _points(snapshot):
    return [dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'sentinel-rehearsal-document-' + str(locator))),
        vector=[1.0, 0.0, 0.0, 0.0], payload=dict(document_id='document', **SCOPE,
            lifecycle=snapshot['lifecycle'], content=snapshot['content'],
            manifest_sha256=snapshot['manifest_sha256'], locator=locator,
            chunk_sha256=digest, text=data.decode('utf-8')))
        for locator, data, digest in snapshot['chunks']]


def _verify_index(index, collection, snapshot):
    result = index.call('POST', '/collections/' + collection + '/points/scroll',
        dict(filter={'must': [{'key': 'document_id', 'match': {'value': 'document'}}]},
             limit=33, with_payload=True, with_vector=False))
    actual = result['points']
    expected = _points(snapshot)
    if result.get('next_page_offset') is not None or len(actual) != len(expected):
        raise InspectionDenied('index_manifest_mismatch')
    by_id = {point['id']: point['payload'] for point in actual}
    if (len(by_id) != len(actual)
            or _json(by_id) != _json({point['id']: point['payload'] for point in expected})):
        raise InspectionDenied('index_manifest_mismatch')
    matches = index.call('POST', '/collections/' + collection + '/points/query',
        dict(query=[1.0, 0.0, 0.0, 0.0], filter={'must': [
            {'key': key, 'match': {'value': value}} for key, value in
            dict(document_id='document', **SCOPE).items()]},
             limit=32, with_payload=True, with_vector=False))['points']
    if (_json({point['id']: point['payload'] for point in matches}) != _json(by_id)
            or len(matches) != len(expected)):
        raise InspectionDenied('scoped_retrieval_mismatch')
    # Resolve returned locators against authoritative SQL bytes, never the text
    # echoed by vector search alone.
    return tuple(snapshot['chunks'][point['payload']['locator']][1] for point in matches)


def _inspect(connection, schema, index, collection, after_read=None):
    before = _snapshot(connection, schema)
    resolved = _verify_index(index, collection, before)
    if after_read:
        after_read()
    if _snapshot(connection, schema) != before:
        raise InspectionDenied('inspection_state_changed')
    return {'resolved_chunk_hashes': sorted(_sha(data) for data in resolved),
            'source_sha256': before['source_sha256'], 'manifest_sha256': before['manifest_sha256']}


def run_composition_rehearsal(*, dsn, qdrant_url):
    """Create and remove only UUID-owned disposable schema/collection.

    Requires PostgreSQL16 database sentinel_sprint21_rehearsal and a dedicated
    loopback Qdrant port whose collections are empty or rehearsal-prefixed.
    Exceptions propagate to the explicit local caller; never print DSN/errors.
    """
    if type(dsn) is not str or not dsn or type(qdrant_url) is not str:
        raise ValueError('explicit_disposable_services_required')
    index = _Index(qdrant_url)
    connection = psycopg2.connect(dsn, connect_timeout=5)
    schema = collection = PREFIX + uuid.uuid4().hex
    schema_created = collection_created = False
    checks = {}
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(),current_setting('server_version_num')::int")
                database, version = cursor.fetchone()
                if database != pg.DATABASE or not 160000 <= version < 170000:
                    raise ValueError('dedicated_postgresql16_database_required')
        if any(not item['name'].startswith(PREFIX) for item in index.call('GET', '/collections')['collections']):
            raise ValueError('dedicated_qdrant_server_required')
        pg._schema(connection, schema, pg.DDL_PATH.read_text())
        schema_created = True
        source = b'\n'.join(CHUNKS)
        manifest = [{'locator': i, 'sha256': _sha(data), 'length': len(data)} for i, data in enumerate(CHUNKS)]
        manifest_hash = _sha(_json(manifest).encode())
        with connection:
            with connection.cursor() as cursor:
                pg._search_path(cursor, schema)
                cursor.execute("INSERT INTO principals VALUES('principal',1,false)")
                cursor.execute("INSERT INTO scopes VALUES('scope','organization','manuals','ir','sre',1)")
                cursor.execute("INSERT INTO grants VALUES('principal','scope')")
                cursor.execute("INSERT INTO identities VALUES('document','scope',1,1,'pending')")
                cursor.execute("INSERT INTO versions VALUES('document',1,%s,%s,%s)", (psycopg2.Binary(source), _sha(source), manifest_hash))
                for i, data in enumerate(CHUNKS):
                    cursor.execute("INSERT INTO chunks VALUES('document',1,%s,%s,%s)", (i, psycopg2.Binary(data), _sha(data)))
                cursor.execute("INSERT INTO outbox VALUES('create','document','scope',1,1,'pending',%s,'pending')", (manifest_hash,))
        before = pg._inventory(connection, schema)
        try:
            pg._transition(connection, schema, operation='create', expected=1, state='archived', manifest_hash=manifest_hash)
        except psycopg2.errors.UniqueViolation:
            pass
        else:
            raise AssertionError('expected_atomic_failure')
        checks['catalog_outbox_atomic_rollback'] = pg._inventory(connection, schema) == before
        index.call('PUT', '/collections/' + collection, {'vectors': {'size': 4, 'distance': 'Cosine'}})
        collection_created = True
        snapshot = _snapshot(connection, schema, reconciled=False)
        points = _points(snapshot)
        index.call('PUT', '/collections/' + collection + '/points?wait=true', {'points': points})
        _verify_index(index, collection, snapshot)
        checks['actual_index_readback_before_acknowledgement'] = pg._reconcile(connection, schema, 'create') == 'reconciled'
        inspection = _inspect(connection, schema, index, collection)
        checks['scoped_query_sql_byte_resolution'] = inspection['resolved_chunk_hashes'] == sorted(_sha(data) for data in CHUNKS)
        for case, field, value in [('text', 'text', 'untrusted changed text'),
                ('organization_id', 'organization_id', 'foreign'),
                ('content', 'content', 2), ('lifecycle', 'lifecycle', 2), ('locator', 'locator', 9),
                ('boolean_content', 'content', True), ('boolean_lifecycle', 'lifecycle', True),
                ('boolean_locator', 'locator', False)]:
            altered = json.loads(_json(points))
            altered[0]['payload'][field] = value
            index.call('PUT', '/collections/' + collection + '/points?wait=true', {'points': altered})
            try:
                _inspect(connection, schema, index, collection)
            except InspectionDenied:
                checks['reject_index_' + case + '_mutation'] = True
            else:
                raise AssertionError('index_mutation_accepted')
            index.call('PUT', '/collections/' + collection + '/points?wait=true', {'points': points})
        def revoke():
            second = psycopg2.connect(dsn, connect_timeout=5)
            try:
                with second:
                    with second.cursor() as cursor:
                        pg._search_path(cursor, schema)
                        cursor.execute("DELETE FROM grants WHERE principal_id='principal'")
                        cursor.execute("UPDATE principals SET permission_epoch=permission_epoch+1 WHERE principal_id='principal'")
            finally:
                second.close()
        try:
            _inspect(connection, schema, index, collection, after_read=revoke)
        except InspectionDenied:
            checks['separate_connection_revocation_before_return'] = True
        else:
            raise AssertionError('revocation_accepted')
        with connection:
            with connection.cursor() as cursor:
                pg._search_path(cursor, schema)
                cursor.execute("INSERT INTO grants VALUES('principal','scope')")
        pg._transition(connection, schema, operation='archive', expected=1, state='archived', manifest_hash=manifest_hash)
        checks['late_index_completion_stale'] = pg._reconcile(connection, schema, 'create') == 'stale'
        try:
            _inspect(connection, schema, index, collection)
        except InspectionDenied:
            checks['archive_denies_despite_retained_vectors'] = True
        else:
            raise AssertionError('archived_source_accepted')
        if not all(checks.values()):
            raise AssertionError('composition_check_failed')
        report = dict(schema_version='isolated-postgres-qdrant-composition-v1',
            execution_source='actual_disposable_postgres_qdrant', checks=checks,
            source_sha256=inspection['source_sha256'], manifest_sha256=manifest_hash,
            schema_sha256=_sha(pg.DDL_PATH.read_bytes()), source_bytes=len(source), chunks=len(CHUNKS),
            vector_kind='fixed_synthetic_not_embeddings', application_migrated=False,
            production_enabled=False, release_authorized=False, governed_eligible=False,
            authenticated_application_principal=False, semantic_grounding_verified=False,
            proposition_to_inference='closed')
    finally:
        try:
            if collection_created:
                index.call('DELETE', '/collections/' + collection)
        finally:
            try:
                if schema_created:
                    with connection:
                        with connection.cursor() as cursor:
                            cursor.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
            finally:
                connection.close()
    report['owned_collection_and_schema_removed'] = True
    return report
