"""Isolated UTF-8 chunk objects; byte identity never grants retrieval authority.

Use a separate private directory from source originals. Publication inherits the
source CAS durability contract, including possible complete objects after fsync
failure. No catalog writes, garbage collection or production registration.
"""
import hashlib
import os
import re
import stat

from .content_addressed_sources import (
    ContentAddressedSourceStore, _identity, _open_source,
)

MAX_CHUNK_BYTES = 65536


def _validate_reference(sha256, byte_length):
    if type(sha256) is not str or re.fullmatch('[0-9a-f]{64}', sha256) is None:
        raise ValueError('invalid_chunk_digest')
    if type(byte_length) is not int or not 0 < byte_length <= MAX_CHUNK_BYTES:
        raise ValueError('invalid_chunk_length')


def _read_verified(fd, sha256, byte_length, *, private):
    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode) or before.st_size != byte_length:
        raise ValueError('invalid_chunk_file')
    if private and (before.st_uid != os.getuid() or stat.S_IMODE(before.st_mode) != 0o600):
        raise ValueError('invalid_chunk_permissions')
    data = bytearray()
    while block := os.read(fd, min(8192, byte_length + 1 - len(data))):
        data.extend(block)
        if len(data) > byte_length:
            raise ValueError('chunk_changed')
    if len(data) != byte_length or _identity(before) != _identity(os.fstat(fd)):
        raise ValueError('chunk_changed')
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError('chunk_digest_mismatch')
    # Validate exact UTF-8; never normalize, replace, strip or re-encode content.
    data.decode('utf-8', errors='strict')
    return bytes(data)


class ContentAddressedChunkStore:
    def __init__(self, root):
        self._store = ContentAddressedSourceStore(root)

    def put(self, source_path, *, expected_sha256, expected_byte_length):
        _validate_reference(expected_sha256, expected_byte_length)
        fd = _open_source(source_path)
        try:
            _read_verified(fd, expected_sha256, expected_byte_length, private=False)
        finally:
            os.close(fd)
        # The streamed publisher independently rechecks exact hash/length and
        # source stability. A replacement after UTF-8 validation cannot change
        # accepted bytes without failing that check.
        return self._store.put(source_path, expected_sha256=expected_sha256,
                               expected_byte_length=expected_byte_length)

    def read(self, *, expected_sha256, expected_byte_length):
        _validate_reference(expected_sha256, expected_byte_length)
        root = self._store._root_fd()
        fd = current = None
        try:
            fd = os.open(expected_sha256, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                         dir_fd=root)
            data = _read_verified(fd, expected_sha256, expected_byte_length, private=True)
            current = os.open(expected_sha256, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                              dir_fd=root)
            if _identity(os.fstat(fd)) != _identity(os.fstat(current)):
                raise ValueError('chunk_changed')
            return data
        finally:
            if current is not None:
                os.close(current)
            if fd is not None:
                os.close(fd)
            os.close(root)
