from uuid import uuid4
from pathlib import Path

from fastapi import APIRouter, UploadFile, File

from app.services.pdf_service import extract_text_from_pdf
from app.services.chunking_service import chunk_text
from app.services.qdrant_service import store_chunks

router = APIRouter()

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    document_id = str(uuid4())
    file_path = f"{UPLOAD_DIR}/{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    text = extract_text_from_pdf(file_path)
    chunks = chunk_text(text)

    stored_vectors = store_chunks(
        document_id=document_id,
        filename=file.filename,
        chunks=chunks
    )

    return {
        "document_id": document_id,
        "filename": file.filename,
        "characters": len(text),
        "chunks": len(chunks),
        "stored_vectors": stored_vectors,
        "preview": chunks[0][:300] if chunks else ""
    }
