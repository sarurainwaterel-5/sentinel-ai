"""Initialize empty stores without replacing existing application data."""
import time
from app.services.qdrant_service import client, create_collection_if_not_exists
from app.services.core_memory_service import create_core_memory_collection, ingest_core_memory, CORE_COLLECTION_NAME
for attempt in range(60):
    try:
        client.get_collections()
        break
    except Exception:
        if attempt == 59:
            raise
        time.sleep(1)
create_collection_if_not_exists()
create_core_memory_collection()
if client.count(collection_name=CORE_COLLECTION_NAME, exact=True).count == 0:
    ingest_core_memory()
print('Vector collections ready.')
