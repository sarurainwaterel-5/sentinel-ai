"""Bounded read-only identities for legacy PDFs, including large reference books."""
import hashlib
import os
import stat

MAX_SOURCE_BYTES = 1024 ** 3
HASH_BLOCK_BYTES = 1024 ** 2


def hash_pdf_source(path, *, max_bytes=MAX_SOURCE_BYTES):
    """Hash a regular source with bounded memory; refuse oversized/changed files.

    The caller supplies an already scoped upload path. This neither parses the PDF
    nor proves that the hash is bound to an authorized catalog/index record.
    """
    if type(max_bytes) is not int or not 0 < max_bytes <= MAX_SOURCE_BYTES:
        raise ValueError('invalid_source_limit')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as source:
        before = os.fstat(source.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError('not_regular_source')
        if before.st_size > max_bytes:
            raise ValueError('source_over_limit')
        digest = hashlib.sha256()
        total = 0
        while block := source.read(HASH_BLOCK_BYTES):
            total += len(block)
            if total > max_bytes:
                raise ValueError('source_over_limit')
            digest.update(block)
        after = os.fstat(source.fileno())
        identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
        if total != before.st_size or identity(before) != identity(after):
            raise ValueError('source_changed')
        return {'sha256': digest.hexdigest(), 'byte_length': total}
