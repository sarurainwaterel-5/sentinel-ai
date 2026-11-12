"""Bounded-memory chunk digests equivalent to the legacy PDF text pipeline.

Snapshots contain no text. Restoring requires the exact pending text reconstructed
by the caller; source and policy bindings are the caller's responsibility. Only
finalize() declares completion, after the caller feeds all pages.
"""
import hashlib
import re

MAX_CHUNK_HASHES = 100_000
CHUNK_SIZE = 1000
STRIDE = 800


class LegacyChunkDigestStream:
    def __init__(self, *, max_chunk_hashes=MAX_CHUNK_HASHES):
        if type(max_chunk_hashes) is not int or not 0 < max_chunk_hashes <= MAX_CHUNK_HASHES:
            raise ValueError('invalid_chunk_limit')
        self._limit = max_chunk_hashes
        self._pending = ''
        self._hashes = []
        self._characters = 0
        self._pages = 0
        self._complete = False
        self._failed = False

    @classmethod
    def restore(cls, snapshot, *, pending_text, max_chunk_hashes=MAX_CHUNK_HASHES):
        """Restore validated progress, not authenticated provenance or completion."""
        stream = cls(max_chunk_hashes=max_chunk_hashes)
        fields = {'complete', 'failed', 'page_count', 'total_characters',
                  'chunk_count', 'extraction_chunk_hashes', 'pending_length', 'pending_sha256'}
        def invalid():
            raise ValueError('invalid_stream_snapshot')
        if type(snapshot) is not dict or snapshot.keys() != fields:
            invalid()
        if snapshot['complete'] is not False or snapshot['failed'] is not False:
            invalid()
        for name in ('page_count', 'total_characters', 'chunk_count', 'pending_length'):
            if type(snapshot[name]) is not int or snapshot[name] < 0:
                invalid()
        pages, total, count, length = (snapshot[name] for name in
            ('page_count', 'total_characters', 'chunk_count', 'pending_length'))
        hashes = snapshot['extraction_chunk_hashes']
        if (pages > 1_000_000 or count > max_chunk_hashes or length >= CHUNK_SIZE
                or total != count * STRIDE + length
                or (pages == 0 and total != 0)
                or (count > 0 and length < CHUNK_SIZE - STRIDE)
                or type(hashes) is not list or len(hashes) != count):
            invalid()
        if any(type(item) is not str or re.fullmatch(r'[0-9a-f]{64}', item) is None
               for item in hashes):
            invalid()
        if type(pending_text) is not str or len(pending_text) != length:
            invalid()
        # Snapshots occur between whole pages; every nonempty page contributes
        # at least one character and its mandatory trailing newline.
        if total > 0 and (total < 2 or not pending_text.endswith('\n')):
            invalid()
        try:
            pending_digest = hashlib.sha256(pending_text.encode('utf-8')).hexdigest()
        except UnicodeError:
            invalid()
        if type(snapshot['pending_sha256']) is not str or snapshot['pending_sha256'] != pending_digest:
            invalid()
        stream._pending = pending_text
        stream._hashes = list(hashes)
        stream._characters = total
        stream._pages = pages
        return stream

    def _ensure_active(self):
        if self._complete or self._failed:
            raise ValueError('stream_not_active')

    def _emit(self):
        if len(self._hashes) >= self._limit:
            self._failed = True
            self._pending = ''
            raise ValueError('chunk_limit_exceeded')
        self._hashes.append(hashlib.sha256(self._pending.encode('utf-8')).hexdigest())
        self._pending = self._pending[STRIDE:]

    def _feed(self, text):
        start = 0
        while start < len(text):
            amount = min(CHUNK_SIZE - len(self._pending), len(text) - start)
            self._pending += text[start:start + amount]
            self._characters += amount
            start += amount
            if len(self._pending) == CHUNK_SIZE:
                self._emit()

    def feed_page(self, text):
        """Apply exactly the legacy `if page_text: text += page_text + '\\n'`."""
        self._ensure_active()
        if self._pages >= 1_000_000:
            self._failed = True
            self._pending = ''
            raise ValueError('page_limit_exceeded')
        if text is not None and type(text) is not str:
            self._failed = True
            self._pending = ''
            raise ValueError('invalid_page_text')
        if text:
            try:
                self._feed(text)
                self._feed('\n')
                self._pending.encode('utf-8')
            except UnicodeError:
                self._failed = True
                self._pending = ''
                raise ValueError('invalid_page_encoding') from None
        self._pages += 1

    def snapshot(self):
        """Return copied digest-only progress; failed streams cannot complete."""
        return {'complete': self._complete, 'failed': self._failed,
                'page_count': self._pages, 'total_characters': self._characters,
                'chunk_count': len(self._hashes),
                'extraction_chunk_hashes': list(self._hashes),
                'pending_length': len(self._pending),
                'pending_sha256': hashlib.sha256(self._pending.encode('utf-8')).hexdigest()}

    def finalize(self):
        """Flush trailing starts only after all pages have been processed."""
        self._ensure_active()
        try:
            while self._pending:
                self._emit()
        except UnicodeError:
            self._failed = True
            self._pending = ''
            raise ValueError('invalid_page_encoding') from None
        self._complete = True
        return self.snapshot()
