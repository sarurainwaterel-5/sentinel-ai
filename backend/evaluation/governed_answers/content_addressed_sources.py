"""Isolated POSIX source-store proposal; never registered with live ingestion.

The owner and filesystem are trusted. Hashes identify bytes, not authorization,
encryption, retention guarantees, or provenance. A publication fsync failure may
leave a complete object; callers must reconcile/retry, never assume rollback.
"""
import hashlib
import os
import re
import stat
import uuid

MAX_SOURCE_BYTES = 1024 ** 3
BLOCK_BYTES = 1024 ** 2


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _absolute_parts(path):
    path = os.fspath(path)
    if type(path) is not str or not path.startswith('/') or '\x00' in path:
        raise ValueError('invalid_absolute_path')
    parts = path.split('/')[1:]
    if not parts or any(part in ('', '.', '..') for part in parts):
        raise ValueError('noncanonical_path')
    return parts


def _open_directory(parts):
    """Traverse every component without following symbolic links."""
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in parts:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        return fd
    except BaseException:
        os.close(fd)
        raise


def _open_source(path):
    parts = _absolute_parts(path)
    parent = _open_directory(parts[:-1])
    try:
        return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)


def _copy_and_hash(source_fd, destination_fd, expected_size):
    before = os.fstat(source_fd)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError('not_regular_source')
    if before.st_size != expected_size:
        raise ValueError('source_size_mismatch')
    digest = hashlib.sha256()
    total = 0
    while block := os.read(source_fd, BLOCK_BYTES):
        total += len(block)
        if total > expected_size or total > MAX_SOURCE_BYTES:
            raise ValueError('source_over_limit')
        digest.update(block)
        if destination_fd is not None:
            view = memoryview(block)
            while view:
                written = os.write(destination_fd, view)
                if written <= 0:
                    raise OSError('source_write_failed')
                view = view[written:]
    if total != expected_size or _identity(before) != _identity(os.fstat(source_fd)):
        raise ValueError('source_changed')
    return digest.hexdigest()


class ContentAddressedSourceStore:
    """Exclusive flat SHA-256 object publication in an existing private directory.

    No directory creation, deletion of canonical objects, network calls, catalog
    registration or migrations. The caller owns garbage collection and durable
    filesystem selection. This proposal requires POSIX dirfd, nofollow and links.
    """
    def __init__(self, root):
        self._parts = _absolute_parts(root)

    def _root_fd(self):
        fd = _open_directory(self._parts)
        info = os.fstat(fd)
        if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            os.close(fd)
            raise ValueError('source_store_not_private')
        return fd

    def put(self, source_path, *, expected_sha256, expected_byte_length):
        if type(expected_sha256) is not str or re.fullmatch('[0-9a-f]{64}', expected_sha256) is None:
            raise ValueError('invalid_source_digest')
        if type(expected_byte_length) is not int or not 0 < expected_byte_length <= MAX_SOURCE_BYTES:
            raise ValueError('invalid_source_length')
        root_fd = self._root_fd()
        source_fd = temporary_fd = None
        temporary_name = '.pending-' + uuid.uuid4().hex
        temporary_exists = False
        published = False
        try:
            source_fd = _open_source(source_path)
            temporary_fd = os.open(temporary_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                   0o600, dir_fd=root_fd)
            temporary_exists = True
            os.fchmod(temporary_fd, 0o600)
            if _copy_and_hash(source_fd, temporary_fd, expected_byte_length) != expected_sha256:
                raise ValueError('source_digest_mismatch')
            # Detect replacement of the named source as well as fd mutations.
            current_source = _open_source(source_path)
            try:
                if _identity(os.fstat(source_fd)) != _identity(os.fstat(current_source)):
                    raise ValueError('source_changed')
            finally:
                os.close(current_source)
            os.fsync(temporary_fd)
            try:
                os.link(temporary_name, expected_sha256, src_dir_fd=root_fd, dst_dir_fd=root_fd,
                        follow_symlinks=False)
                published = True
            except FileExistsError:
                existing_fd = os.open(expected_sha256, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root_fd)
                try:
                    info = os.fstat(existing_fd)
                    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600:
                        raise ValueError('invalid_existing_object_permissions')
                    if _copy_and_hash(existing_fd, None, expected_byte_length) != expected_sha256:
                        raise ValueError('existing_object_digest_mismatch')
                    # Adoption repeats file durability before syncing its directory.
                    os.fsync(existing_fd)
                finally:
                    os.close(existing_fd)
            os.unlink(temporary_name, dir_fd=root_fd)
            temporary_exists = False
            os.fsync(root_fd)
            return {'sha256': expected_sha256, 'byte_length': expected_byte_length, 'created': published}
        finally:
            if source_fd is not None:
                os.close(source_fd)
            if temporary_fd is not None:
                os.close(temporary_fd)
            try:
                if temporary_exists:
                    os.unlink(temporary_name, dir_fd=root_fd)
            finally:
                os.close(root_fd)
