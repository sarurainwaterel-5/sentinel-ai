"""Paged governed index rehearsal; no production embedding or answer authority."""
import math
import time
import hashlib
import uuid

from .versioned_manifests import Version,Locator,manifest_digest,MAX_CHUNKS,PAGE_SIZE
from .live_provider_rehearsal import canonical
from .postgres_qdrant_rehearsal import _Index

MAX_TEXT_BYTES=64*1024*1024
MAX_SELECTED_CHUNKS=128


class ReconciliationDenied(ValueError):
    pass


class FixtureVectorAdapter:
    """Explicit constant fixture; no embedding, retrieval-quality or model claim."""
    dimension=4
    model_name='synthetic-constant-four-dimensional-v1'
    policy_sha256=hashlib.sha256(model_name.encode()).hexdigest()
    def embed(self,texts):return [[1.0,0.0,0.0,0.0] for _ in texts]


class GovernedRehearsalIndex:
    def __init__(self,url,*,collection,dimension=4):
        if not collection.startswith('sentinel_s21_v2_') or len(collection)!=len('sentinel_s21_v2_')+32:
            raise ValueError('dedicated_collection_required')
        uuid.UUID(hex=collection.removeprefix('sentinel_s21_v2_'))
        if type(dimension) is not int or not 1<=dimension<=4096:raise ValueError('bounded_dimension_required')
        self.http,self.collection,self.dimension=_Index(url),collection,dimension

    def initialize(self):
        self.http.call('PUT','/collections/'+self.collection,{'vectors':{'size':self.dimension,'distance':'Cosine'}})

    def begin_replace(self,document_id):
        self.http.call('POST','/collections/'+self.collection+'/points/delete?wait=true',{'filter':{'must':[{'key':'document_id','match':{'value':document_id}}]}})

    def upsert_batch(self,points):
        if not 1<=len(points)<=PAGE_SIZE:raise ReconciliationDenied('bounded_index_batch_required')
        self.http.call('PUT','/collections/'+self.collection+'/points?wait=true',{'points':points})

    def replace(self,document_id,points):
        self.begin_replace(document_id)
        for start in range(0,len(points),PAGE_SIZE):self.upsert_batch(points[start:start+PAGE_SIZE])

    def read_all(self,document_id,*,progress=None):
        """Complete bounded readback; never interpret one page as a manifest."""
        points,offset,seen_cursors,seen_ids=[],None,set(),set()
        for _ in range((MAX_CHUNKS+PAGE_SIZE-1)//PAGE_SIZE):
            if progress is not None:progress()
            body={'filter':{'must':[{'key':'document_id','match':{'value':document_id}}]},'limit':PAGE_SIZE,'with_payload':True,'with_vector':False}
            if offset is not None:body['offset']=offset
            result=self.http.call('POST','/collections/'+self.collection+'/points/scroll',body)
            if progress is not None:progress()
            page=result['points']
            if type(page) is not list or len(page)>PAGE_SIZE:raise ReconciliationDenied('invalid_index_page')
            for point in page:
                point_id=point.get('id')
                if type(point_id) is not str or point_id in seen_ids:raise ReconciliationDenied('duplicate_or_invalid_index_id')
                uuid.UUID(point_id)
                seen_ids.add(point_id)
            points.extend(page)
            if len(points)>MAX_CHUNKS:raise ReconciliationDenied('oversized_manifest')
            offset=result.get('next_page_offset')
            if offset is None:return points
            if type(offset) is not str or not page or offset in seen_cursors:raise ReconciliationDenied('invalid_index_cursor')
            uuid.UUID(offset);seen_cursors.add(offset)
        raise ReconciliationDenied('index_page_budget')

    def destroy(self):self.http.call('DELETE','/collections/'+self.collection)


class CatalogIndexReconciler:
    """Full paged immutable verification and exact still-current SQL ack.

    Vector adapters are explicit synchronous bounded capabilities: embed(text)
    returns finite vectors matching dimension, policy_sha256 identifies configuration.
    No provider is constructed or paid call made by this module. The default is
    visibly a fixture. Request/semantic context selects explicit chunk locators
    only after verifying the complete index, never truncating index validation.
    """
    def __init__(self,writer,*,chunk_store,index,vector_adapter=None):
        self.writer,self.chunk_store,self.index=writer,chunk_store,index
        self.vector_adapter=vector_adapter or FixtureVectorAdapter()
        self._clock=time.monotonic
        self._vector_binding=self._configuration()
        if index is not None and index.dimension!=self.vector_adapter.dimension:raise ReconciliationDenied('index_dimension_mismatch')

    def _configuration(self):
        adapter=self.vector_adapter
        if type(adapter.dimension) is not int or not 1<=adapter.dimension<=4096 or type(adapter.model_name) is not str or not 1<=len(adapter.model_name)<=200 or type(adapter.policy_sha256) is not str or len(adapter.policy_sha256)!=64 or any(c not in '0123456789abcdef' for c in adapter.policy_sha256):
            raise ReconciliationDenied('invalid_vector_configuration')
        return canonical(dict(dimension=adapter.dimension,model_name=adapter.model_name,policy_sha256=adapter.policy_sha256))

    def _snapshot(self,document_id,*,require_active,progress=None):
        with self.writer.transaction() as cursor:
            cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            cursor.execute('SELECT * FROM documents WHERE document_id=%s',(document_id,))
            document=cursor.fetchone()
            if document is None or (require_active and document['state']!='active'):raise ReconciliationDenied('inactive_document')
            document=dict(document)
            cursor.execute('SELECT * FROM versions WHERE version_id=%s',(document['version_id'],))
            stored=cursor.fetchone()
            binding=dict(stored['binding_json']);binding['scope']=tuple(binding['scope'])
            version=Version(**binding);version.validate()
            if not 1<=version.chunk_count<=MAX_CHUNKS:raise ReconciliationDenied('bounded_manifest_required')
            cursor.execute('SELECT scope_json,catalog_epoch FROM scopes WHERE scope_sha256=%s',(document['scope_sha256'],))
            scope=cursor.fetchone()
            version_scope=dict(zip(('organization_id','collection','module','topic'),version.scope))
            if stored['document_id']!=document_id or version.document_version_id!=document['version_id'] or canonical(version_scope)!=canonical(scope['scope_json']) or stored['source_sha256']!=version.source_sha256:
                raise ReconciliationDenied('version_scope_or_source_mismatch')
            cursor.execute('SELECT byte_length,store_version FROM source_objects WHERE source_sha256=%s',(version.source_sha256,))
            source=cursor.fetchone()
            if source is None or source['byte_length']!=version.source_byte_length or source['store_version']!='source-cas-v2':raise ReconciliationDenied('source_reference_mismatch')
            if require_active:
                cursor.execute("SELECT 1 FROM outbox WHERE document_id=%s AND version_id=%s AND lifecycle_epoch=%s AND content_epoch=%s AND index_epoch=%s AND manifest_sha256=%s AND status='acknowledged' LIMIT 1",(document_id,document['version_id'],document['lifecycle_epoch'],document['content_epoch'],document['index_epoch'],stored['manifest_sha256']))
                if cursor.fetchone() is None:raise ReconciliationDenied('unacknowledged_index')
            chunks,locators,total=[],[],0
            for start in range(0,version.chunk_count,PAGE_SIZE):
                if progress is not None:progress()
                cursor.execute('SELECT * FROM chunks WHERE version_id=%s AND chunk_index>=%s ORDER BY chunk_index LIMIT %s',(document['version_id'],start,PAGE_SIZE))
                rows=cursor.fetchall()
                if len(rows)!=min(PAGE_SIZE,version.chunk_count-start):raise ReconciliationDenied('manifest_page_length')
                for offset,row in enumerate(rows):
                    locator=Locator(row['chunk_index'],row['chunk_sha256'],row['byte_length'],row['storage_reference']);locator.validate()
                    if locator.chunk_index!=start+offset:raise ReconciliationDenied('manifest_order')
                    total+=locator.chunk_byte_length
                    if total>MAX_TEXT_BYTES:raise ReconciliationDenied('text_byte_budget')
                    data=self.chunk_store.read(expected_sha256=locator.chunk_sha256,expected_byte_length=locator.chunk_byte_length)
                    locators.append(locator)
                    chunks.append(dict(index=locator.chunk_index,text=data.decode(),sha256=locator.chunk_sha256,byte_length=locator.chunk_byte_length))
            if progress is not None:progress()
            cursor.execute('SELECT 1 FROM chunks WHERE version_id=%s AND chunk_index>=%s LIMIT 1',(document['version_id'],version.chunk_count))
            if cursor.fetchone() is not None or manifest_digest(version,locators)!=stored['manifest_sha256']:raise ReconciliationDenied('manifest_mismatch')
            return dict(document=document,scope=scope['scope_json'],catalog_epoch=scope['catalog_epoch'],manifest_sha256=stored['manifest_sha256'],chunks=chunks,total_text_bytes=total)

    def _point(self,snapshot,chunk,*,include_vector):
        if self._configuration()!=self._vector_binding:raise ReconciliationDenied('vector_configuration_changed')
        document=snapshot['document']
        point=dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL,document['document_id']+':'+document['version_id']+':'+str(chunk['index']))),payload=dict(document_id=document['document_id'],version_id=document['version_id'],lifecycle_epoch=document['lifecycle_epoch'],content_epoch=document['content_epoch'],index_epoch=document['index_epoch'],manifest_sha256=snapshot['manifest_sha256'],scope=snapshot['scope'],chunk_index=chunk['index'],chunk_sha256=chunk['sha256'],byte_length=chunk['byte_length'],vector_configuration=self._vector_binding))
        if include_vector:
            vectors=self.vector_adapter.embed([chunk['text']])
            if type(vectors) is not list or len(vectors)!=1:raise ReconciliationDenied('invalid_vector_batch')
            vector=vectors[0]
            if type(vector) is not list or len(vector)!=self.vector_adapter.dimension or any(type(v) not in (int,float) or not math.isfinite(v) for v in vector):raise ReconciliationDenied('invalid_vector')
            if self._configuration()!=self._vector_binding:raise ReconciliationDenied('vector_configuration_changed')
            point['vector']=vector
        return point

    def _batch_points(self,snapshot,chunks,*,progress=None):
        if self._configuration()!=self._vector_binding:raise ReconciliationDenied('vector_configuration_changed')
        vectors=[]
        for start in range(0,len(chunks),32):
            if progress is not None:progress()
            batch=chunks[start:start+32]
            produced=self.vector_adapter.embed([c['text'] for c in batch])
            if progress is not None:progress()
            if type(produced) is not list or len(produced)!=len(batch):raise ReconciliationDenied('invalid_vector_batch')
            vectors.extend(produced)
        if type(vectors) is not list or len(vectors)!=len(chunks):raise ReconciliationDenied('invalid_vector_batch')
        points=[]
        for chunk,vector in zip(chunks,vectors):
            if type(vector) is not list or len(vector)!=self.vector_adapter.dimension or any(type(v) not in (int,float) or not math.isfinite(v) for v in vector):raise ReconciliationDenied('invalid_vector')
            point=self._point(snapshot,chunk,include_vector=False);point['vector']=vector;points.append(point)
        return points

    def _points(self,snapshot):return self._batch_points(snapshot,snapshot['chunks'])

    def _verify(self,snapshot,*,absent=False,progress=None):
        actual=self.index.read_all(snapshot['document']['document_id'],progress=progress)
        expected={} if absent else {p['id']:p['payload'] for p in (self._point(snapshot,c,include_vector=False) for c in snapshot['chunks'])}
        observed={p['id']:p['payload'] for p in actual}
        if len(observed)!=len(actual) or canonical(observed)!=canonical(expected):raise ReconciliationDenied('index_readback_mismatch')

    def reconcile_once(self,*,timeout_seconds=3600,lease_seconds=120):
        if type(timeout_seconds) not in (int,float) or not math.isfinite(timeout_seconds) or not 0<timeout_seconds<=3600:
            raise ValueError('bounded_worker_deadline_required')
        if type(lease_seconds) is not int or not 1<=lease_seconds<=120:raise ValueError('bounded_lease_required')
        deadline=self._clock()+timeout_seconds
        operation=self.writer.claim(lease_seconds=lease_seconds)
        if operation is None:return None
        def progress():
            if self._clock()>=deadline:raise ReconciliationDenied('worker_deadline')
            self.writer.renew_lease(operation['operation_id'],lease_token=operation['lease_token'],lease_seconds=lease_seconds)
            if self._clock()>=deadline:raise ReconciliationDenied('worker_deadline')
        progress()
        snapshot=self._snapshot(operation['document_id'],require_active=False,progress=progress);document=snapshot['document']
        if any(operation[k]!=document[k] for k in ('version_id','lifecycle_epoch','content_epoch','index_epoch')) or operation['manifest_sha256']!=snapshot['manifest_sha256']:raise ReconciliationDenied('stale_operation')
        absent=operation['kind'] in ('archive','tombstone')
        progress();self.index.begin_replace(document['document_id']);progress()
        if not absent:
            for start in range(0,len(snapshot['chunks']),PAGE_SIZE):
                points=self._batch_points(snapshot,snapshot['chunks'][start:start+PAGE_SIZE],progress=progress)
                progress();self.index.upsert_batch(points);progress()
        progress();self._verify(snapshot,absent=absent,progress=progress);progress()
        # This synchronous SQL operation still enforces its own unexpired lease.
        # A blocking adapter cannot be preempted; subsequent progress checks deny.
        return self.writer.acknowledge(operation['operation_id'],lease_token=operation['lease_token'],expected_manifest_sha256=snapshot['manifest_sha256'])

    def retrieve_verified(self,*,document_id,scope,chunk_indices=None):
        initial=self._snapshot(document_id,require_active=True)
        if canonical(initial['scope'])!=canonical(scope):raise ReconciliationDenied('scope_mismatch')
        if chunk_indices is None:
            if len(initial['chunks'])>MAX_SELECTED_CHUNKS:raise ReconciliationDenied('explicit_chunk_selection_required')
            chunk_indices=list(range(len(initial['chunks'])))
        if type(chunk_indices) not in (list,tuple) or not 1<=len(chunk_indices)<=MAX_SELECTED_CHUNKS or any(type(i) is not int or not 0<=i<len(initial['chunks']) for i in chunk_indices) or len(set(chunk_indices))!=len(chunk_indices):raise ReconciliationDenied('invalid_chunk_selection')
        self._verify(initial)
        final=self._snapshot(document_id,require_active=True)
        if canonical(final)!=canonical(initial):raise ReconciliationDenied('catalog_changed')
        return dict(final,chunks=[final['chunks'][i] for i in chunk_indices],selected_chunk_indices=list(chunk_indices),full_manifest_chunk_count=len(final['chunks']))
