"""Bounded PDF upload storage; client filenames never select disk paths."""
from pathlib import Path
from uuid import uuid4
from fastapi import HTTPException

async def save_pdf_upload(file, directory: Path, max_bytes: int) -> tuple[Path, str]:
    filename = file.filename or ""
    if not filename or "/" in filename or "\\" in filename or "\x00" in filename:
        raise HTTPException(status_code=400, detail="A plain PDF filename is required.")
    if Path(filename).suffix.lower() != ".pdf":
        raise HTTPException(status_code=415, detail="Only PDF documents are supported.")
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid4()}.pdf"
    total = 0
    header = bytearray()
    try:
        with path.open("xb") as buffer:
            while chunk := await file.read(64 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    raise HTTPException(status_code=413, detail="Document exceeds the upload size limit.")
                if len(header) < 5:
                    header.extend(chunk[:5 - len(header)])
                buffer.write(chunk)
        if bytes(header) != b"%PDF-":
            raise HTTPException(status_code=415, detail="The document is not a PDF.")
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path, filename
