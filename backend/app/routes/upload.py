from fastapi import APIRouter, UploadFile, File
from pathlib import Path

from app.services.pdf_service import extract_text_from_pdf
from app.services.chunking_service import chunk_text

router = APIRouter()

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)

    return {
        "filename": file.filename,
        "characters": len(text),
        "chunks": len(chunks),
        "preview": chunks[0][:300] if chunks else ""
    }
