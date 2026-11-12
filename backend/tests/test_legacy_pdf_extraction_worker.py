import hashlib
from types import SimpleNamespace

import pytest

from evaluation.governed_answers.legacy_chunk_digest_stream import LegacyChunkDigestStream
from evaluation.governed_answers.legacy_extraction_checkpoint import extraction_policy_digest
from evaluation.governed_answers.legacy_pdf_extraction_worker import run_worker


@pytest.fixture
def setup(tmp_path):
    source = tmp_path / 'source.pdf'
    source.write_bytes(b'%PDF-test-private')
    pdf = tmp_path / 'pdf.py'
    chunk = tmp_path / 'chunk.py'
    pdf.write_text('extract')
    chunk.write_text('chunk')
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    request = dict(source_sha256=digest(source), byte_length=source.stat().st_size,
                   policy_digest=extraction_policy_digest(pdf_service_sha256=digest(pdf),
                   chunking_service_sha256=digest(chunk), pypdf_version='6.0'), resume=None)
    kwargs = dict(source_path=source, upload_root=tmp_path, pdf_service_path=pdf,
                  chunking_service_path=chunk, parser_version='6.0', progress_interval_pages=1)
    return request, kwargs


def reader_for(texts, mutate=None):
    class Page:
        def __init__(self, text):
            self.text = text
        def extract_text(self):
            if mutate:
                mutate()
            if isinstance(self.text, Exception):
                raise self.text
            return self.text
    return lambda handle: SimpleNamespace(pages=[Page(text) for text in texts])


def execute(setup, texts, **overrides):
    request, kwargs = setup
    events = []
    run_worker(request, **{**kwargs, 'reader_factory': reader_for(texts), **overrides}, emit=events.append)
    return events


def test_finish_matches_stream_and_emits_no_text_or_paths(setup):
    pages = ['secret document' * 100, None, '', 'α🐍' * 1300]
    events = execute(setup, pages)
    expected = LegacyChunkDigestStream()
    for page in pages:
        expected.feed_page(page)
    assert events[-1]['event'] == 'complete'
    assert events[-1]['snapshot'] == expected.finalize()
    assert 'secret document' not in repr(events)
    assert str(setup[1]['source_path']) not in repr(events)
    assert all(not event['snapshot']['complete'] for event in events if event['event'] == 'progress')


@pytest.mark.parametrize('prefix', [[], [''], ['a' * 999], ['x', None, '', 'y' * 100]])
def test_resume_reconstructs_pending_and_finishes_equivalently(setup, prefix):
    stream = LegacyChunkDigestStream()
    for text in prefix:
        stream.feed_page(text)
    setup[0]['resume'] = stream.snapshot()
    pages = prefix + ['final' * 500]
    events = execute(setup, pages)
    assert any(event['event'] == 'resumed' for event in events)
    for text in pages[len(prefix):]:
        stream.feed_page(text)
    assert events[-1]['snapshot'] == stream.finalize()


@pytest.mark.parametrize('field,value', [('source_sha256', 'a' * 64), ('byte_length', 3),
                                         ('policy_digest', 'a' * 64)])
def test_binding_changes_rejected_before_reader(setup, field, value):
    setup[0][field] = value
    def forbidden(handle):
        pytest.fail('reader constructed before source and policy validation')
    assert execute(setup, [], reader_factory=forbidden) == [
        {'event': 'failed', 'reason': 'source_or_policy_validation_failed'}]


def test_policy_code_change_rejected(setup):
    setup[1]['pdf_service_path'].write_text('changed')
    assert execute(setup, ['text'])[-1]['event'] == 'failed'


def test_zero_text_is_distinct(setup):
    result = execute(setup, [None, '', ''])[-1]
    assert result['event'] == 'no_text'
    assert result['snapshot']['extraction_chunk_hashes'] == []


def test_parse_failure_never_completes_and_sanitizes_error(setup):
    events = execute(setup, ['text', RuntimeError('private filename and raw text')])
    assert events[-1]['event'] == 'failed'
    assert not any(event['event'] in ('complete', 'no_text') for event in events)
    assert 'private filename' not in repr(events)


def test_changed_source_during_extraction_rejected(setup):
    path = setup[1]['source_path']
    events = execute(setup, ['text'], reader_factory=reader_for(['text'], lambda: path.write_bytes(b'changed')))
    assert events[-1]['event'] == 'failed'
    assert not any(event['event'] == 'complete' for event in events)


def test_wrong_pending_digest_rejects_resume(setup):
    stream = LegacyChunkDigestStream()
    stream.feed_page('old')
    setup[0]['resume'] = stream.snapshot()
    events = execute(setup, ['new', 'next'])
    assert events[-1]['event'] == 'failed'
    assert not any(event['event'] == 'complete' for event in events)


def test_outside_upload_root_rejected(setup, tmp_path):
    setup[1]['upload_root'] = tmp_path / 'different'
    assert execute(setup, ['text'])[-1]['event'] == 'failed'


def test_disguised_non_pdf_rejected_before_parser(setup):
    request, kwargs = setup
    path = kwargs['source_path']
    path.write_bytes(b'\x89PNG\r\n\x1a\nprivate')
    request.update(source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                   byte_length=path.stat().st_size)
    def forbidden(handle):
        pytest.fail('non-PDF reached parser')
    events = execute(setup, [], reader_factory=forbidden)
    assert events[-1]['reason'] == 'invalid_pdf_header'
    assert 'PNG' not in repr(events)


def test_same_content_source_replacement_rejected(setup):
    path = setup[1]['source_path']
    def replace():
        original = path.read_bytes()
        path.unlink()
        path.write_bytes(original)
    events = execute(setup, [], reader_factory=reader_for(['text'], replace))
    assert events[-1]['event'] == 'failed'
    assert not any(event['event'] == 'complete' for event in events)


@pytest.mark.parametrize('target', ['source', 'progress', 'complete', 'no_text', 'failed', 'resumed'])
def test_collector_failure_propagates_original_without_retry(setup, target):
    request, kwargs = setup
    pages = ['first', 'second']
    if target == 'no_text':
        pages = ['', None]
    if target == 'failed':
        request['policy_digest'] = 'a' * 64
    if target == 'resumed':
        stream = LegacyChunkDigestStream()
        stream.feed_page('first')
        request['resume'] = stream.snapshot()
    original = OSError('private checkpoint write failed')
    observed = []
    def emit(event):
        observed.append(event['event'])
        if event['event'] == target:
            raise original
    with pytest.raises(OSError) as caught:
        run_worker(request, **kwargs, reader_factory=reader_for(pages), emit=emit)
    assert caught.value is original
    assert observed[-1] == target
    assert observed.count(target) == 1
    if target not in ('failed',):
        assert 'failed' not in observed
