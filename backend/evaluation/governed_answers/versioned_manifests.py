"""Isolated v2 SQL references and complete paged verification, never authority.

The caller supplies an isolated SQLite connection and trusted CAS configuration.
Nothing in this module registers production storage or publishes a search index.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import re

from .scope_catalog_contracts import EvidenceScope

MAX_CHUNKS = 100000
PAGE_SIZE = 256


def digest(value):
    if type(value) is not str or re.fullmatch(r'[0-9a-f]{64}', value) is None:
        raise ValueError('invalid_digest')


def integer(value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError('invalid_integer')


@dataclass(frozen=True)
class Version:
    document_version_id: str
    scope: tuple[str, str, str, str]
    source_sha256: str
    source_byte_length: int
    extraction_policy_sha256: str
    chunk_count: int
    lifecycle_epoch: int
    content_epoch: int
    index_epoch: int
    state: str = 'pending'

    def validate(self):
        for value in (self.document_version_id,):
            if type(value) is not str or not value or len(value.encode('utf-8')) > 1024:
                raise ValueError('invalid_identity')
        if type(self.scope) is not tuple or len(self.scope) != 4:
            raise ValueError('invalid_scope')
        EvidenceScope.model_validate(dict(zip(('organization_id', 'collection', 'module', 'topic'), self.scope)), strict=True)
        digest(self.source_sha256)
        digest(self.extraction_policy_sha256)
        integer(self.source_byte_length, 1, 1073741824)
        integer(self.chunk_count, 0, MAX_CHUNKS)
        for value in (self.lifecycle_epoch, self.content_epoch, self.index_epoch):
            integer(value, 0, 2**63 - 1)
        if self.state not in ('pending', 'active', 'archived', 'tombstoned', 'failed'):
            raise ValueError('invalid_state')
        if self.chunk_count == 0 and self.state == 'active':
            raise ValueError('empty_active_version')


@dataclass(frozen=True)
class Locator:
    chunk_index: int
    chunk_sha256: str
    chunk_byte_length: int
    storage_reference: str

    def validate(self):
        integer(self.chunk_index, 0, MAX_CHUNKS - 1)
        digest(self.chunk_sha256)
        integer(self.chunk_byte_length, 1, 65536)
        if self.storage_reference != 'chunk-cas-v2:' + self.chunk_sha256:
            raise ValueError('invalid_storage_reference')


@dataclass(frozen=True)
class Page:
    version: Version
    start_index: int
    locators: tuple[Locator, ...]
    next_index: int | None


@dataclass(frozen=True)
class VerifiedManifest:
    version: Version
    locators: tuple[Locator, ...]
    manifest_sha256: str


def manifest_digest(version, locators):
    """Canonical metadata identity for independently pinned manifest plans."""
    hasher = hashlib.sha256()
    hasher.update(json.dumps(asdict(version), sort_keys=True, separators=(',', ':')).encode())
    for locator in locators:
        hasher.update(b'\n' + json.dumps(asdict(locator), sort_keys=True, separators=(',', ':')).encode())
    return hasher.hexdigest()


def verify_manifest(version, fetch_page, chunk_store, *, expected_manifest_sha256):
    """Fetch <=391 bounded pages, verify bytes; return only after full success.

    fetch_page(version, start, limit) must bind a single immutable snapshot. Any
    interruption, missing/extra/reordered locator or binding change fails closed.
    Returned identity proves bytes at verification time, never later authority.
    """
    version.validate()
    digest(expected_manifest_sha256)
    locators = []
    hasher = hashlib.sha256()
    hasher.update(json.dumps(asdict(version), sort_keys=True, separators=(',', ':')).encode())
    start = 0
    while True:
        page = fetch_page(version, start, PAGE_SIZE)
        if isinstance(page, Page) and isinstance(page.version, Version):
            page.version.validate()
        if not isinstance(page, Page) or page.version != version or type(page.start_index) is not int or page.start_index != start:
            raise ValueError('page_binding_mismatch')
        expected = min(PAGE_SIZE, version.chunk_count - start)
        if type(page.locators) is not tuple or len(page.locators) != expected:
            raise ValueError('page_length_mismatch')
        for offset, locator in enumerate(page.locators):
            if not isinstance(locator, Locator):
                raise ValueError('invalid_locator')
            locator.validate()
            if locator.chunk_index != start + offset:
                raise ValueError('noncontiguous_manifest')
            chunk_store.read(expected_sha256=locator.chunk_sha256,
                             expected_byte_length=locator.chunk_byte_length)
            hasher.update(b'\n' + json.dumps(asdict(locator), sort_keys=True, separators=(',', ':')).encode())
            locators.append(locator)
        next_index = start + expected
        if next_index == version.chunk_count:
            if page.next_index is not None:
                raise ValueError('extra_page')
            break
        if type(page.next_index) is not int or page.next_index != next_index:
            raise ValueError('invalid_cursor')
        start = next_index
    if hasher.hexdigest() != expected_manifest_sha256:
        raise ValueError('manifest_digest_mismatch')
    return VerifiedManifest(version, tuple(locators), hasher.hexdigest())


class ManifestRepository:
    """Immutable insert-only SQL references in a dedicated isolated database.

    SQL storage is untrusted on read. Application permissions, source validation,
    remote index publication and mutable lifecycle transitions remain external.
    """
    def __init__(self, connection):
        self.connection = connection

    def initialize(self):
        self.connection.executescript('''
        CREATE TABLE IF NOT EXISTS v2_source_object (
          sha256 TEXT PRIMARY KEY, byte_length INTEGER NOT NULL,
          store_version TEXT NOT NULL CHECK(store_version='source-cas-v2'));
        CREATE TABLE IF NOT EXISTS v2_document_version (
          id TEXT PRIMARY KEY, binding TEXT NOT NULL, manifest_sha256 TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS v2_chunk_locator (
          version_id TEXT NOT NULL REFERENCES v2_document_version(id),
          chunk_index INTEGER NOT NULL, sha256 TEXT NOT NULL,
          byte_length INTEGER NOT NULL, storage_reference TEXT NOT NULL,
          PRIMARY KEY(version_id, chunk_index));
        ''')

    def insert(self, manifest):
        """Atomically insert already verified metadata; collisions never overwrite."""
        if self.connection.in_transaction:
            raise ValueError('requires_independent_transaction')
        version = manifest.version
        version.validate()
        if len(manifest.locators) != version.chunk_count:
            raise ValueError('manifest_count_mismatch')
        # Verify structure again; a constructed VerifiedManifest is no authority.
        for index, locator in enumerate(manifest.locators):
            locator.validate()
            if locator.chunk_index != index:
                raise ValueError('noncontiguous_manifest')
        digest(manifest.manifest_sha256)
        if manifest_digest(version, manifest.locators) != manifest.manifest_sha256:
            raise ValueError('manifest_digest_mismatch')
        with self.connection:
            self.connection.execute('INSERT OR IGNORE INTO v2_source_object VALUES (?, ?, ?)',
                                    (version.source_sha256, version.source_byte_length, 'source-cas-v2'))
            row = self.connection.execute('SELECT byte_length, store_version FROM v2_source_object WHERE sha256=?', (version.source_sha256,)).fetchone()
            if tuple(row) != (version.source_byte_length, 'source-cas-v2'):
                raise ValueError('source_reference_collision')
            self.connection.execute('INSERT INTO v2_document_version VALUES (?, ?, ?)',
                                    (version.document_version_id, json.dumps(asdict(version), sort_keys=True), manifest.manifest_sha256))
            self.connection.executemany('INSERT INTO v2_chunk_locator VALUES (?, ?, ?, ?, ?)',
                ((version.document_version_id, row.chunk_index, row.chunk_sha256, row.chunk_byte_length, row.storage_reference) for row in manifest.locators))

    def fetch_page(self, version, start, limit):
        version.validate()
        integer(start, 0, version.chunk_count)
        integer(limit, 1, PAGE_SIZE)
        row = self.connection.execute('SELECT binding FROM v2_document_version WHERE id=?', (version.document_version_id,)).fetchone()
        if row is None:
            raise ValueError('sql_binding_mismatch')
        stored_binding = json.loads(row[0])
        if type(stored_binding.get('scope')) is not list:
            raise ValueError('invalid_stored_scope')
        stored_binding['scope'] = tuple(stored_binding['scope'])
        stored_version = Version(**stored_binding)
        stored_version.validate()
        if stored_version != version:
            raise ValueError('sql_binding_mismatch')
        source = self.connection.execute('SELECT byte_length, store_version FROM v2_source_object WHERE sha256=?', (version.source_sha256,)).fetchone()
        if source is None or tuple(source) != (version.source_byte_length, 'source-cas-v2'):
            raise ValueError('sql_source_mismatch')
        rows = self.connection.execute('SELECT chunk_index, sha256, byte_length, storage_reference FROM v2_chunk_locator WHERE version_id=? AND chunk_index>=? ORDER BY chunk_index LIMIT ?', (version.document_version_id, start, limit + 1)).fetchall()
        selected = tuple(Locator(*row) for row in rows[:limit])
        cursor = selected[-1].chunk_index + 1 if len(rows) > limit else None
        return Page(version, start, selected, cursor)

    def verify(self, version, chunk_store, *, expected_manifest_sha256):
        if self.connection.in_transaction:
            raise ValueError('requires_independent_snapshot')
        digest(expected_manifest_sha256)
        self.connection.execute('BEGIN')
        try:
            pinned = self.connection.execute('SELECT manifest_sha256 FROM v2_document_version WHERE id=?', (version.document_version_id,)).fetchone()
            if pinned is None or pinned[0] != expected_manifest_sha256:
                raise ValueError('sql_manifest_digest_mismatch')
            count, minimum, maximum = self.connection.execute(
                'SELECT count(*), min(chunk_index), max(chunk_index) FROM v2_chunk_locator WHERE version_id=?',
                (version.document_version_id,)).fetchone()
            if count != version.chunk_count or (count and (minimum != 0 or maximum != count - 1)):
                raise ValueError('sql_manifest_extent_mismatch')
            result = verify_manifest(version, self.fetch_page, chunk_store, expected_manifest_sha256=expected_manifest_sha256)
            self.connection.rollback()
            return result
        except BaseException:
            self.connection.rollback()
            raise
