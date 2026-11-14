import json
import subprocess
import pytest
from pypdf import PdfWriter
from app.services import operator_pdf_extraction as extraction


def setup(tmp_path):
    source=tmp_path/'source.pdf'
    writer=PdfWriter(); writer.add_blank_page(width=100,height=100)
    with source.open('wb') as stream: writer.write(stream)
    private=tmp_path/'private'; private.mkdir(mode=0o700)
    return source,private


def test_real_blank_page_complete_and_resumable(tmp_path,monkeypatch):
    source,private=setup(tmp_path)
    first=extraction.extract(source,private)
    assert first['page_count']==1 and first['text_byte_length']==0
    assert first['pages']==[{'page':0,'byte_length':0,'sha256':extraction._sha(b'')}]
    assert (private/'manifest.complete.json').stat().st_mode&0o777==0o600
    original=extraction._run; calls=[]
    def run(source,directory,start,stop):
        calls.append(start); return original(source,directory,start,stop)
    monkeypatch.setattr(extraction,'_run',run)
    assert extraction.extract(source,private)==first
    assert calls==[-1]


def test_modified_page_is_rejected(tmp_path):
    source,private=setup(tmp_path); extraction.extract(source,private)
    page=private/'page-00000.json'; value=json.loads(page.read_text()); value['text']='changed'
    page.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='page_checkpoint_invalid'): extraction.extract(source,private)


def test_source_identity_drift_rejects_old_checkpoint(tmp_path):
    source,private=setup(tmp_path); extraction.extract(source,private)
    source.write_bytes(source.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='checkpoint_binding_changed'): extraction.extract(source,private)


def test_worker_timeout_never_completes(tmp_path,monkeypatch):
    source,private=setup(tmp_path)
    def fail(*args): raise subprocess.TimeoutExpired('worker',60)
    monkeypatch.setattr(extraction,'_run',fail)
    with pytest.raises(subprocess.TimeoutExpired): extraction.extract(source,private)
    assert not (private/'manifest.complete.json').exists()


def test_changed_limits_invalidate_policy(tmp_path,monkeypatch):
    source,private=setup(tmp_path); extraction.extract(source,private)
    monkeypatch.setattr(extraction,'MAX_TEXT',-1)
    with pytest.raises(ValueError,match='checkpoint_binding_changed'): extraction.extract(source,private)


def test_rejects_public_directory_and_symlink_source(tmp_path):
    source,private=setup(tmp_path); private.chmod(0o755)
    with pytest.raises(ValueError,match='private_directory_required'): extraction.extract(source,private)
    private.chmod(0o700); linked=tmp_path/'linked.pdf'; linked.symlink_to(source)
    with pytest.raises(OSError): extraction.extract(linked,private)


def test_aggregate_output_limit_no_complete_manifest(tmp_path,monkeypatch):
    source,private=setup(tmp_path)
    monkeypatch.setattr(extraction,'MAX_TEXT',1)
    def worker(source,work,start,stop):
        if start==-1: (work/'count').write_text('1')
        else: (work/'0.txt').write_text('xx')
    monkeypatch.setattr(extraction,'_run',worker)
    with pytest.raises(ValueError,match='aggregate_text_exceeded'): extraction.extract(source,private)
    assert not (private/'manifest.complete.json').exists()


def test_subprocess_has_hard_timeout_and_no_stream_capture(tmp_path,monkeypatch):
    def run(command,**options):
        assert command[1:3]==['-m','app.services.operator_pdf_extraction']
        assert options['timeout']==60
        assert options['stdout']==options['stderr']==subprocess.DEVNULL
        assert options['preexec_fn'] is extraction._limits
        raise subprocess.TimeoutExpired(command,60)
    monkeypatch.setattr(extraction.subprocess,'run',run)
    with pytest.raises(subprocess.TimeoutExpired): extraction._run(tmp_path/'source',tmp_path,0,16)
