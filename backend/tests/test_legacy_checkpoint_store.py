import hashlib
import os
import stat

import pytest

from evaluation.governed_answers import legacy_checkpoint_store as store
from evaluation.governed_answers.legacy_extraction_checkpoint import create_checkpoint, checkpoint_key


@pytest.fixture
def sample(tmp_path):
    binding = dict(source_sha256='a' * 64, byte_length=100, policy_digest='b' * 64)
    record = create_checkpoint(**binding, extraction_chunk_hashes=['c' * 64])
    return tmp_path / 'private', binding, record


def test_atomic_roundtrip_private_permissions_and_idempotency(sample):
    directory, binding, record = sample
    key = store.save_checkpoint(directory, record, **binding)
    path = directory / (key + '.json')
    before = path.stat().st_ino
    assert store.load_checkpoint(directory, **binding) == record
    assert stat.S_IMODE(directory.stat().st_mode) == 0o700
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert store.save_checkpoint(directory, record, **binding) == key
    assert path.stat().st_ino == before
    assert len(list(directory.iterdir())) == 1


@pytest.mark.parametrize('contents', [b'{"truncated":', b'null', b'[]', b'not json'])
def test_invalid_record_never_reused_or_overwritten(sample, contents):
    directory, binding, record = sample
    directory.mkdir(mode=0o700)
    path = directory / (checkpoint_key(**binding) + '.json')
    path.write_bytes(contents)
    path.chmod(0o600)
    assert store.load_checkpoint(directory, **binding) is None
    with pytest.raises((ValueError, TypeError)):
        store.save_checkpoint(directory, record, **binding)
    assert path.read_bytes() == contents


def test_missing_and_wrong_source_policy_are_not_reused(sample):
    directory, binding, record = sample
    assert store.load_checkpoint(directory, **binding) is None
    store.save_checkpoint(directory, record, **binding)
    for field, value in [('source_sha256', 'd' * 64), ('byte_length', 101), ('policy_digest', 'e' * 64)]:
        assert store.load_checkpoint(directory, **{**binding, field: value}) is None
        with pytest.raises(ValueError):
            store.save_checkpoint(directory, record, **{**binding, field: value})


def test_symlink_target_never_followed(sample, tmp_path):
    directory, binding, record = sample
    directory.mkdir(mode=0o700)
    target = tmp_path / 'untouched'
    target.write_text('private')
    (directory / (checkpoint_key(**binding) + '.json')).symlink_to(target)
    assert store.load_checkpoint(directory, **binding) is None
    with pytest.raises(OSError):
        store.save_checkpoint(directory, record, **binding)
    assert target.read_text() == 'private'


def test_symlink_store_directory_rejected(sample, tmp_path):
    directory, binding, record = sample
    actual = tmp_path / 'actual'
    actual.mkdir(mode=0o700)
    directory.symlink_to(actual, target_is_directory=True)
    assert store.load_checkpoint(directory, **binding) is None
    with pytest.raises(OSError):
        store.save_checkpoint(directory, record, **binding)
    assert list(actual.iterdir()) == []


def test_oversized_record_is_bounded(sample):
    directory, binding, _ = sample
    directory.mkdir(mode=0o700)
    path = directory / (checkpoint_key(**binding) + '.json')
    with path.open('wb') as handle:
        handle.truncate(store.MAX_CHECKPOINT_BYTES + 1)
    path.chmod(0o600)
    assert store.load_checkpoint(directory, **binding) is None


@pytest.mark.parametrize('operation', ['fsync', 'link'])
def test_failed_prepublication_cleans_owned_temp_only(sample, monkeypatch, operation):
    directory, binding, record = sample
    directory.mkdir(mode=0o700)
    unrelated = directory / 'unrelated'
    unrelated.write_text('preserve')
    def failure(*args, **kwargs):
        raise OSError('simulated failure')
    monkeypatch.setattr(store.os, operation, failure)
    with pytest.raises(OSError):
        store.save_checkpoint(directory, record, **binding)
    assert list(directory.iterdir()) == [unrelated]
    assert unrelated.read_text() == 'preserve'


def test_conflicting_valid_record_preserves_previous_bytes(sample):
    directory, binding, record = sample
    key = store.save_checkpoint(directory, record, **binding)
    path = directory / (key + '.json')
    before = path.read_bytes()
    conflicting = create_checkpoint(**binding, extraction_chunk_hashes=['d' * 64])
    with pytest.raises(ValueError, match='checkpoint_conflict'):
        store.save_checkpoint(directory, conflicting, **binding)
    assert path.read_bytes() == before


def test_concurrent_publication_never_overwrites_other_writer(sample, monkeypatch):
    directory, binding, record = sample
    directory.mkdir(mode=0o700)
    path = directory / (checkpoint_key(**binding) + '.json')
    def race(*args, **kwargs):
        path.write_bytes(b'other writer')
        path.chmod(0o600)
        raise FileExistsError()
    monkeypatch.setattr(store.os, 'link', race)
    with pytest.raises(ValueError):
        store.save_checkpoint(directory, record, **binding)
    assert path.read_bytes() == b'other writer'
    assert list(directory.iterdir()) == [path]


def test_failed_write_removes_only_own_temporary(sample, monkeypatch):
    directory, binding, record = sample
    original_fdopen = store.os.fdopen
    class BrokenWriter:
        def __init__(self, handle):
            self.handle = handle
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.handle.close()
        def write(self, data):
            self.handle.write(data[:8])
            raise OSError('interrupted write')
    def fdopen(fd, mode):
        handle = original_fdopen(fd, mode)
        return BrokenWriter(handle) if mode == 'wb' else handle
    monkeypatch.setattr(store.os, 'fdopen', fdopen)
    with pytest.raises(OSError):
        store.save_checkpoint(directory, record, **binding)
    assert list(directory.iterdir()) == []


def test_postpublication_fsync_failure_keeps_complete_record(sample, monkeypatch):
    directory, binding, record = sample
    original_fsync = store.os.fsync
    def fsync(fd):
        if os.fstat(fd).st_ino == directory.stat().st_ino:
            raise OSError('directory sync failed')
        original_fsync(fd)
    monkeypatch.setattr(store.os, 'fsync', fsync)
    with pytest.raises(OSError):
        store.save_checkpoint(directory, record, **binding)
    assert store.load_checkpoint(directory, **binding) == record
    assert len(list(directory.iterdir())) == 1


def test_retry_after_publication_sync_failure_resyncs_store(sample, monkeypatch):
    directory, binding, record = sample
    original_fsync = store.os.fsync
    store_syncs = []
    def fsync(fd):
        if directory.exists() and os.fstat(fd).st_ino == directory.stat().st_ino:
            store_syncs.append(fd)
            if len(store_syncs) == 1:
                raise OSError('first store sync failed')
        original_fsync(fd)
    monkeypatch.setattr(store.os, 'fsync', fsync)
    with pytest.raises(OSError):
        store.save_checkpoint(directory, record, **binding)
    assert store.load_checkpoint(directory, **binding) == record
    store.save_checkpoint(directory, record, **binding)
    assert len(store_syncs) == 2


def test_parent_sync_failure_prevents_publication_and_retry_resyncs(sample, monkeypatch):
    directory, binding, record = sample
    original_fsync = store.os.fsync
    parent_inode = directory.parent.stat().st_ino
    parent_syncs = []
    def fsync(fd):
        if os.fstat(fd).st_ino == parent_inode:
            parent_syncs.append(fd)
            if len(parent_syncs) == 1:
                raise OSError('first parent sync failed')
        original_fsync(fd)
    monkeypatch.setattr(store.os, 'fsync', fsync)
    with pytest.raises(OSError):
        store.save_checkpoint(directory, record, **binding)
    assert directory.is_dir()
    assert list(directory.iterdir()) == []
    store.save_checkpoint(directory, record, **binding)
    assert len(parent_syncs) == 2
    assert store.load_checkpoint(directory, **binding) == record


def test_adopt_external_valid_file_syncs_validated_file(sample, monkeypatch):
    import json
    directory, binding, record = sample
    directory.mkdir(mode=0o700)
    path = directory / (checkpoint_key(**binding) + '.json')
    path.write_text(json.dumps(record))
    path.chmod(0o600)
    original_fsync = store.os.fsync
    synced = []
    def fsync(fd):
        synced.append(os.fstat(fd).st_ino)
        original_fsync(fd)
    monkeypatch.setattr(store.os, 'fsync', fsync)
    assert store.load_checkpoint(directory, **binding) == record
    assert synced == []
    store.save_checkpoint(directory, record, **binding)
    assert synced == [directory.parent.stat().st_ino, path.stat().st_ino, directory.stat().st_ino]


def test_existing_file_sync_failure_preserves_bytes(sample, monkeypatch):
    directory, binding, record = sample
    store.save_checkpoint(directory, record, **binding)
    path = directory / (checkpoint_key(**binding) + '.json')
    original = path.read_bytes()
    inode = path.stat().st_ino
    original_fsync = store.os.fsync
    def fsync(fd):
        if os.fstat(fd).st_ino == inode:
            raise OSError('adopted file sync failed')
        original_fsync(fd)
    monkeypatch.setattr(store.os, 'fsync', fsync)
    with pytest.raises(OSError):
        store.save_checkpoint(directory, record, **binding)
    assert path.read_bytes() == original


def test_concurrent_valid_winner_synced_before_success(sample, monkeypatch):
    import json
    directory, binding, record = sample
    directory.mkdir(mode=0o700)
    path = directory / (checkpoint_key(**binding) + '.json')
    original_fsync = store.os.fsync
    synced = []
    def race(*args, **kwargs):
        path.write_text(json.dumps(record))
        path.chmod(0o600)
        raise FileExistsError()
    def fsync(fd):
        synced.append(os.fstat(fd).st_ino)
        original_fsync(fd)
    monkeypatch.setattr(store.os, 'link', race)
    monkeypatch.setattr(store.os, 'fsync', fsync)
    store.save_checkpoint(directory, record, **binding)
    assert path.stat().st_ino in synced
    assert synced.index(path.stat().st_ino) < synced.index(directory.stat().st_ino)
    assert list(directory.iterdir()) == [path]
