import hashlib
import time
from pathlib import Path
from uuid import uuid4
import json
from datetime import datetime

from qdrant_client.models import Distance, VectorParams, PointStruct

from app.services.qdrant_service import client
from app.services.embedding_service import EmbeddingService
from app.services.chunking_service import chunk_text
from app.services.core_memory_service import CORE_COLLECTION_NAME


class ConstitutionBuilderService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.project_root = Path(__file__).resolve().parents[4]

        self.source_paths = [
            self.project_root / "docs" / "philosophy",
            self.project_root / "docs" / "design",
            self.project_root / "docs" / "architecture" / "decisions",
        ]

    def rebuild_constitution(self):
        start_time = time.time()

        documents = self._load_documents()
        validation = self._validate_documents(documents)
        constitution_hash = self._calculate_constitution_hash(documents)

        self._replace_collection()

        points = []
        chunk_count = 0

        for document in documents:
            chunks = chunk_text(document["content"])
            chunk_count += len(chunks)

            for index, chunk in enumerate(chunks):
                points.append(
                    PointStruct(
                        id=str(uuid4()),
                        vector=self.embedding_service.generate_embedding(chunk),
                        payload={
                            "memory_type": "core",
                            "authority": "constitutional",
                            "immutable": True,
                            "priority": 100,
                            "constitution_hash": constitution_hash,
                            "source_file": document["relative_path"],
                            "chunk_index": index,
                            "text": chunk,
                        },
                    )
                )

        if points:
            client.upsert(
                collection_name=CORE_COLLECTION_NAME,
                points=points,
            )

        build_time = round(time.time() - start_time, 2)
        manifest = {
            "constitution_version": "1.0",
            "constitution_hash": constitution_hash,
            "collection": CORE_COLLECTION_NAME,
            "documents_processed": len(documents),
            "chunks_embedded": chunk_count,
            "validation": validation,
            "build_time_seconds": build_time,
            "built_at": datetime.utcnow().isoformat(),
            "builder": "ConstitutionBuilderService",
            "status": "healthy" if validation["status"] == "healthy" else "incomplete",
        }

        self._write_manifest(manifest)

        return {
            "status": "constitution_rebuilt",
            "message": "SentinelAI Constitution rebuilt successfully.",
            **manifest,
        }

    def _load_documents(self):
        documents = []

        for source_path in self.source_paths:
            if not source_path.exists():
                continue

            for file_path in sorted(source_path.glob("*.md")):
                content = file_path.read_text(encoding="utf-8")

                documents.append(
                    {
                        "path": file_path,
                        "relative_path": str(file_path.relative_to(self.project_root)),
                        "content": content,
                    }
                )

        return documents

    def _validate_documents(self, documents):
        found_files = {document["path"].name for document in documents}

        required_files = {
            "VISION.md",
            "MANIFESTO.md",
            "BUILDERS_OATH.md",
            "ENGINEERING_PRINCIPLES.md",
            "LANGUAGE_GUIDE.md",
            "COGNITIVE_DESIGN_PRINCIPLES.md",
        }

        missing = sorted(required_files - found_files)

        return {
            "status": "healthy" if not missing else "incomplete",
            "required_files": sorted(required_files),
            "missing_files": missing,
        }

    def _calculate_constitution_hash(self, documents):
        sha256 = hashlib.sha256()

        for document in documents:
            sha256.update(document["relative_path"].encode("utf-8"))
            sha256.update(document["content"].encode("utf-8"))

        return sha256.hexdigest()

    def _write_manifest(self, manifest):
        manifest_path = self.project_root / "docs" / "architecture" / "constitution-build-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8"
        )

    def _replace_collection(self):
        collections = client.get_collections().collections
        existing = [collection.name for collection in collections]

        if CORE_COLLECTION_NAME in existing:
            client.delete_collection(collection_name=CORE_COLLECTION_NAME)

        client.create_collection(
            collection_name=CORE_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=self.embedding_service.get_dimension(),
                distance=Distance.COSINE,
            ),
        )
