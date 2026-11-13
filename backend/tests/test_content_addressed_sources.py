"""Private temporary fixture files only; no live sources or network."""
import hashlib
import os
import stat
from concurrent.futures import ThreadPoolExecutor
import pytest
from evaluation.governed_answers import content_addressed_sources as cas


def setup_store(tmp_path, data=b'fixture source'):
    root = tmp_path / 'cas'; root.mkdir(mode=0o700)
    source = tmp_path / 'source'; source.write_bytes(data)
    return cas.ContentAddressedSourceStore(root), root, source, hashlib.sha256(data).hexdigest()


def put(store, source, digest):
    return store.put(source, expected_sha256=digest, expected_byte_length=source.stat().st_size)


def test_streamed_publication_and_verified_deduplication(tmp_path, monkeypatch):
    data = b'content' * 400000
    store, root, source, digest = setup_store(tmp_path, data)
    original_read = cas.os.read
    sizes = []
    def read(fd, amount):
        sizes.append(amount)
        return original_read(fd, amount)
    monkeypatch.setattr(cas.os, 'read', read)
    assert put(store, source, digest) == {'sha256': digest, 'byte_length': len(data), 'created': True}
    assert put(store, source, digest)['created'] is False
    assert (root / digest).read_bytes() == data
    assert stat.S_IMODE((root / digest).stat().st_mode) == 0o600
    assert max(sizes) <= 1024**2
    assert list(root.iterdir()) == [root / digest]


@pytest.mark.parametrize('value', [0, -1, True, 1024**3+1, '12'])
def test_invalid_size_has_no_side_effects(tmp_path, value):
    store,root,source,digest = setup_store(tmp_path)
    with pytest.raises(ValueError, match='invalid_source_length'):
        store.put(source, expected_sha256=digest, expected_byte_length=value)
    assert not list(root.iterdir())


def test_wrong_hash_and_wrong_size_leave_no_objects(tmp_path):
    store,root,source,digest=setup_store(tmp_path)
    with pytest.raises(ValueError, match='digest_mismatch'): put(store,source,'a'*64)
    with pytest.raises(ValueError, match='size_mismatch'):
        store.put(source, expected_sha256=digest, expected_byte_length=1)
    assert not list(root.iterdir())


@pytest.mark.parametrize('kind', ['source_symlink','parent_symlink','root_symlink','fifo','directory'])
def test_unsafe_paths_refused(tmp_path, kind):
    store,root,source,digest=setup_store(tmp_path)
    if kind=='source_symlink':
        link=tmp_path/'link';link.symlink_to(source);source=link
    elif kind=='parent_symlink':
        link=tmp_path/'parent';link.symlink_to(tmp_path,target_is_directory=True);source=link/'source'
    elif kind=='root_symlink':
        link=tmp_path/'rootlink';link.symlink_to(root,target_is_directory=True);store=cas.ContentAddressedSourceStore(link)
    elif kind=='fifo': source.unlink();os.mkfifo(source)
    elif kind=='directory': source.unlink();source.mkdir()
    with pytest.raises((ValueError,OSError)):
        store.put(source,expected_sha256=digest,expected_byte_length=14)
    assert not list(root.iterdir())


@pytest.mark.parametrize('kind', ['symlink','corrupt','permissive'])
def test_existing_objects_fail_closed(tmp_path, kind):
    store,root,source,digest=setup_store(tmp_path)
    target=root/digest
    if kind=='symlink':target.symlink_to(source)
    else:
        target.write_bytes(source.read_bytes() if kind=='permissive' else b'x'*source.stat().st_size)
        target.chmod(0o644 if kind=='permissive' else 0o600)
    original=target.read_bytes()
    with pytest.raises((ValueError,OSError)):put(store,source,digest)
    assert target.read_bytes()==original
    assert not list(root.glob('.pending-*'))


@pytest.mark.parametrize('replacement', [False,True])
def test_source_change_during_copy_refused(tmp_path, monkeypatch, replacement):
    store,root,source,digest=setup_store(tmp_path,b'original')
    original_read=cas.os.read;changed=False
    def read(fd,size):
        nonlocal changed
        data=original_read(fd,size)
        if data and not changed:
            changed=True
            if replacement:
                source.unlink();source.write_bytes(b'original')
            else:source.write_bytes(b'different')
        return data
    monkeypatch.setattr(cas.os,'read',read)
    with pytest.raises(ValueError):put(store,source,digest)
    assert not list(root.iterdir())


def test_file_fsync_before_publication_and_directory_fsync_after(tmp_path, monkeypatch):
    store,root,source,digest=setup_store(tmp_path)
    original=cas.os.fsync;events=[]
    def fsync(fd):
        kind='directory' if stat.S_ISDIR(os.fstat(fd).st_mode) else 'file'
        events.append(kind)
        assert (root/digest).exists() == (kind=='directory')
        return original(fd)
    monkeypatch.setattr(cas.os,'fsync',fsync)
    put(store,source,digest)
    assert events==['file','directory']


@pytest.mark.parametrize('fail_on', ['file','directory'])
def test_fsync_failure_never_exposes_partial_object(tmp_path, monkeypatch, fail_on):
    store,root,source,digest=setup_store(tmp_path)
    original=cas.os.fsync
    def fsync(fd):
        kind='directory' if stat.S_ISDIR(os.fstat(fd).st_mode) else 'file'
        if kind==fail_on:raise OSError('injected durability failure')
        return original(fd)
    monkeypatch.setattr(cas.os,'fsync',fsync)
    with pytest.raises(OSError):put(store,source,digest)
    assert not list(root.glob('.pending-*'))
    if fail_on=='directory':assert (root/digest).read_bytes()==source.read_bytes()
    else:assert not (root/digest).exists()


def test_concurrent_publication_does_not_overwrite(tmp_path):
    store,root,source,digest=setup_store(tmp_path,b'concurrent'*10000)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda _:put(store,source,digest),range(8)))
    assert sum(row['created'] for row in results)==1
    assert (root/digest).read_bytes()==source.read_bytes()
    assert not list(root.glob('.pending-*'))


def test_nonprivate_store_refused(tmp_path):
    store,root,source,digest=setup_store(tmp_path);root.chmod(0o755)
    with pytest.raises(ValueError,match='source_store_not_private'):put(store,source,digest)

@pytest.mark.parametrize('digest', ['', 'A'*64, 'a'*63, '../escape', None, True])
def test_digest_is_only_canonical_lowercase_sha256(tmp_path, digest):
    store,root,source,_=setup_store(tmp_path)
    with pytest.raises(ValueError,match='invalid_source_digest'):
        store.put(source,expected_sha256=digest,expected_byte_length=14)
    assert not list(root.iterdir())


def test_sparse_oversized_source_rejected_before_copy(tmp_path):
    store,root,source,digest=setup_store(tmp_path)
    with source.open('wb') as stream:stream.truncate(cas.MAX_SOURCE_BYTES+1)
    with pytest.raises(ValueError,match='source_size_mismatch'):
        store.put(source,expected_sha256=digest,expected_byte_length=cas.MAX_SOURCE_BYTES)
    assert not list(root.iterdir())


def test_short_writes_are_completed(tmp_path,monkeypatch):
    store,root,source,digest=setup_store(tmp_path,b'write fixture'*100)
    original=cas.os.write
    monkeypatch.setattr(cas.os,'write',lambda fd,data:original(fd,data[:7]))
    put(store,source,digest)
    assert (root/digest).read_bytes()==source.read_bytes()


def test_zero_write_fails_without_partial_publication(tmp_path,monkeypatch):
    store,root,source,digest=setup_store(tmp_path)
    monkeypatch.setattr(cas.os,'write',lambda fd,data:0)
    with pytest.raises(OSError,match='source_write_failed'):put(store,source,digest)
    assert not list(root.iterdir())


def test_verified_existing_object_is_fsynced_before_adoption(tmp_path, monkeypatch):
    store, root, source, digest = setup_store(tmp_path)
    put(store, source, digest)
    original = cas.os.fsync
    adopted = []
    target_inode = (root / digest).stat().st_ino
    def fsync(fd):
        if os.fstat(fd).st_ino == target_inode:
            adopted.append('existing_file')
            raise OSError('adoption sync failed')
        return original(fd)
    monkeypatch.setattr(cas.os, 'fsync', fsync)
    with pytest.raises(OSError, match='adoption sync failed'):
        put(store, source, digest)
    assert adopted == ['existing_file']
    assert (root / digest).read_bytes() == source.read_bytes()
    assert not list(root.glob('.pending-*'))
    monkeypatch.setattr(cas.os, 'fsync', original)
    assert put(store, source, digest)['created'] is False
