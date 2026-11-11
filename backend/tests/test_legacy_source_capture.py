import hashlib

import pytest

from evaluation.governed_answers.legacy_source_capture import (
    HASH_BLOCK_BYTES, MAX_SOURCE_BYTES, hash_pdf_source,
)


def test_streams_multiple_blocks_and_accepts_above_old_limit(tmp_path):
    path = tmp_path / 'large.pdf'
    block = b'x' * HASH_BLOCK_BYTES
    digest = hashlib.sha256()
    with path.open('wb') as source:
        for _ in range(21):
            source.write(block)
            digest.update(block)
    assert MAX_SOURCE_BYTES == 1024 ** 3
    assert hash_pdf_source(path) == {
        'sha256': digest.hexdigest(), 'byte_length': 21 * HASH_BLOCK_BYTES,
    }


def test_limit_is_inclusive_and_oversize_is_refused(tmp_path):
    path = tmp_path / 'source.pdf'
    path.write_bytes(b'1234')
    assert hash_pdf_source(path, max_bytes=4)['byte_length'] == 4
    with pytest.raises(ValueError, match='source_over_limit'):
        hash_pdf_source(path, max_bytes=3)


def test_symlinks_and_nonregular_files_are_refused(tmp_path):
    path = tmp_path / 'source.pdf'
    path.write_bytes(b'1234')
    link = tmp_path / 'link.pdf'
    link.symlink_to(path)
    with pytest.raises(OSError):
        hash_pdf_source(link)
    with pytest.raises((ValueError, OSError)):
        hash_pdf_source(tmp_path)


@pytest.mark.parametrize('limit', [0, -1, True, MAX_SOURCE_BYTES + 1])
def test_invalid_limits_are_refused(tmp_path, limit):
    with pytest.raises(ValueError, match='invalid_source_limit'):
        hash_pdf_source(tmp_path / 'unused', max_bytes=limit)
