import os
import uuid
from types import SimpleNamespace
import pytest
from app.services.governed_qdrant_index import GovernedQdrantIndex

@pytest.mark.parametrize('collection',['incident_knowledge','sentinel_core_memory','governed_v2_../x',None])
def test_legacy_or_invalid_collection_denied_before_io(collection):
    with pytest.raises(ValueError):GovernedQdrantIndex(None,collection=collection,dimension=4)

def test_existing_collection_requires_explicit_adoption():
    index=GovernedQdrantIndex(SimpleNamespace(collection_exists=lambda _:True),collection='governed_v2_test',dimension=4)
    with pytest.raises(ValueError,match='adoption'):index.initialize()

def test_duplicate_paged_point_rejected():
    point=SimpleNamespace(id=str(uuid.uuid4()),payload={})
    pages=iter([([point],str(uuid.uuid4())),([point],None)])
    client=SimpleNamespace(scroll=lambda **_:next(pages))
    with pytest.raises(ValueError,match='duplicate'):
        GovernedQdrantIndex(client,collection='governed_v2_test',dimension=4).read_all('document')

def test_actual_sdk_index_full_pagination_and_document_delete():
    url=os.getenv('SENTINEL_ISOLATED_QDRANT_URL')
    if not url:pytest.skip('explicit disposable Qdrant required')
    # Test code refuses installed/default endpoints before creating a collection.
    from evaluation.governed_answers.postgres_qdrant_rehearsal import _Index
    _Index(url)
    from qdrant_client import QdrantClient
    collection='governed_v2_test_'+uuid.uuid4().hex
    client=QdrantClient(url=url,timeout=10,check_compatibility=False)
    index=GovernedQdrantIndex(client,collection=collection,dimension=4)
    try:
        index.initialize()
        points=[dict(id=str(uuid.uuid4()),vector=[1.,0.,0.,0.],payload=dict(document_id='document',chunk_index=i)) for i in range(257)]
        index.replace('document',points)
        observed=index.read_all('document')
        assert len(observed)==257
        assert {p['id']:p['payload'] for p in observed}=={p['id']:p['payload'] for p in points}
        index.begin_replace('document');assert index.read_all('document')==[]
    finally:
        client.delete_collection(collection_name=collection);client.close()
