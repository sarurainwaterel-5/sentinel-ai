"""Explicit SDK adapter for a separate governed collection, no legacy fallback.

Caller supplies a bounded QdrantClient and reviewed collection identity. No
startup registration, automatic reuse, deletion of collections or model calls.
"""
import re
import uuid
from qdrant_client import models
from evaluation.governed_answers.versioned_manifests import MAX_CHUNKS,PAGE_SIZE


class GovernedQdrantIndex:
    def __init__(self, client, *, collection, dimension):
        if type(collection) is not str or re.fullmatch(r'governed_v2_[a-z0-9_]{1,80}',collection) is None:
            raise ValueError('separate_governed_collection_required')
        if type(dimension) is not int or not 1<=dimension<=4096:
            raise ValueError('bounded_dimension_required')
        self.client,self.collection,self.dimension=client,collection,dimension

    def initialize(self):
        # Never adopt an existing collection solely on a matching display name.
        if self.client.collection_exists(self.collection):
            raise ValueError('explicit_collection_adoption_review_required')
        if not self.client.create_collection(collection_name=self.collection,
                vectors_config=models.VectorParams(size=self.dimension,distance=models.Distance.COSINE)):
            raise ValueError('collection_creation_failed')

    @staticmethod
    def _filter(document_id):
        if type(document_id) is not str or not document_id.strip() or len(document_id)>200:
            raise ValueError('invalid_document_identity')
        return models.Filter(must=[models.FieldCondition(key='document_id',match=models.MatchValue(value=document_id))])

    def begin_replace(self,document_id):
        self.client.delete(collection_name=self.collection,points_selector=models.FilterSelector(
            filter=self._filter(document_id)),wait=True)

    def upsert_batch(self,points):
        if type(points) is not list or not 1<=len(points)<=PAGE_SIZE:
            raise ValueError('bounded_index_batch_required')
        self.client.upsert(collection_name=self.collection,
            points=[models.PointStruct(**p) for p in points],wait=True)

    def replace(self,document_id,points):
        self.begin_replace(document_id)
        for start in range(0,len(points),PAGE_SIZE):self.upsert_batch(points[start:start+PAGE_SIZE])

    def read_all(self,document_id,*,progress=None):
        result=[];offset=None;seen_offsets=set();seen_ids=set()
        for _ in range((MAX_CHUNKS+PAGE_SIZE-1)//PAGE_SIZE):
            if progress is not None: progress()
            rows,next_offset=self.client.scroll(collection_name=self.collection,scroll_filter=self._filter(document_id),
                limit=PAGE_SIZE,offset=offset,with_payload=True,with_vectors=False)
            if progress is not None: progress()
            if type(rows) is not list or len(rows)>PAGE_SIZE:raise ValueError('invalid_index_page')
            for row in rows:
                point_id=str(row.id)
                uuid.UUID(point_id)
                if point_id in seen_ids or type(row.payload) is not dict:
                    raise ValueError('invalid_or_duplicate_index_point')
                seen_ids.add(point_id);result.append(dict(id=point_id,payload=row.payload))
            if len(result)>MAX_CHUNKS:raise ValueError('index_manifest_over_limit')
            if next_offset is None:return result
            offset=str(next_offset);uuid.UUID(offset)
            if not rows or offset in seen_offsets:raise ValueError('invalid_index_cursor')
            seen_offsets.add(offset)
        raise ValueError('index_page_budget')
