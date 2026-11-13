"""Opt-in application intake into immutable objects and transactional v2 catalog.

Caller supplies extracted UTF-8 text and an explicit extraction-policy digest.
No live startup wiring, migration, filename-based lookup or legacy index write.
"""
import hashlib
from pathlib import Path
import os
import stat
import tempfile
import uuid

from app.services.chunking_service import chunk_text
from app.services.governed_authentication import GovernedAuthenticationSession
from evaluation.governed_answers.content_addressed_sources import _open_source, _identity
from evaluation.governed_answers.versioned_manifests import (
    Version, Locator, Page, manifest_digest, verify_manifest, MAX_CHUNKS,
)


class GovernedIngestionService:
    def __init__(self, *, catalog, source_store, chunk_store):
        self.catalog, self.source_store, self.chunk_store = catalog, source_store, chunk_store

    def ingest(self, *, session, principal, source_path, extracted_text,
               extraction_policy_sha256, document_id=None, version_id=None):
        if (type(session) is not GovernedAuthenticationSession or not session.bound_to(self.catalog)
                or not session.recheck(principal)):
            raise ValueError('authentication_or_grant_changed')
        if type(extracted_text) is not str:
            raise ValueError('text_required')
        encoded = extracted_text.encode('utf-8', errors='strict')
        if len(encoded) > 64 * 1024**2:
            raise ValueError('extraction_over_limit')
        chunks = chunk_text(extracted_text) if extracted_text.strip() else []
        if len(chunks) > MAX_CHUNKS:
            raise ValueError('chunk_count_over_limit')
        source_path = Path(source_path)
        # Hash bounded blocks, then the CAS publisher independently checks named
        # source stability and exact expected bytes. Originals are never deleted.
        fd = _open_source(source_path)
        try:
            before = os.fstat(fd)
            size = before.st_size
            if not stat.S_ISREG(before.st_mode) or not 0 < size <= 1024**3:
                raise ValueError('source_length_over_limit')
            sha = hashlib.sha256()
            total = 0
            while block := os.read(fd, 1024**2):
                total += len(block)
                if total > size: raise ValueError('source_changed')
                sha.update(block)
            if total != size or _identity(before) != _identity(os.fstat(fd)):
                raise ValueError('source_changed')
        finally:
            os.close(fd)
        version = Version(version_id or str(uuid.uuid4()),
            tuple(getattr(principal.scope, key) for key in ('organization_id','collection','module','topic')),
            sha.hexdigest(), size, extraction_policy_sha256, len(chunks), 1, 1, 1)
        version.validate()
        self.source_store.put(source_path, expected_sha256=version.source_sha256,
                              expected_byte_length=size)
        locators = []
        with tempfile.TemporaryDirectory(prefix='sentinel-governed-chunks-') as staging:
            path = Path(staging) / 'chunk'
            for index, text in enumerate(chunks):
                data = text.encode('utf-8', errors='strict')
                digest = hashlib.sha256(data).hexdigest()
                path.write_bytes(data)
                self.chunk_store.put(path, expected_sha256=digest, expected_byte_length=len(data))
                locators.append(Locator(index,digest,len(data),'chunk-cas-v2:'+digest))
        expected = manifest_digest(version, locators)
        def page(binding, start, limit):
            rows = tuple(locators[start:start+limit])
            next_index = start+len(rows)
            return Page(binding,start,rows,next_index if next_index < len(locators) else None)
        manifest = verify_manifest(version,page,self.chunk_store,expected_manifest_sha256=expected)
        if not session.recheck(principal):
            raise ValueError('authentication_or_grant_changed')
        # SQL writer must recheck locked authority as part of the catalog/outbox
        # transaction. The session observation above cannot close that race.
        result = self.catalog.create_authorized_version(document_id or str(uuid.uuid4()),manifest,
            principal=principal,authentication_session=session,chunk_store=self.chunk_store,expected_manifest_sha256=expected)
        return dict(result,production_enabled=False,release_authorized=False,
                    source_sha256=version.source_sha256,chunk_count=len(locators))
