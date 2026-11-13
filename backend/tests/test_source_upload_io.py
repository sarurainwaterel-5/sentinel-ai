import asyncio
from io import BytesIO
import pytest
from fastapi import UploadFile, HTTPException
from app.services.source_upload_io import save_source_upload, validate_relative_path, source_limit


def save(tmp_path, name, body, limit=1024):
    return asyncio.run(save_source_upload(UploadFile(filename=name, file=BytesIO(body)), tmp_path, limit))


@pytest.mark.parametrize('name,body', [('image.png', b'\x89PNG\r\n\x1a\nbody'), ('clip.mp4', b'\0\0\0\x18ftypisom'), ('notes.txt', b'hello'), ('archive.zip', b'PKopaque')])
def test_accepted_sources_use_unique_flat_storage(tmp_path, name, body):
    first, original = save(tmp_path, name, body)
    second, _ = save(tmp_path, name, body)
    assert original == name and first != second
    assert first.parent == tmp_path and first.read_bytes() == body
    if name.endswith('.zip'):
        assert first.suffix == '.bin'


@pytest.mark.parametrize('name,body,status', [('bad.png', b'fake', 415), ('bad.mp4', b'fake', 415), ('empty.txt', b'', 422), ('big.txt', b'x'*1025, 413), ('../bad.txt', b'hello', 400)])
def test_rejected_sources_leave_no_partial_file(tmp_path, name, body, status):
    with pytest.raises(HTTPException) as error:
        save(tmp_path, name, body)
    assert error.value.status_code == status
    assert not list(tmp_path.iterdir())


@pytest.mark.parametrize('path', ['/folder/a.txt', '../a.txt', 'folder/../a.txt', 'folder//a.txt', 'C:/a.txt', 'folder\\a.txt', 'folder/other.txt'])
def test_folder_paths_cannot_escape_or_mislabel_source(path):
    with pytest.raises(HTTPException):
        validate_relative_path(path, 'a.txt')


def test_folder_metadata_and_format_caps():
    assert validate_relative_path('reports/november/a.txt', 'a.txt') == 'reports/november/a.txt'
    assert source_limit('photo.png', 1024**3) == 32*1024**2
    assert source_limit('notes.txt', 1024**3) == 16*1024**2
    assert source_limit('movie.mp4', 1024**3) == 1024**3
