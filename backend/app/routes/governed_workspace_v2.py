"""Explicit opt-in v2 intake/lifecycle router; never auto-migrates or enables answers.

A configured host must mount this router only after reviewing its exact target.
Its Basic credentials are independently verified against the supplied catalog.
"""
from pathlib import Path
import os
import uuid

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile, Request
from fastapi.routing import APIRoute
from starlette.concurrency import run_in_threadpool
from evaluation.governed_answers.identity_resolution import _parse_basic
from evaluation.governed_answers.content_addressed_sources import _open_directory, _absolute_parts
from pydantic import BaseModel, ConfigDict, Field

from app.services.governed_authentication import GovernedAuthenticationSession
from app.services.governed_ingestion import GovernedIngestionService
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope


class LifecycleRequest(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)
    scope: EvidenceScope
    expected_lifecycle_epoch: int = Field(ge=1)
    expected_content_epoch: int = Field(ge=1)
    expected_index_epoch: int = Field(ge=1)


def create_governed_workspace_router(*, catalog, source_store, chunk_store,
                                      accepted_source_root, extraction_policy_sha256, extractor,
                                      max_request_bytes=1024**3+2*1024**2, max_concurrent_requests=2):
    """All dependencies are explicit server capabilities, not request parameters.

    extractor(path, original_name) returns text under the pinned server policy.
    It must enforce its own CPU/time/memory bounds; thread-pool execution keeps
    the event loop responsive but cannot forcibly terminate a blocking parser.
    Accepted source files are retained even on later errors. This factory is not
    mounted in the current frozen main app and does not change release state.
    """
    root = Path(accepted_source_root)
    if not root.is_absolute() or root.is_symlink() or not root.is_dir():
        raise ValueError('explicit_existing_source_root_required')
    info = root.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('private_source_root_required')
    fd = _open_directory(_absolute_parts(str(root)))
    os.close(fd)
    if not callable(extractor): raise ValueError('extractor_required')
    if type(max_request_bytes) is not int or not 1 <= max_request_bytes <= 1024**3+2*1024**2:
        raise ValueError('bounded_request_limit_required')
    if type(max_concurrent_requests) is not int or not 1 <= max_concurrent_requests <= 8:
        raise ValueError('bounded_concurrency_required')
    service = GovernedIngestionService(catalog=catalog,source_store=source_store,chunk_store=chunk_store)
    in_flight = 0
    class BoundedAuthenticatedRoute(APIRoute):
        def get_route_handler(self):
            original = super().get_route_handler()
            async def handler(request):
                nonlocal in_flight
                if in_flight >= max_concurrent_requests:
                    raise HTTPException(429,'Governed workspace is busy.')
                in_flight += 1
                try:
                    values=tuple(request.headers.getlist('authorization'))
                    def preflight():
                        try:
                            attempt=_parse_basic(values)
                            record=catalog.read_principal(attempt.username)
                            scopes=record.get('scopes',[]) if type(record) is dict else []
                            scope=EvidenceScope.model_validate(scopes[0],strict=True) if scopes else EvidenceScope(
                                organization_id='preflight',collection='preflight',module='preflight',topic='preflight')
                            authenticate(values,scope)
                        except Exception:
                            raise HTTPException(401,'Credentials denied.',headers={'WWW-Authenticate':'Basic realm="Sentinel governed workspace"'}) from None
                    # Authenticate headers before FastAPI parses multipart/spools.
                    await run_in_threadpool(preflight)
                    lengths=request.headers.getlist('content-length')
                    if lengths:
                        if len(lengths)!=1 or len(lengths[0])>20 or not lengths[0].isascii() or not lengths[0].isdecimal():
                            raise HTTPException(400,'Invalid request length.')
                        if int(lengths[0])>max_request_bytes: raise HTTPException(413,'Request exceeds intake limit.')
                    total=0
                    async def bounded_receive():
                        nonlocal total
                        message=await request.receive()
                        if message['type']=='http.request':
                            total+=len(message.get('body',b''))
                            if total>max_request_bytes: raise HTTPException(413,'Request exceeds intake limit.')
                        return message
                    return await original(Request(request.scope,receive=bounded_receive))
                finally:
                    in_flight -= 1
            return handler
    router = APIRouter(prefix='/governance/v2',tags=['Governed v2 inspection workspace'],route_class=BoundedAuthenticatedRoute)

    def authenticate(headers, scope):
        session=GovernedAuthenticationSession(catalog)
        principal=session.authenticate(authorization_values=tuple(headers or ()),scope=scope)
        if principal is None:
            raise HTTPException(401,'Credentials or exact scope denied.',headers={'WWW-Authenticate':'Basic realm="Sentinel governed workspace"'})
        return session,principal

    @router.post('/sources',status_code=202)
    async def ingest_source(file: UploadFile=File(...),organization_id: str=Form(...),
                            collection: str=Form(...),module: str=Form(...),topic: str=Form(...),
                            authorization: list[str] | None=Header(default=None)):
        try: scope=EvidenceScope(organization_id=organization_id,collection=collection,module=module,topic=topic)
        except ValueError: raise HTTPException(422,'Explicit exact scope required.') from None
        session,principal=authenticate(authorization,scope)
        suffix=Path(file.filename or '').suffix.lower()
        if len(suffix)>12 or any(not (c.isascii() and (c.isalnum() or c=='.')) for c in suffix): suffix=''
        path=root/(uuid.uuid4().hex+suffix)
        # Private exclusive server-generated filename; never trust folder paths.
        total=0
        try:
            with path.open('xb') as accepted:
                path.chmod(0o600)
                while block:=await file.read(1024**2):
                    total+=len(block)
                    if total>1024**3: raise HTTPException(413,'Source exceeds 1 GiB.')
                    accepted.write(block)
                accepted.flush();os.fsync(accepted.fileno())
            if not total: raise HTTPException(422,'Empty source.')
            text=await run_in_threadpool(extractor,path,file.filename or 'source')
            result=await run_in_threadpool(service.ingest,session=session,principal=principal,source_path=path,
                extracted_text=text,extraction_policy_sha256=extraction_policy_sha256)
            return result
        except HTTPException: raise
        except Exception: raise HTTPException(409,'Intake withheld; accepted source retained for inspection.') from None
        finally:
            await file.close()

    @router.post('/documents/{document_id}/{operation}',status_code=202)
    def lifecycle(document_id: str,operation: str,request: LifecycleRequest,
                  authorization: list[str] | None=Header(default=None)):
        if operation not in ('archive','restore','tombstone'):
            raise HTTPException(422,'Unsupported governed lifecycle operation.')
        session,principal=authenticate(authorization,request.scope)
        try:
            result=catalog.transition_authorized(document_id,principal=principal,authentication_session=session,
                expected_lifecycle_epoch=request.expected_lifecycle_epoch,
                expected_content_epoch=request.expected_content_epoch,
                expected_index_epoch=request.expected_index_epoch,operation=operation)
            return dict(result,production_enabled=False,release_authorized=False)
        except Exception: raise HTTPException(409,'Lifecycle transition denied or stale.') from None

    return router
