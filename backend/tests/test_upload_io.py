import asyncio
from io import BytesIO
from fastapi import UploadFile, HTTPException
import pytest
from app.services.upload_io import save_pdf_upload


def save(tmp_path, filename, body, limit=1024):
    return asyncio.run(save_pdf_upload(UploadFile(filename=filename, file=BytesIO(body)), tmp_path, limit))

@pytest.mark.parametrize("name", ["../escape.pdf", "/tmp/escape.pdf", "..\\escape.pdf", "", "bad\x00.pdf"])
def test_client_cannot_choose_storage_path(tmp_path, name):
    with pytest.raises(HTTPException) as error:
        save(tmp_path, name, b"%PDF-1.4")
    assert error.value.status_code == 400
    assert not list(tmp_path.iterdir())

@pytest.mark.parametrize("name,body,status", [("notes.txt", b"hello", 415), ("fake.pdf", b"hello", 415), ("empty.pdf", b"", 415), ("large.pdf", b"%PDF-" + b"x" * 1024, 413)])
def test_rejected_upload_leaves_no_file(tmp_path, name, body, status):
    with pytest.raises(HTTPException) as error:
        save(tmp_path, name, body)
    assert error.value.status_code == status
    assert not list(tmp_path.iterdir())


def test_same_filename_does_not_overwrite_existing_document(tmp_path):
    first, name = save(tmp_path, "report.pdf", b"%PDF-first")
    second, _ = save(tmp_path, "report.pdf", b"%PDF-second")
    assert name == "report.pdf"
    assert first != second
    assert first.read_bytes() == b"%PDF-first"
    assert second.read_bytes() == b"%PDF-second"
