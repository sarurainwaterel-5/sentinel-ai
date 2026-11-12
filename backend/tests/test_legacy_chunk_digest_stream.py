import hashlib

import pytest

from app.services.chunking_service import chunk_text
from evaluation.governed_answers.legacy_chunk_digest_stream import LegacyChunkDigestStream


@pytest.mark.parametrize('pages', [
    [], [None, ''], ['a'], ['\n'], ['x' * 799], ['x' * 800], ['x' * 999],
    ['x' * 1000], ['x' * 1599], ['x' * 1799], ['x' * 1999],
    ['x' * 5000], ['α🐍é' * 1500], ['abc', '', None, 'def\n'],
    ['a' * 699, 'b' * 300, 'c' * 1200], ['a' * 1000] * 100,
])
def test_exact_legacy_equivalence(pages):
    stream = LegacyChunkDigestStream()
    for page in pages:
        stream.feed_page(page)
        state = stream.snapshot()
        assert state['complete'] is False
        assert state['pending_length'] < 1000
    result = stream.finalize()
    text = ''.join(page + '\n' for page in pages if page)
    expected = [hashlib.sha256(chunk.encode()).hexdigest() for chunk in chunk_text(text)]
    assert result['extraction_chunk_hashes'] == expected
    assert result['total_characters'] == len(text)
    assert result['page_count'] == len(pages)
    assert result['complete'] is True
    assert result['failed'] is False
    assert result['pending_length'] == 0


def test_exact_full_chunk_keeps_trailing_overlap():
    stream = LegacyChunkDigestStream()
    stream.feed_page('x' * 999)
    assert stream.snapshot()['chunk_count'] == 1
    assert stream.snapshot()['pending_length'] == 200
    assert stream.finalize()['chunk_count'] == 2


def test_snapshots_are_copies_and_do_not_expose_text():
    stream = LegacyChunkDigestStream()
    stream.feed_page('secret document')
    state = stream.snapshot()
    assert 'secret document' not in repr(state)
    state['extraction_chunk_hashes'].append('changed')
    assert stream.snapshot()['chunk_count'] == 0
    assert stream.snapshot()['complete'] is False


@pytest.mark.parametrize('limit', [0, -1, True, 1.0, 100001])
def test_bad_limits(limit):
    with pytest.raises(ValueError):
        LegacyChunkDigestStream(max_chunk_hashes=limit)


def test_bound_failure_during_feed_never_completes():
    stream = LegacyChunkDigestStream(max_chunk_hashes=1)
    with pytest.raises(ValueError, match='chunk_limit_exceeded'):
        stream.feed_page('x' * 3000)
    assert stream.snapshot()['failed'] is True
    assert stream.snapshot()['complete'] is False
    with pytest.raises(ValueError):
        stream.finalize()


def test_bound_failure_during_final_flush_never_completes():
    stream = LegacyChunkDigestStream(max_chunk_hashes=1)
    stream.feed_page('x' * 999)
    with pytest.raises(ValueError, match='chunk_limit_exceeded'):
        stream.finalize()
    assert stream.snapshot()['complete'] is False
    assert stream.snapshot()['failed'] is True


def test_one_hundred_thousand_chunk_limit():
    stream = LegacyChunkDigestStream()
    # Reuse bounded pages rather than construct an 80-million-character string.
    for _ in range(100000):
        stream.feed_page('x' * 799)
    assert stream.finalize()['chunk_count'] == 100000


@pytest.mark.parametrize('value', [False, 1, b'text', [], {}])
def test_invalid_page_fails_closed(value):
    stream = LegacyChunkDigestStream()
    with pytest.raises(ValueError):
        stream.feed_page(value)
    assert stream.snapshot()['failed'] is True
    with pytest.raises(ValueError):
        stream.finalize()


def test_completion_is_terminal():
    stream = LegacyChunkDigestStream()
    stream.finalize()
    with pytest.raises(ValueError):
        stream.feed_page('later')
    with pytest.raises(ValueError):
        stream.finalize()


def test_unencodable_page_fails_closed():
    stream = LegacyChunkDigestStream()
    with pytest.raises(ValueError, match='invalid_page_encoding'):
        stream.feed_page('\ud800')
    assert stream.snapshot()['failed'] is True
    with pytest.raises(ValueError):
        stream.finalize()


@pytest.mark.parametrize('prefix', [[], [None, ''], ['short'], ['x' * 999], ['α🐍' * 1500]])
def test_restore_then_continue_matches_full_extraction(prefix):
    stream = LegacyChunkDigestStream()
    for page in prefix:
        stream.feed_page(page)
    state = stream.snapshot()
    text = ''.join(page + '\n' for page in prefix if page)
    pending = text[state['chunk_count'] * 800:]
    restored = LegacyChunkDigestStream.restore(state, pending_text=pending)
    state['extraction_chunk_hashes'].clear()
    rest = ['end', None, 'z' * 1700]
    for page in rest:
        restored.feed_page(page)
    result = restored.finalize()
    full = text + ''.join(page + '\n' for page in rest if page)
    assert result['extraction_chunk_hashes'] == [hashlib.sha256(c.encode()).hexdigest()
                                                for c in chunk_text(full)]


@pytest.mark.parametrize('change', [
    {'complete': True}, {'failed': True}, {'complete': 0}, {'failed': 0},
    {'filename': 'private.pdf'}, {'page_count': True}, {'page_count': -1},
    {'page_count': 1000001}, {'page_count': 0}, {'total_characters': True},
    {'total_characters': 1001}, {'chunk_count': True}, {'chunk_count': 2},
    {'pending_length': True}, {'pending_length': 1000}, {'pending_length': -1},
    {'pending_sha256': 'a' * 64}, {'extraction_chunk_hashes': []},
    {'extraction_chunk_hashes': ['A' * 64]}, {'extraction_chunk_hashes': ('a' * 64,)},
])
def test_restore_rejects_invalid_progress(change):
    stream = LegacyChunkDigestStream()
    stream.feed_page('x' * 999)
    state = stream.snapshot()
    state.update(change)
    with pytest.raises(ValueError):
        LegacyChunkDigestStream.restore(state, pending_text='x' * 199 + '\n')


def test_restore_rejects_missing_field_and_wrong_pending_text():
    stream = LegacyChunkDigestStream()
    stream.feed_page('abc')
    state = stream.snapshot()
    for name in state:
        partial = {key: value for key, value in state.items() if key != name}
        with pytest.raises(ValueError):
            LegacyChunkDigestStream.restore(partial, pending_text='abc\n')
    for pending in ('abd\n', 'abc', None, b'abc\n', '\ud800abc'):
        with pytest.raises(ValueError):
            LegacyChunkDigestStream.restore(state, pending_text=pending)


def test_restore_rejects_impossible_overlap_and_limit():
    stream = LegacyChunkDigestStream()
    stream.feed_page('x' * 1999)
    state = stream.snapshot()
    with pytest.raises(ValueError):
        LegacyChunkDigestStream.restore(state, pending_text='x' * 399 + '\n', max_chunk_hashes=1)
    state.update(pending_length=0, total_characters=1600,
                 pending_sha256=hashlib.sha256(b'').hexdigest())
    with pytest.raises(ValueError):
        LegacyChunkDigestStream.restore(state, pending_text='')


@pytest.mark.parametrize('pending', ['x', '\n', 'xx', 'α🐍'])
def test_restore_rejects_impossible_completed_page_tail(pending):
    stream = LegacyChunkDigestStream()
    state = stream.snapshot()
    state.update(page_count=1, total_characters=len(pending), pending_length=len(pending),
                 pending_sha256=hashlib.sha256(pending.encode()).hexdigest())
    with pytest.raises(ValueError):
        LegacyChunkDigestStream.restore(state, pending_text=pending)


def test_restore_accepts_minimum_nonempty_newline_page():
    stream = LegacyChunkDigestStream()
    stream.feed_page('\n')
    restored = LegacyChunkDigestStream.restore(stream.snapshot(), pending_text='\n\n')
    assert restored.finalize()['extraction_chunk_hashes'] == [hashlib.sha256(b'\n\n').hexdigest()]
