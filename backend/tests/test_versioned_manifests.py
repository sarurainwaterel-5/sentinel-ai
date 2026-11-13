from dataclasses import replace
import hashlib
import sqlite3
import pytest
from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore
from evaluation.governed_answers.versioned_manifests import Locator, ManifestRepository, Page, Version, manifest_digest, verify_manifest


def fixture(tmp_path, count=257):
    root = tmp_path / 'objects'
    root.mkdir(mode=0o700)
    source = tmp_path / 'text'
    source.write_bytes(b'exact bytes\n')
    sha = hashlib.sha256(source.read_bytes()).hexdigest()
    store = ContentAddressedChunkStore(str(root))
    store.put(str(source), expected_sha256=sha, expected_byte_length=12)
    version = Version('v1', ('org', 'collection', 'module', 'topic'), 'a'*64, 42, 'b'*64, count, 1, 2, 3)
    rows = tuple(Locator(i, sha, 12, 'chunk-cas-v2:' + sha) for i in range(count))
    def fetch(v, start, limit):
        end = min(start + limit, count)
        return Page(v, start, rows[start:end], end if end < count else None)
    return version, rows, store, fetch


@pytest.mark.parametrize('count', [0, 1, 255, 256, 257, 513])
def test_roundtrip(tmp_path, count):
    v, rows, store, fetch = fixture(tmp_path, count)
    manifest = verify_manifest(v, fetch, store, expected_manifest_sha256=manifest_digest(v, rows))
    repo = ManifestRepository(sqlite3.connect(':memory:'))
    repo.initialize()
    repo.insert(manifest)
    assert repo.verify(v, store, expected_manifest_sha256=manifest_digest(v, rows)) == manifest
    assert manifest.locators == rows
    assert not repo.connection.in_transaction


@pytest.mark.parametrize('mutation', ['binding', 'start', 'missing', 'extra', 'reorder', 'cursor', 'bool'])
def test_bad_page(tmp_path, mutation):
    v, rows, store, fetch = fixture(tmp_path)
    def bad(version, start, limit):
        page = fetch(version, start, limit)
        if mutation == 'binding': return replace(page, version=replace(v, content_epoch=4))
        if mutation == 'start': return replace(page, start_index=True)
        if mutation == 'missing': return replace(page, locators=page.locators[:-1])
        if mutation == 'extra': return replace(page, locators=page.locators + (rows[0],))
        if mutation == 'reorder': return replace(page, locators=tuple(reversed(page.locators)))
        if mutation == 'bool': return replace(page, version=replace(v, lifecycle_epoch=True))
        return replace(page, next_index=0)
    with pytest.raises(ValueError): verify_manifest(v, bad, store, expected_manifest_sha256=manifest_digest(v, rows))


def test_interruption(tmp_path):
    v, rows, store, fetch = fixture(tmp_path)
    def interrupted(version, start, limit):
        if start: raise InterruptedError('stopped')
        return fetch(version, start, limit)
    with pytest.raises(InterruptedError): verify_manifest(v, interrupted, store, expected_manifest_sha256=manifest_digest(v, rows))


@pytest.mark.parametrize('sql', [
    'DELETE FROM v2_chunk_locator WHERE chunk_index=20',
    "UPDATE v2_chunk_locator SET storage_reference='../../escape' WHERE chunk_index=20",
    'UPDATE v2_chunk_locator SET chunk_index=-1 WHERE chunk_index=20',
    'UPDATE v2_source_object SET byte_length=43',
])
def test_tamper(tmp_path, sql):
    v, rows, store, fetch = fixture(tmp_path)
    repo = ManifestRepository(sqlite3.connect(':memory:'))
    repo.initialize()
    repo.insert(verify_manifest(v, fetch, store, expected_manifest_sha256=manifest_digest(v, rows)))
    repo.connection.execute(sql)
    repo.connection.commit()
    with pytest.raises(ValueError): repo.verify(v, store, expected_manifest_sha256=manifest_digest(v, rows))
    assert not repo.connection.in_transaction


def test_collision_rollback(tmp_path):
    v, rows, store, fetch = fixture(tmp_path, 1)
    repo = ManifestRepository(sqlite3.connect(':memory:'))
    repo.initialize()
    manifest = verify_manifest(v, fetch, store, expected_manifest_sha256=manifest_digest(v, rows))
    repo.insert(manifest)
    altered = replace(v, source_sha256='c'*64)
    with pytest.raises(sqlite3.IntegrityError):
        repo.insert(replace(manifest, version=altered, manifest_sha256=manifest_digest(altered, rows)))
    assert repo.connection.execute('SELECT count(*) FROM v2_source_object').fetchone()[0] == 1
    assert repo.verify(v, store, expected_manifest_sha256=manifest_digest(v, rows)) == manifest


def test_empty_active(tmp_path):
    v, rows, store, fetch = fixture(tmp_path, 0)
    with pytest.raises(ValueError): verify_manifest(replace(v, state='active'), fetch, store, expected_manifest_sha256=manifest_digest(v, rows))


def test_tampered_bytes(tmp_path):
    v, rows, store, fetch = fixture(tmp_path, 1)
    repo = ManifestRepository(sqlite3.connect(':memory:'))
    repo.initialize()
    repo.insert(verify_manifest(v, fetch, store, expected_manifest_sha256=manifest_digest(v, rows)))
    (tmp_path / 'objects' / rows[0].chunk_sha256).write_bytes(b'wrong bytes\n')
    with pytest.raises(ValueError): repo.verify(v, store, expected_manifest_sha256=manifest_digest(v, rows))


def test_full_capacity_bounded_pages():
    class Store:
        def read(self, **kwargs): return b'x'
    v = Version('v', ('org', 'collection', 'module', 'topic'), 'a'*64, 1, 'b'*64, 100000, 0, 0, 0)
    calls = []
    def fetch(version, start, limit):
        calls.append((start, limit))
        end = min(start + limit, v.chunk_count)
        rows = tuple(Locator(i, 'c'*64, 1, 'chunk-cas-v2:' + 'c'*64) for i in range(start, end))
        return Page(version, start, rows, end if end < v.chunk_count else None)
    rows = tuple(Locator(i, 'c'*64, 1, 'chunk-cas-v2:' + 'c'*64) for i in range(v.chunk_count))
    assert len(verify_manifest(v, fetch, Store(), expected_manifest_sha256=manifest_digest(v, rows)).locators) == 100000
    assert len(calls) == 391
    assert all(limit == 256 for _, limit in calls)


def test_sql_binding_bool_rejected(tmp_path):
    import json
    v, rows, store, fetch = fixture(tmp_path, 1)
    repo = ManifestRepository(sqlite3.connect(':memory:'))
    repo.initialize()
    repo.insert(verify_manifest(v, fetch, store, expected_manifest_sha256=manifest_digest(v, rows)))
    binding = json.loads(repo.connection.execute('SELECT binding FROM v2_document_version').fetchone()[0])
    binding['lifecycle_epoch'] = True
    repo.connection.execute('UPDATE v2_document_version SET binding=?', (json.dumps(binding),))
    repo.connection.commit()
    with pytest.raises(ValueError): repo.verify(v, store, expected_manifest_sha256=manifest_digest(v, rows))


def test_preserves_callers_transaction(tmp_path):
    v, rows, store, fetch = fixture(tmp_path, 1)
    repo = ManifestRepository(sqlite3.connect(':memory:'))
    repo.initialize()
    repo.connection.execute('BEGIN')
    manifest = verify_manifest(v, fetch, store, expected_manifest_sha256=manifest_digest(v, rows))
    with pytest.raises(ValueError): repo.insert(manifest)
    with pytest.raises(ValueError): repo.verify(v, store, expected_manifest_sha256=manifest_digest(v, rows))
    assert repo.connection.in_transaction


def test_sql_snapshot_survives_concurrent_binding_change(tmp_path):
    from dataclasses import asdict
    import json
    v, rows, store, fetch = fixture(tmp_path)
    db = tmp_path / 'isolated.sqlite'
    connection = sqlite3.connect(db)
    connection.execute('PRAGMA journal_mode=WAL')
    repo = ManifestRepository(connection)
    repo.initialize()
    manifest = verify_manifest(v, fetch, store, expected_manifest_sha256=manifest_digest(v, rows))
    repo.insert(manifest)
    other = sqlite3.connect(db)
    class ConcurrentStore:
        changed = False
        def read(self, **kwargs):
            if not self.changed:
                other.execute('UPDATE v2_document_version SET binding=?', (json.dumps(asdict(replace(v, state='archived'))),))
                other.commit()
                self.changed = True
            return store.read(**kwargs)
    assert repo.verify(v, ConcurrentStore(), expected_manifest_sha256=manifest_digest(v, rows)) == manifest
    # Snapshot coherence does not grant current lifecycle authority.
    with pytest.raises(ValueError): repo.verify(v, store, expected_manifest_sha256=manifest_digest(v, rows))
    other.close()
    connection.close()


def test_valid_object_substitution_rejected_by_external_pin(tmp_path):
    v, rows, store, fetch = fixture(tmp_path, 1)
    pinned = manifest_digest(v, rows)
    manifest = verify_manifest(v, fetch, store, expected_manifest_sha256=pinned)
    repo = ManifestRepository(sqlite3.connect(':memory:'))
    repo.initialize()
    repo.insert(manifest)
    alternate = tmp_path / 'alternate'
    alternate.write_bytes(b'other valid UTF-8 bytes')
    sha = hashlib.sha256(alternate.read_bytes()).hexdigest()
    size = alternate.stat().st_size
    store.put(str(alternate), expected_sha256=sha, expected_byte_length=size)
    replacement = Locator(0, sha, size, 'chunk-cas-v2:' + sha)
    repo.connection.execute('UPDATE v2_chunk_locator SET sha256=?, byte_length=?, storage_reference=?',
                            (sha, size, replacement.storage_reference))
    repo.connection.commit()
    with pytest.raises(ValueError, match='manifest_digest_mismatch'):
        repo.verify(v, store, expected_manifest_sha256=pinned)
    # Even a coherently rewritten database digest cannot replace the external pin.
    repo.connection.execute('UPDATE v2_document_version SET manifest_sha256=?',
                            (manifest_digest(v, (replacement,)),))
    repo.connection.commit()
    with pytest.raises(ValueError, match='sql_manifest_digest_mismatch'):
        repo.verify(v, store, expected_manifest_sha256=pinned)


def test_insert_rejects_forged_manifest_digest(tmp_path):
    v, rows, store, fetch = fixture(tmp_path, 1)
    manifest = verify_manifest(v, fetch, store, expected_manifest_sha256=manifest_digest(v, rows))
    repo = ManifestRepository(sqlite3.connect(':memory:'))
    repo.initialize()
    with pytest.raises(ValueError, match='manifest_digest_mismatch'):
        repo.insert(replace(manifest, manifest_sha256='d'*64))
    assert repo.connection.execute('SELECT count(*) FROM v2_document_version').fetchone()[0] == 0


@pytest.mark.parametrize('scope', ['opaque', ('org',), ('org', '*', 'module', 'topic'), ('org', 'collection', 'module', True)])
def test_scope_exact_shape(tmp_path, scope):
    v, rows, store, fetch = fixture(tmp_path, 1)
    altered = replace(v, scope=scope)
    with pytest.raises(ValueError):
        verify_manifest(altered, fetch, store, expected_manifest_sha256=manifest_digest(v, rows))
