"""Read-only bounded PDF worker; callers enforce process deadlines and isolation."""
import hashlib
import importlib.metadata
import os
from pathlib import Path

from .legacy_chunk_digest_stream import LegacyChunkDigestStream
from .legacy_extraction_checkpoint import checkpoint_key, extraction_policy_digest
from .legacy_source_capture import hash_pdf_source


def _code_digest(path):
    with open(path, 'rb') as handle:
        data = handle.read(1024 * 1024 + 1)
    if len(data) > 1024 * 1024:
        raise ValueError('invalid_policy')
    return hashlib.sha256(data).hexdigest()


def _run_worker(request, *, source_path, upload_root, pdf_service_path,
               chunking_service_path, emit, reader_factory=None, parser_version=None,
               progress_interval_pages=10):
    """Emit digest-only evidence; exceptions become fixed diagnostic codes.

    Resume snapshots must separately be bound by the caller to this exact source
    and policy. The snapshot's pending text is reconstructed from preceding pages.
    No source or checkpoint files are written. Callback failures propagate.
    """
    def send(event, **payload):
        try:
            emit({'event': event, **payload})
        except Exception as error:
            raise _EmissionFailure(error) from None

    try:
        if (type(request) is not dict or request.keys() !=
                {'source_sha256', 'byte_length', 'policy_digest', 'resume'}):
            raise ValueError('invalid_request')
        if type(progress_interval_pages) is not int or not 1 <= progress_interval_pages <= 100:
            raise ValueError('invalid_request')
        key = checkpoint_key(source_sha256=request['source_sha256'],
                             byte_length=request['byte_length'], policy_digest=request['policy_digest'])
        path, root = Path(source_path), Path(upload_root)
        if path.is_symlink() or path.parent.resolve() != root.resolve():
            raise ValueError('invalid_source')
        identity = lambda stat: (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
        before_stat = identity(path.stat(follow_symlinks=False))
        before = hash_pdf_source(path)
        if before != {'sha256': request['source_sha256'], 'byte_length': request['byte_length']}:
            raise ValueError('source_changed')
        version = parser_version if parser_version is not None else importlib.metadata.version('pypdf')
        policy = extraction_policy_digest(pdf_service_sha256=_code_digest(pdf_service_path),
                                           chunking_service_sha256=_code_digest(chunking_service_path),
                                           pypdf_version=version)
        if policy != request['policy_digest']:
            raise ValueError('policy_changed')
    except _EmissionFailure:
        raise
    except Exception:
        send('failed', reason='source_or_policy_validation_failed')
        return
    send('source', checkpoint_key=key, source_sha256=before['sha256'], byte_length=before['byte_length'],
         policy_digest=policy)
    try:
        if reader_factory is None:
            from pypdf import PdfReader
            reader_factory = PdfReader
        # Hold one file descriptor while extracting. Final rehash detects changes
        # to the named source; callers must also preserve the private upload root.
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), 'rb') as handle:
            if identity(os.fstat(handle.fileno())) != before_stat:
                raise ValueError('source_changed')
            if handle.read(5) != b'%PDF-':
                send('failed', checkpoint_key=key, reason='invalid_pdf_header')
                return
            handle.seek(0)
            reader = reader_factory(handle)
            page_count = len(reader.pages)
            if type(page_count) is not int or not 0 <= page_count <= 1_000_000:
                raise ValueError('invalid_page_count')
            resume = request['resume']
            if resume is None:
                stream, start = LegacyChunkDigestStream(), 0
            else:
                if type(resume) is not dict or type(resume.get('page_count')) is not int:
                    raise ValueError('invalid_resume')
                start = resume['page_count']
                needed = resume.get('pending_length')
                if not 0 <= start <= page_count or type(needed) is not int or not 0 <= needed < 1000:
                    raise ValueError('invalid_resume')
                pending = ''
                for index in range(start - 1, -1, -1):
                    if len(pending) >= needed:
                        break
                    text = reader.pages[index].extract_text()
                    if text is not None and type(text) is not str:
                        raise ValueError('invalid_page')
                    if text:
                        pending = (text + '\n')[-(needed - len(pending)):] + pending
                stream = LegacyChunkDigestStream.restore(resume, pending_text=pending)
                send('resumed', checkpoint_key=key, snapshot=stream.snapshot())
            for index in range(start, page_count):
                stream.feed_page(reader.pages[index].extract_text())
                if (index + 1) % progress_interval_pages == 0:
                    send('progress', checkpoint_key=key, snapshot=stream.snapshot())
            if (hash_pdf_source(path) != before
                    or identity(os.fstat(handle.fileno())) != before_stat
                    or identity(path.stat(follow_symlinks=False)) != before_stat):
                raise ValueError('source_changed')
            result = stream.finalize()
            send('complete' if result['chunk_count'] else 'no_text', checkpoint_key=key,
                 source_sha256=before['sha256'], byte_length=before['byte_length'],
                 policy_digest=policy, snapshot=result)
    except _EmissionFailure:
        raise
    except Exception:
        send('failed', checkpoint_key=key, reason='extraction_or_resume_failed')


class _EmissionFailure(Exception):
    """Internal marker keeps collector failures out of extraction diagnostics."""
    def __init__(self, original):
        self.original = original
        super().__init__()


def run_worker(request, *, source_path, upload_root, pdf_service_path,
               chunking_service_path, emit, reader_factory=None, parser_version=None,
               progress_interval_pages=10):
    """Run read-only extraction; propagate the original collector exception."""
    try:
        return _run_worker(request, source_path=source_path, upload_root=upload_root,
                           pdf_service_path=pdf_service_path,
                           chunking_service_path=chunking_service_path, emit=emit,
                           reader_factory=reader_factory, parser_version=parser_version,
                           progress_interval_pages=progress_interval_pages)
    except _EmissionFailure as failure:
        raise failure.original from None
