from pathlib import Path
from uuid import uuid4

from app.database import SessionLocal
from app.repositories.document_repository import DocumentRepository
from app.services.fingerprint_service import FingerprintService
from app.services.pdf_service import extract_text_from_pdf
from app.services.chunking_service import chunk_text
from app.services.embedding_service import EmbeddingService

UPLOAD_DIR = Path("uploads")
DEFAULT_COLLECTION = "engineering"

db = SessionLocal()
repo = DocumentRepository(db)
embedding_service = EmbeddingService()

added = 0
skipped = 0

try:
    for pdf_path in UPLOAD_DIR.glob("*.pdf"):
        file_hash = FingerprintService.calculate_sha256(str(pdf_path))
        existing = repo.get_by_hash(file_hash)

        if existing:
            print(f"SKIP duplicate: {pdf_path.name}")
            skipped += 1
            continue

        try:
            text = extract_text_from_pdf(str(pdf_path))
            chunks = chunk_text(text)

            repo.create_document(
                document_id=str(uuid4()),
                filename=pdf_path.name,
                file_hash=file_hash,
                collection=DEFAULT_COLLECTION,
                description="Backfilled from uploads folder",
                chunk_count=len(chunks),
                embedding_model=embedding_service.get_model_name(),
                status="indexed",
                organization_id="default",
            )

            print(f"ADDED: {pdf_path.name} | chunks={len(chunks)}")
            added += 1

        except Exception as error:
            print(f"FAILED: {pdf_path.name} | {error}")

finally:
    db.close()

print("\nBackfill complete.")
print(f"Added: {added}")
print(f"Skipped: {skipped}")
