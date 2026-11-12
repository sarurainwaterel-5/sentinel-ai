"""Private, atomic persistence for complete extraction checkpoints only.

A successful exclusive link publishes a complete file. Directory fsync failure afterward
raises, but the newly published file remains intact; prior bytes cannot be promised
at that durability boundary. Every save syncs the immediate parent and store;
existing ancestor directories are assumed durable. No content is authenticated.
"""
import json
import os
import secrets
import stat

from .legacy_extraction_checkpoint import checkpoint_key, reusable_chunk_hashes

MAX_CHECKPOINT_BYTES = 8 * 1024 * 1024


def _directory(path, *, create):
    if create:
        try:
            os.mkdir(path, 0o700)
        except FileExistsError:
            pass
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    info = os.fstat(fd)
    if stat.S_IMODE(info.st_mode) != 0o700 or info.st_uid != os.geteuid():
        os.close(fd)
        raise ValueError('unsafe_checkpoint_directory')
    return fd


def _read(directory_fd, name, binding, *, sync_for_save=False):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory_fd)
    with os.fdopen(fd, 'rb') as handle:
        info = os.fstat(handle.fileno())
        if (not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600
                or info.st_uid != os.geteuid() or info.st_size > MAX_CHECKPOINT_BYTES):
            raise ValueError('unsafe_checkpoint_file')
        data = handle.read(MAX_CHECKPOINT_BYTES + 1)
        if len(data) > MAX_CHECKPOINT_BYTES:
            raise ValueError('checkpoint_over_limit')
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError('duplicate_checkpoint_field')
                result[key] = value
            return result
        record = json.loads(data, object_pairs_hook=unique_object)
        if reusable_chunk_hashes(record, **binding) is None:
            raise ValueError('invalid_checkpoint')
        if sync_for_save:
            os.fsync(handle.fileno())
        return record


def load_checkpoint(store_directory, *, source_sha256, byte_length, policy_digest):
    """Return None for missing, unsafe, oversized, or invalid persisted evidence."""
    binding = dict(source_sha256=source_sha256, byte_length=byte_length, policy_digest=policy_digest)
    directory_fd = None
    try:
        name = checkpoint_key(**binding) + '.json'
        directory_fd = _directory(store_directory, create=False)
        return _read(directory_fd, name, binding)
    except (OSError, ValueError, TypeError, RecursionError):
        return None
    finally:
        if directory_fd is not None:
            os.close(directory_fd)


def save_checkpoint(store_directory, checkpoint, *, source_sha256, byte_length, policy_digest):
    """Publish validated complete evidence, refusing conflicts for the same key.

    Existing identical valid evidence is idempotent. Invalid existing files require
    separate manual quarantine; this function never replaces them or symlinks.
    """
    binding = dict(source_sha256=source_sha256, byte_length=byte_length, policy_digest=policy_digest)
    key = checkpoint_key(**binding)
    if reusable_chunk_hashes(checkpoint, **binding) is None:
        raise ValueError('invalid_checkpoint')
    data = json.dumps(checkpoint, sort_keys=True, separators=(',', ':')).encode('utf-8')
    if len(data) > MAX_CHECKPOINT_BYTES:
        raise ValueError('checkpoint_over_limit')
    directory_fd = _directory(store_directory, create=True)
    name, temporary = key + '.json', '.checkpoint-' + secrets.token_hex(16) + '.tmp'
    owned_temp = False
    try:
        parent_fd = os.open('..', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory_fd)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        try:
            existing = _read(directory_fd, name, binding, sync_for_save=True)
        except FileNotFoundError:
            existing = None
        if existing is not None:
            if existing != checkpoint:
                raise ValueError('checkpoint_conflict')
            os.fsync(directory_fd)
            return key
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=directory_fd)
        owned_temp = True
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        # Exclusive hard-link publication avoids replacing a concurrent writer's
        # evidence, symlink, or unrelated object; both names reference valid bytes.
        try:
            os.link(temporary, name, src_dir_fd=directory_fd, dst_dir_fd=directory_fd,
                    follow_symlinks=False)
        except FileExistsError:
            if _read(directory_fd, name, binding, sync_for_save=True) != checkpoint:
                raise ValueError('checkpoint_conflict') from None
        os.unlink(temporary, dir_fd=directory_fd)
        owned_temp = False
        os.fsync(directory_fd)
        return key
    finally:
        try:
            if owned_temp:
                os.unlink(temporary, dir_fd=directory_fd)
        finally:
            os.close(directory_fd)
