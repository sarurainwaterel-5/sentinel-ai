import json
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.services import media_extraction as media


@pytest.mark.parametrize('name,content', [('a.txt', 'hello'), ('a.md', '# title'),
    ('a.csv', 'a,b\n1,2'), ('a.json', '{"ok":true}')])
def test_text_formats(tmp_path, name, content):
    source = tmp_path / 'retained'
    source.write_text(content)
    result = media.extract_source_text(source, name)
    assert result['text'] == content
    assert result['extraction_method'] == 'utf8_text'
    assert result['warnings'] == []


@pytest.mark.parametrize('content', [b'\xff', b'hello\x00world', b'{broken'])
def test_invalid_text_is_sanitized(tmp_path, content):
    source = tmp_path / 'retained'
    source.write_bytes(content)
    with pytest.raises(HTTPException) as error:
        media.extract_source_text(source, 'private.json')
    assert error.value.status_code == 422
    assert str(source) not in error.value.detail


def test_missing_tools_503(tmp_path, monkeypatch):
    source = tmp_path / 'source'
    source.write_bytes(b'image')
    monkeypatch.setattr(media.shutil, 'which', lambda tool: None)
    with pytest.raises(HTTPException) as error:
        media.extract_source_text(source, 'a.png')
    assert error.value.status_code == 503


def test_command_contract_bounds_cpu_memory_output_and_no_shell(monkeypatch):
    monkeypatch.setattr(media.shutil, 'which', lambda tool: '/usr/bin/' + tool)
    observed = []
    def run(command, **kwargs):
        observed.append((command, kwargs))
        kwargs['stdout'].write(b'bounded text')
    monkeypatch.setattr(media.subprocess, 'run', run)
    assert media._run(['tesseract', 'local.png', 'stdout'], timeout=7) == b'bounded text'
    command, kwargs = observed[0]
    assert command[:4] == ['prlimit', '--cpu=60', '--as=2147483648', '--fsize=8388608']
    assert command[4] == '--'
    assert kwargs['timeout'] == 7
    assert kwargs['stdin'] == subprocess.DEVNULL
    assert kwargs['stderr'] == subprocess.DEVNULL
    assert 'shell' not in kwargs


def test_command_timeout_sanitized(monkeypatch):
    monkeypatch.setattr(media.shutil, 'which', lambda tool: tool)
    def run(*args, **kwargs):
        raise subprocess.TimeoutExpired('private command', 1)
    monkeypatch.setattr(media.subprocess, 'run', run)
    with pytest.raises(HTTPException) as error:
        media._run(['ffmpeg', 'private path'])
    assert 'private' not in error.value.detail


def test_video_samples_visual_text_with_explicit_limits(tmp_path, monkeypatch):
    source = tmp_path / 'video'
    source.write_bytes(b'video')
    commands = []
    monkeypatch.setattr(media, '_require', lambda *args: None)
    def run(command, **kwargs):
        commands.append(command)
        if command[0] == 'ffprobe':
            return json.dumps({'format': {'duration': '90'},
                               'streams': [{'codec_type': 'video', 'width': 1920, 'height': 1080}]}).encode()
        return b''
    monkeypatch.setattr(media, '_run', run)
    monkeypatch.setattr(media, '_ocr', lambda path: ('visible words', {}))
    progress = []
    result = media.extract_source_text(source, 'movie.mp4', progress.append)
    assert result['metadata']['sampled_frames'] == 3
    assert 'video_has_no_audio_track' in result['warnings']
    assert 'embedded_subtitles_not_extracted' in result['warnings']
    assert '[Video frame at 30.000 seconds]' in result['text']
    assert len(progress) == 3
    for command in commands:
        assert command[command.index('-protocol_whitelist') + 1] == 'file,pipe'
        assert command[command.index('-format_whitelist') + 1] == 'mov,matroska,webm'
        if command[0] == 'ffmpeg':
            assert '-an' in command and '-sn' in command
            assert command[command.index('-frames:v') + 1] == '1'
            assert '1280' in command[command.index('-vf') + 1]


@pytest.mark.parametrize('duration', ['nan', 'inf', '-1', '7201', 'unknown'])
def test_video_duration_bounds(tmp_path, monkeypatch, duration):
    source = tmp_path / 'movie'
    source.write_bytes(b'video')
    monkeypatch.setattr(media, '_require', lambda *args: None)
    monkeypatch.setattr(media, '_run', lambda *args, **kwargs: json.dumps({
        'format': {'duration': duration}, 'streams': [{'codec_type': 'video'}]}).encode())
    with pytest.raises(HTTPException) as error:
        media.extract_source_text(source, 'a.webm')
    assert error.value.status_code == 422


def test_blank_video_retained_as_no_readable_text(tmp_path, monkeypatch):
    source = tmp_path / 'movie'
    source.write_bytes(b'video')
    monkeypatch.setattr(media, '_require', lambda *args: None)
    monkeypatch.setattr(media, '_run', lambda *args, **kwargs: json.dumps({
        'format': {'duration': 1}, 'streams': [{'codec_type': 'video', 'width': 32, 'height': 32}]}).encode())
    monkeypatch.setattr(media, '_ocr', lambda path: ('', {}))
    result = media.extract_source_text(source, 'a.mov')
    assert result['text'] == ''
    assert 'video_has_no_readable_sampled_text' in result['warnings']


def test_actual_image_decode_with_fake_ocr_command(tmp_path, monkeypatch):
    image_module = pytest.importorskip('PIL.Image')
    source = tmp_path / 'picture.png'
    image_module.new('RGB', (64, 32), 'white').save(source)
    monkeypatch.setattr(media, '_require', lambda *args: None)
    monkeypatch.setattr(media, '_run', lambda *args, **kwargs: b'local OCR words')
    result = media.extract_source_text(source, 'picture.png')
    assert result['text'] == 'local OCR words'
    assert result['metadata'] == {'width': 64, 'height': 32}
    assert source.exists()


def test_video_empty_seek_cannot_reuse_previous_frame(tmp_path, monkeypatch):
    source = tmp_path / 'movie'
    source.write_bytes(b'video')
    monkeypatch.setattr(media, '_require', lambda *args: None)
    samples = []
    def run(command, **kwargs):
        if command[0] == 'ffprobe':
            return json.dumps({'format': {'duration': 60}, 'streams': [
                {'codec_type': 'video', 'width': 32, 'height': 32}]}).encode()
        if not samples:
            Path(command[-1]).write_bytes(b'first frame')
        return b''
    def ocr(path):
        if not path.exists():
            raise HTTPException(422, 'No frame was decoded.')
        samples.append(path.read_bytes())
        return 'first frame text', {}
    monkeypatch.setattr(media, '_run', run)
    monkeypatch.setattr(media, '_ocr', ocr)
    with pytest.raises(HTTPException) as error:
        media.extract_source_text(source, 'movie.mp4')
    assert error.value.status_code == 422
    assert samples == [b'first frame']


@pytest.mark.parametrize('width,height', [(-32, -32), (0, 32), (32, -32)])
def test_video_dimensions_must_each_be_positive(tmp_path, monkeypatch, width, height):
    source = tmp_path / 'movie'
    source.write_bytes(b'video')
    monkeypatch.setattr(media, '_require', lambda *args: None)
    monkeypatch.setattr(media, '_run', lambda *args, **kwargs: json.dumps({
        'format': {'duration': 1}, 'streams': [
            {'codec_type': 'video', 'width': width, 'height': height}]}).encode())
    with pytest.raises(HTTPException) as error:
        media.extract_source_text(source, 'movie.mp4')
    assert error.value.status_code == 422


@pytest.mark.parametrize('output', [b'page one\npage two\n', b''])
def test_pdf_uses_isolated_bounded_child_and_preserves_no_text_notice(tmp_path, monkeypatch, output):
    source = tmp_path / 'private.pdf'
    source.write_bytes(b'%PDF-test')
    observed = []
    def run(arguments, **kwargs):
        observed.append((arguments, kwargs))
        return output
    monkeypatch.setattr(media, '_run', run)
    result = media.extract_source_text(source, 'document.pdf')
    arguments, options = observed[0]
    assert arguments[:3] == [sys.executable, '-I', '-c']
    assert 'from pypdf import PdfReader' in arguments[3]
    assert 'from app' not in arguments[3]
    assert arguments[4:] == [str(source), str(media.MAX_PDF_TEXT_BYTES)]
    assert options == {'timeout': 60, 'output_limit': media.MAX_PDF_TEXT_BYTES}
    assert result['text'] == output.decode()
    assert result['warnings'] == ([] if output else ['pdf_has_no_extractable_text_ocr_not_applied'])


def test_pdf_child_output_limit_failure_cannot_return_partial_text(tmp_path, monkeypatch):
    source = tmp_path / 'private.pdf'
    source.write_bytes(b'%PDF-test')
    monkeypatch.setattr(media.shutil, 'which', lambda tool: tool)
    def run(command, **kwargs):
        kwargs['stdout'].write(b'partial page text')
        raise subprocess.CalledProcessError(1, command)
    monkeypatch.setattr(media.subprocess, 'run', run)
    with pytest.raises(HTTPException) as error:
        media.extract_source_text(source, 'document.pdf')
    assert error.value.status_code == 422
    assert 'private' not in error.value.detail
    assert 'partial' not in error.value.detail


def test_pdf_actual_child_blank_result(tmp_path):
    pytest.importorskip('pypdf')
    from pypdf import PdfWriter
    source = tmp_path / 'blank.pdf'
    writer = PdfWriter()
    writer.add_blank_page(width=72, height=72)
    with source.open('wb') as output:
        writer.write(output)
    result = media.extract_source_text(source, 'blank.pdf')
    assert result['text'] == ''
    assert result['warnings'] == ['pdf_has_no_extractable_text_ocr_not_applied']


def test_pdf_actual_child_text_and_output_bound(tmp_path):
    pytest.importorskip('pypdf')
    from pypdf import PdfWriter
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
    source = tmp_path / 'text.pdf'
    writer = PdfWriter()
    page = writer.add_blank_page(width=200, height=200)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
        NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
        DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    content = DecodedStreamObject()
    content.set_data(b'BT /F1 12 Tf 10 100 Td (bounded child text) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(content)
    with source.open('wb') as output:
        writer.write(output)
    result = media.extract_source_text(source, 'text.pdf')
    assert result['text'] == 'bounded child text\n'
    with pytest.raises(HTTPException) as error:
        media._run([sys.executable, '-I', '-c', media._PDF_EXTRACT_SCRIPT,
                    str(source), '1'], output_limit=1)
    assert error.value.status_code == 422
