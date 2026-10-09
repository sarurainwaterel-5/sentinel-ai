"""Copy a saved legacy catalog/vector export into configured storage, additively.

Run inside the API container with PYTHONPATH=/app/backend. Default is a dry run.
Existing IDs/hashes are preserved; incompatible collisions stop the import.
The export must be captured from one consistent, stopped legacy ingestion session.
"""
import argparse
from collections import Counter
from datetime import datetime
import json
import hashlib
from pathlib import Path

from sqlalchemy import select
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from app.database import SessionLocal
from app.models.document import Document
from app.settings import QDRANT_URL, QDRANT_API_KEY

COLLECTION = "incident_knowledge"


def read_lines(path):
    with path.open() as stream:
        for line in stream:
            yield json.loads(line)


def point_signature(payload, vector):
    stable_payload = {key: value for key, value in payload.items() if key != "status"}
    return hashlib.sha256(json.dumps({"payload": stable_payload, "vector": vector}, sort_keys=True).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("export", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    rows = list(read_lines(args.export / "documents.jsonl"))
    ids = {row["id"] for row in rows}
    source_rows = {row["id"]: row for row in rows}
    if len(ids) != len(rows):
        raise ValueError("Duplicate catalog IDs")
    counts = Counter()
    point_ids = set()
    signatures = {}
    for point in read_lines(args.export / "points.jsonl"):
        if point["id"] in point_ids:
            raise ValueError("Duplicate vector ID")
        point_ids.add(point["id"])
        signatures[str(point["id"])] = point_signature(point["payload"], point["vector"])
        if point["payload"]["document_id"] not in ids:
            raise ValueError("Vector without catalog record")
        counts[point["payload"]["document_id"]] += 1
        if not isinstance(point["vector"], list) or len(point["vector"]) != 384:
            raise ValueError("Unexpected embedding dimensions")
    for row in rows:
        if counts[row["id"]] != row["chunk_count"]:
            raise ValueError(f"Chunk count mismatch for {row['filename']}")
        if row["embedding_model"] != "sentence-transformers/all-MiniLM-L6-v2":
            raise ValueError("Unsupported legacy embedding model")
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=120)
    vectors = client.get_collection(COLLECTION).config.params.vectors
    if vectors.size != 384 or vectors.distance.value != "Cosine":
        raise ValueError("Target collection embedding configuration differs")
    with SessionLocal() as session:
        existing = session.scalars(select(Document)).all()
        by_id = {doc.id: doc for doc in existing}
        by_hash = {doc.file_hash: doc for doc in existing}
        new_rows = []
        for row in rows:
            collision = by_id.get(row["id"]) or by_hash.get(row["file_hash"])
            if collision:
                for key in ("id", "file_hash", "module", "organization_id", "chunk_count", "embedding_model"):
                    if getattr(collision, key) != row[key]:
                        raise ValueError("Incompatible existing catalog record; no overwrite allowed")
            else:
                new_rows.append(row)
        if not new_rows:
            print(json.dumps({"catalog_records": len(rows), "new_documents": 0, "apply": args.apply, "status": "already_imported"}))
            return
        offset = None
        while True:
            points, offset = client.scroll(COLLECTION, limit=256, offset=offset, with_payload=True, with_vectors=True)
            for point in points:
                if str(point.id) in point_ids:
                    if point_signature(point.payload, point.vector) != signatures[str(point.id)]:
                        raise ValueError("Existing vector content differs; no overwrite allowed")
                    source = source_rows.get(point.payload.get("document_id"))
                    if not source or any(point.payload.get(key) != source[key] for key in ("file_hash", "module", "organization_id")):
                        raise ValueError("Existing vector ID collision; no overwrite allowed")
            if offset is None:
                break
        print(json.dumps({"catalog_records": len(rows), "vectors": sum(counts.values()), "new_documents": len(new_rows), "apply": args.apply}), flush=True)
        if not args.apply:
            return
        new_ids = {row["id"] for row in new_rows}
        batch = []
        for point in read_lines(args.export / "points.jsonl"):
            if point["payload"]["document_id"] not in new_ids:
                continue
            payload = dict(point["payload"])
            payload["status"] = source_rows[payload["document_id"]]["status"]
            batch.append(PointStruct(id=point["id"], vector=point["vector"], payload=payload))
            if len(batch) == 256:
                client.upsert(COLLECTION, points=batch, wait=True)
                batch = []
        if batch:
            client.upsert(COLLECTION, points=batch, wait=True)
        for row in new_rows:
            values = dict(row)
            if values.get("uploaded_at"):
                values["uploaded_at"] = datetime.fromisoformat(values["uploaded_at"])
            session.add(Document(**values))
        session.commit()
        print("Import complete. Original identifiers, timestamps, and scope preserved.")


if __name__ == "__main__":
    main()
