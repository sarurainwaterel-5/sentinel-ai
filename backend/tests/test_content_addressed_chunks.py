import hashlib
import pytest

from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore


@pytest.fixture
def setup_store(tmp_path):
    root = tmp_path / 'chunks'
    root.mkdir(mode=0o700)
    return ContentAddressedChunkStore(root), root, tmp_path / 'input'


def reference(data):
    return dict(expected_sha256=hashlib.sha256(data).hexdigest(), expected_byte_length=len(data))


def test_exact_utf8_roundtrip_and_deduplication(setup_store):
    store, root, source = setup_store
    data = 'é\r\n  Ω\x00'.encode()
    source.write_bytes(data)
    ref = reference(data)
    assert store.put(source, **ref)['created'] is True
    assert store.put(source, **ref)['created'] is False
    assert store.read(**ref) == data
    assert len(list(root.iterdir())) == 1


@pytest.mark.parametrize('data', [b'', b'\xff', b'\xc0\xaf', b'x' * 65537])
def test_invalid_text_never_published(setup_store, data):
    store, root, source = setup_store
    source.write_bytes(data)
    with pytest.raises((ValueError, UnicodeError)):
        store.put(source, **reference(data))
    assert list(root.iterdir()) == []


def test_maximum_chunk(setup_store):
    store, root, source = setup_store
    data = b'x' * 65536
    source.write_bytes(data)
    store.put(source, **reference(data))
    assert store.read(**reference(data)) == data


@pytest.mark.parametrize('length', [True, 0, -1, 65537, 1.0])
def test_read_rejects_invalid_lengths(setup_store, length):
    store, _, _ = setup_store
    with pytest.raises(ValueError):
        store.read(expected_sha256='a' * 64, expected_byte_length=length)


@pytest.mark.parametrize('mutation', ['bytes', 'permissions', 'symlink', 'truncate'])
def test_read_rejects_tampering(setup_store, mutation):
    store, root, source = setup_store
    source.write_bytes(b'hello')
    ref = reference(b'hello')
    store.put(source, **ref)
    obj = root / ref['expected_sha256']
    if mutation == 'bytes':
        obj.write_bytes(b'wrong')
    elif mutation == 'permissions':
        obj.chmod(0o644)
    elif mutation == 'truncate':
        obj.write_bytes(b'')
    else:
        obj.unlink()
        obj.symlink_to(source)
    with pytest.raises((ValueError, OSError)):
        store.read(**ref)


def test_source_replaced_after_utf8_check_is_rejected(setup_store, monkeypatch):
    store, root, source = setup_store
    source.write_bytes(b'hello')
    original = store._store.put
    def replacing(path, **kwargs):
        source.write_bytes(b'\xff' * 5)
        return original(path, **kwargs)
    monkeypatch.setattr(store._store, 'put', replacing)
    with pytest.raises(ValueError):
        store.put(source, **reference(b'hello'))
    assert list(root.iterdir()) == []
