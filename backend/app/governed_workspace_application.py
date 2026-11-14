"""Explicit configured governed workspace sidecar; production answering disabled.

Uvicorn: app.governed_workspace_application:create_app --factory. Configuration
path is supplied explicitly or through SENTINEL_GOVERNED_CONFIG. No legacy main,
default credentials, migration, provider construction or collection creation.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

from fastapi import FastAPI,HTTPException,Request
from starlette.responses import JSONResponse
from evaluation.governed_answers.identity_resolution import _parse_basic
from pydantic import BaseModel,ConfigDict,Field,field_validator
from psycopg2.extras import Json
from starlette.concurrency import run_in_threadpool

from app.routes.governed_workspace_v2 import create_governed_workspace_router
from app.services.governed_authentication import GovernedAuthenticationSession
from app.services.governed_catalog import CatalogWriter,scope_key
from app.services.governed_embeddings import GovernedEmbeddingAdapter
from app.services.governed_qdrant_index import GovernedQdrantIndex
from evaluation.governed_answers.catalog_index_reconciler import CatalogIndexReconciler
from evaluation.governed_answers.content_addressed_chunks import ContentAddressedChunkStore
from evaluation.governed_answers.content_addressed_sources import _open_source,_identity,_open_directory,_absolute_parts,ContentAddressedSourceStore
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope

AUTH_HEADER='x-sentinel-governed-authorization'


def server_extraction_policy_sha256():
    """Canonical identity of installed extraction code and parser dependencies.

    Missing optional packages are pinned as absent. This policy identifies the
    server implementation; it does not certify unreviewed OCR or speech output.
    """
    from importlib.metadata import version, PackageNotFoundError
    import platform
    services=Path(__file__).parent/'services'
    files={name:hashlib.sha256((services/name).read_bytes()).hexdigest()
           for name in ('media_extraction.py','chunking_service.py',
                        'audio_transcription.py','audio_worker.py')}
    files['governed_workspace_application.py']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    dependencies={}
    for package in ('pypdf','Pillow','faster-whisper','ctranslate2','numpy','fastapi'):
        try:dependencies[package]=version(package)
        except PackageNotFoundError:dependencies[package]=None
    value=dict(version='sentinel-server-extraction-policy-v1',files=files,
               dependencies=dependencies,python=platform.python_version())
    raw=json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(raw).hexdigest()


class WorkerConfiguration(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True,strict=True)
    max_seconds:int=Field(ge=1,le=3600)
    lease_seconds:int=Field(ge=1,le=120)
    poll_seconds:int=Field(ge=1,le=60)
    max_operations:int=Field(ge=1,le=100000)


class WorkspaceConfiguration(BaseModel):
    model_config=ConfigDict(extra='forbid',frozen=True,strict=True)
    version:str
    database_env:str
    schema:str
    source_root:str
    chunk_root:str
    accepted_source_root:str
    qdrant_url:str
    collection:str
    collection_identity:dict[str,str]
    model_root:str
    model_artifact_manifest:str
    model_manifest_sha256:str
    model_name:str
    dimension:int=Field(ge=1,le=4096)
    extraction_policy_sha256:str
    max_request_bytes:int=Field(ge=1,le=1075838976)
    max_concurrent_requests:int=Field(ge=1,le=8)
    worker:WorkerConfiguration

    @field_validator('model_manifest_sha256','extraction_policy_sha256')
    @classmethod
    def digest(cls,value):
        if re.fullmatch('[a-f0-9]{64}',value) is None:raise ValueError('explicit_digest_required')
        return value

    @field_validator('source_root','chunk_root','accepted_source_root','model_root','model_artifact_manifest')
    @classmethod
    def absolute(cls,value):
        if not Path(value).is_absolute():raise ValueError('absolute_path_required')
        return value

    @field_validator('version')
    @classmethod
    def versioned(cls,value):
        if value!='sentinel-governed-workspace-v1':raise ValueError('unsupported_configuration')
        return value

    @field_validator('database_env')
    @classmethod
    def environment_name(cls,value):
        if re.fullmatch('[A-Z][A-Z0-9_]{2,99}',value) is None:raise ValueError('explicit_database_environment_reference_required')
        return value

    @field_validator('schema')
    @classmethod
    def schema_name(cls,value):
        if re.fullmatch('sentinel_governed_[a-z0-9_]{1,80}',value) is None:raise ValueError('dedicated_schema_required')
        return value

    @field_validator('qdrant_url')
    @classmethod
    def endpoint(cls,value):
        parsed=urlsplit(value)
        if parsed.scheme not in ('http','https') or not parsed.hostname or not parsed.port or parsed.username or parsed.password or parsed.query or parsed.fragment or parsed.path not in ('','/'):
            raise ValueError('explicit_index_endpoint_required')
        return value


def _read_private_json(path,*,private=False):
    fd=_open_source(path)
    try:
        before=os.fstat(fd)
        if private and (before.st_uid!=os.geteuid() or stat.S_IMODE(before.st_mode)&0o077):raise ValueError('private_configuration_required')
        if not 1<=before.st_size<=1024*1024:raise ValueError('configuration_size_budget')
        raw=os.read(fd,before.st_size+1)
        if len(raw)!=before.st_size or _identity(before)!=_identity(os.fstat(fd)):raise ValueError('configuration_changed')
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise ValueError('duplicate_configuration_key')
                result[key]=value
            return result
        value=json.loads(raw,object_pairs_hook=unique,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite_configuration')))
        return value,raw
    finally:os.close(fd)


def load_configuration(path):
    value,_=_read_private_json(path,private=True)
    result=WorkspaceConfiguration.model_validate(value,strict=True)
    if len({result.source_root,result.chunk_root,result.accepted_source_root,result.model_root})!=4:
        raise ValueError('separate_storage_roots_required')
    identity=result.collection_identity
    if (set(identity)!={'sentinel_workspace_identity','embedding_policy_sha256','schema'}
            or identity['schema']!='governed-v2' or identity['embedding_policy_sha256']!=result.model_manifest_sha256
            or re.fullmatch('[a-f0-9]{32}',identity['sentinel_workspace_identity']) is None):
        raise ValueError('explicit_collection_identity_required')
    return result


def verify_model_artifacts(config):
    manifest,raw=_read_private_json(config.model_artifact_manifest)
    if hashlib.sha256(raw).hexdigest()!=config.model_manifest_sha256:raise ValueError('model_manifest_digest_mismatch')
    if (type(manifest) is not dict or set(manifest)!={'version','model_name','dimension','files'}
            or manifest['version']!='sentinel-model-artifacts-v1' or manifest['model_name']!=config.model_name
            or type(manifest['dimension']) is not int or manifest['dimension']!=config.dimension
            or type(manifest['files']) is not list or not 1<=len(manifest['files'])<=256):raise ValueError('model_manifest_binding_mismatch')
    root=Path(config.model_root)
    fd=_open_directory(_absolute_parts(str(root)));os.close(fd)
    seen=[];total=0
    for record in manifest['files']:
        if type(record) is not dict or set(record)!={'path','sha256','byte_length'}:raise ValueError('invalid_model_record')
        path=record['path']
        if type(path) is not str or not path or Path(path).is_absolute() or any(p in ('','..','.') for p in path.split('/')) or '\\' in path or len(path)>500:
            raise ValueError('invalid_model_path')
        if path in seen or type(record['byte_length']) is not int or not 1<=record['byte_length']<=1024**3 or type(record['sha256']) is not str or re.fullmatch('[a-f0-9]{64}',record['sha256']) is None:raise ValueError('invalid_model_record')
        seen.append(path);total+=record['byte_length']
        if total>2*1024**3:raise ValueError('model_byte_budget')
        target=root/path;descriptor=_open_source(target)
        try:
            before=os.fstat(descriptor)
            if before.st_size!=record['byte_length']:raise ValueError('model_length_mismatch')
            hasher=hashlib.sha256();count=0
            while block:=os.read(descriptor,1024*1024):
                count+=len(block)
                if count>record['byte_length']:raise ValueError('model_changed')
                hasher.update(block)
            if count!=record['byte_length'] or hasher.hexdigest()!=record['sha256'] or _identity(before)!=_identity(os.fstat(descriptor)):raise ValueError('model_digest_mismatch')
            current=_open_source(target)
            try:
                if _identity(os.fstat(current))!=_identity(before):raise ValueError('model_changed')
            finally:os.close(current)
        finally:os.close(descriptor)
    actual=[]
    for child in root.rglob('*'):
        if child.is_symlink():raise ValueError('model_symlink_denied')
        if child.is_file():actual.append(child.relative_to(root).as_posix())
        elif not child.is_dir():raise ValueError('model_special_file_denied')
    if seen!=sorted(seen) or sorted(actual)!=seen:raise ValueError('model_file_inventory_mismatch')
    return dict(sha256=config.model_manifest_sha256,file_count=len(seen),byte_length=total)


def verify_collection(client,config):
    if not client.collection_exists(config.collection):raise ValueError('reviewed_collection_missing')
    info=client.get_collection(config.collection)
    vectors=info.config.params.vectors
    distance=getattr(getattr(vectors,'distance',None),'value',getattr(vectors,'distance',None))
    if (getattr(vectors,'size',None)!=config.dimension or distance!='Cosine'
            or info.config.metadata!=config.collection_identity):raise ValueError('reviewed_collection_identity_mismatch')


@dataclass
class WorkspaceRuntime:
    config:WorkspaceConfiguration
    catalog:object
    source_store:object
    chunk_store:object
    index:object
    embeddings:object
    reconciler:object
    model_verification:dict

    def close(self):self.index.client.close()


def build_runtime(config):
    """Validate existing reviewed resources only; never install/adopt by name."""
    import psycopg2
    from qdrant_client import QdrantClient
    from app.services.embedding_service import EmbeddingService
    if config.extraction_policy_sha256!=server_extraction_policy_sha256():
        raise ValueError('server_extraction_policy_mismatch')
    verified=verify_model_artifacts(config)
    for path in (config.source_root,config.chunk_root,config.accepted_source_root):
        fd=_open_directory(_absolute_parts(path))
        try:
            info=os.fstat(fd)
            if info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)&0o077:raise ValueError('private_owned_storage_required')
        finally:os.close(fd)
    dsn=os.environ.get(config.database_env)
    if type(dsn) is not str or not dsn.strip():raise ValueError('explicit_database_credentials_missing')
    catalog=CatalogWriter(lambda:psycopg2.connect(dsn,connect_timeout=5),schema=config.schema)
    with catalog.transaction() as cursor:
        # Missing schema/table fails; factory never performs migrations.
        cursor.execute('SELECT permission_epoch,credential_epoch FROM principals LIMIT 0')
        cursor.execute('SELECT manifest_sha256 FROM versions LIMIT 0')
    backend=EmbeddingService();backend.model_name=config.model_root
    embeddings=GovernedEmbeddingAdapter(backend=backend,dimension=config.dimension,policy_sha256=config.model_manifest_sha256)
    if backend.get_dimension()!=config.dimension:raise ValueError('model_dimension_mismatch')
    client=QdrantClient(url=config.qdrant_url,timeout=10)
    try:
        verify_collection(client,config)
        index=GovernedQdrantIndex(client,collection=config.collection,dimension=config.dimension)
        source_store=ContentAddressedSourceStore(config.source_root);chunk_store=ContentAddressedChunkStore(config.chunk_root)
        reconciler=CatalogIndexReconciler(catalog,chunk_store=chunk_store,index=index,vector_adapter=embeddings)
        return WorkspaceRuntime(config,catalog,source_store,chunk_store,index,embeddings,reconciler,verified)
    except BaseException:client.close();raise


def _extract(path,name):
    from app.services.media_extraction import extract_source_text
    # Retain the uploaded original, but require a reviewed derivative before OCR
    # or transcription can become governed searchable text.
    if Path(name).suffix.lower() not in ('.txt','.md','.csv','.json','.log','.pdf'):
        raise ValueError('extraction_requires_review')
    result=extract_source_text(path,name)
    if result.get('warnings') or result.get('notices') or not result.get('text','').strip():raise ValueError('extraction_requires_review')
    return result['text']


class InspectionRequest(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
    document_id:str=Field(min_length=1,max_length=200)
    scope:EvidenceScope
    chunk_indices:list[int]=Field(min_length=1,max_length=128)


def create_app(config_path=None):
    from contextlib import asynccontextmanager
    path=config_path or os.environ.get('SENTINEL_GOVERNED_CONFIG')
    if type(path) is not str or not path:raise ValueError('explicit_workspace_configuration_required')
    try:
        config=load_configuration(path);runtime=build_runtime(config)
    except Exception:raise ValueError('governed_workspace_startup_verification_failed') from None
    @asynccontextmanager
    async def lifespan(app):
        yield
        runtime.close()
    app=FastAPI(title='Sentinel governed inspection workspace',lifespan=lifespan)
    app.state.governed_runtime=runtime
    @app.middleware('http')
    async def header_guard(request,call_next):
        if request.url.path!='/governance/v2/status':
            def preflight():
                values=tuple(request.headers.getlist(AUTH_HEADER))
                attempt=_parse_basic(values)
                record=runtime.catalog.read_principal(attempt.username)
                scopes=record.get('scopes',[]) if type(record) is dict else []
                if not scopes:raise ValueError('no_grants')
                scope=EvidenceScope.model_validate(scopes[0],strict=True)
                session=GovernedAuthenticationSession(runtime.catalog)
                if session.authenticate(authorization_values=values,scope=scope) is None:raise ValueError('credentials_denied')
            try:await run_in_threadpool(preflight)
            except Exception:return JSONResponse({'detail':'Dedicated governed credentials denied.'},status_code=401)
            if request.url.path=='/governance/v2/inspect':
                lengths=request.headers.getlist('content-length')
                if lengths and (len(lengths)!=1 or not lengths[0].isascii() or not lengths[0].isdecimal() or len(lengths[0])>20):
                    return JSONResponse({'detail':'Invalid request length.'},status_code=400)
                if lengths and int(lengths[0])>65536:return JSONResponse({'detail':'Inspection request exceeds limit.'},status_code=413)
                original=request._receive
                total=0
                async def bounded_receive():
                    nonlocal total
                    message=await original()
                    if message['type']=='http.request':
                        total+=len(message.get('body',b''))
                        if total>65536:raise HTTPException(413,'Inspection request exceeds limit.')
                    return message
                request._receive=bounded_receive
        return await call_next(request)
    app.include_router(create_governed_workspace_router(catalog=runtime.catalog,source_store=runtime.source_store,chunk_store=runtime.chunk_store,accepted_source_root=config.accepted_source_root,extraction_policy_sha256=config.extraction_policy_sha256,extractor=_extract,max_request_bytes=config.max_request_bytes,max_concurrent_requests=config.max_concurrent_requests,authorization_header=AUTH_HEADER))

    def authenticate(request,scope):
        session=GovernedAuthenticationSession(runtime.catalog)
        principal=session.authenticate(authorization_values=tuple(request.headers.getlist(AUTH_HEADER)),scope=scope)
        if principal is None:raise HTTPException(401,'Governed credentials or exact scope denied.')
        return session,principal

    def lock_authority(cursor,session,principal):
        if not session.recheck(principal):raise ValueError('authority_changed')
        cursor.execute('SELECT credential_epoch,permission_epoch,disabled FROM principals WHERE principal_id=%s FOR UPDATE',(principal.principal_id,))
        row=cursor.fetchone()
        if row is None or row['disabled'] or row['credential_epoch']!=principal.credential_epoch or row['permission_epoch']!=principal.permission_epoch:raise ValueError('authority_changed')
        key=scope_key(principal.scope.model_dump(mode='json'))
        cursor.execute('SELECT catalog_epoch FROM scopes WHERE scope_sha256=%s FOR UPDATE',(key,))
        scope=cursor.fetchone()
        cursor.execute('SELECT 1 FROM grants WHERE principal_id=%s AND scope_sha256=%s',(principal.principal_id,key))
        if scope is None or cursor.fetchone() is None:raise ValueError('grant_changed')
        return key,scope['catalog_epoch']

    @app.get('/governance/v2/status')
    def status():
        return dict(status='verified_inspection_workspace',production_enabled=False,release_authorized=False,provider_calls=0,model_artifacts_verified=True,collection_identity_verified=True)

    @app.get('/governance/v2/documents')
    def documents(request:Request,organization_id:str,collection:str,module:str,topic:str,after:str='',limit:int=100):
        if not 1<=limit<=256 or len(after)>200:raise HTTPException(422,'Bounded cursor required.')
        try:scope=EvidenceScope(organization_id=organization_id,collection=collection,module=module,topic=topic)
        except ValueError:raise HTTPException(422,'Exact scope required.') from None
        session,principal=authenticate(request,scope)
        try:
            with runtime.catalog.transaction() as cursor:
                key,epoch=lock_authority(cursor,session,principal)
                cursor.execute('SELECT document_id,state,version_id,lifecycle_epoch,content_epoch,index_epoch FROM documents WHERE scope_sha256=%s AND document_id>%s ORDER BY document_id LIMIT %s',(key,after,limit+1))
                rows=[dict(row) for row in cursor.fetchall()]
            return dict(documents=rows[:limit],next_cursor=rows[limit-1]['document_id'] if len(rows)>limit else None,catalog_epoch=epoch,production_enabled=False,release_authorized=False,provider_calls=0)
        except Exception:raise HTTPException(409,'Current catalog inspection denied.') from None

    @app.post('/governance/v2/inspect')
    def inspect(request:Request,body:InspectionRequest):
        session,principal=authenticate(request,body.scope)
        try:
            verified=runtime.reconciler.retrieve_verified(document_id=body.document_id,scope=body.scope.model_dump(mode='json'),chunk_indices=body.chunk_indices)
            with runtime.catalog.transaction() as cursor:
                key,epoch=lock_authority(cursor,session,principal)
                cursor.execute('SELECT * FROM documents WHERE document_id=%s FOR UPDATE',(body.document_id,))
                row=cursor.fetchone()
                if row is None or dict(row)!=verified['document'] or row['scope_sha256']!=key or epoch!=verified['catalog_epoch']:raise ValueError('catalog_changed')
                sources=[dict(document_id=body.document_id,chunk_index=c['index'],text=c['text'],sha256=c['sha256'],byte_length=c['byte_length']) for c in verified['chunks']]
            return dict(document=verified['document'],manifest_sha256=verified['manifest_sha256'],sources=sources,selected_chunk_indices=verified['selected_chunk_indices'],full_manifest_chunk_count=verified['full_manifest_chunk_count'],catalog_epoch=epoch,production_enabled=False,release_authorized=False,provider_calls=0,semantic_grounding_verified=False,proposition_to_inference='closed')
        except Exception:raise HTTPException(409,'Verified source inspection denied or stale.') from None
    return app
