"""Explicitly composed local API. Not mounted into installed or production app."""
from datetime import datetime, timezone
from typing import Literal
from fastapi import FastAPI, Request, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from app.services.sre.authorization import Access
from app.services.sre.contracts import SREError

class CreateConversation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    tone:Literal['direct','friendly','technical']='direct'
class Turn(BaseModel):
    model_config=ConfigDict(extra='forbid')
    turn_id:str=Field(min_length=1,max_length=128)
    text:str=Field(min_length=1,max_length=4000)
    expected_revision:int=Field(ge=0,le=100)
class Investigation(BaseModel):
    model_config=ConfigDict(extra='forbid')
    service_id:str=Field(max_length=128)
    observation_ids:list[str]|None=None
    incident_id:str|None=None
    evaluated_at:str

def create_companion_app(*,store,manager,knowledge,session_factory,evidence_scope,tenant_id,application_id,sre_store=None,now=lambda:datetime.now(timezone.utc).isoformat()):
    app=FastAPI(title='Sentinel Companion local opt-in',docs_url=None,redoc_url=None,openapi_url=None)
    def access(request,action):
        session=session_factory()
        principal=session.authenticate(authorization_values=tuple(request.headers.getlist('authorization')),scope=evidence_scope)
        if principal is None:raise HTTPException(401,'Authentication required',headers={'WWW-Authenticate':'Basic'})
        value=Access(session,principal);store.authority.check(value,tenant_id,application_id,action);return value
    @app.middleware('http')
    async def bounded_body(request,call_next):
        from fastapi.responses import JSONResponse
        if request.method in ('POST','PUT','PATCH'):
            body=bytearray()
            async for chunk in request.stream():
                if len(body)+len(chunk)>16384:return JSONResponse(status_code=413,content={'detail':'Request exceeds local budget'})
                body.extend(chunk)
            request._body=bytes(body)
        return await call_next(request)
    @app.exception_handler(SREError)
    async def denied(request,error):
        from fastapi.responses import JSONResponse
        return JSONResponse(status_code=409 if str(error) in ('STALE_CONVERSATION','TURN_CONFLICT') else 403,content={'detail':'Companion request unavailable'})
    @app.get('/companion/v1/capabilities')
    async def capabilities(request:Request):
        value=access(request,'inspect');result=knowledge.authorized(lambda:store.authority.check(value,tenant_id,application_id,'inspect')).snapshot()
        for capability in result['capabilities']:
            for source in capability.get('evidence_references',[]):source['label']=source['path']
        store.authority.check(value,tenant_id,application_id,'inspect');return result
    @app.get('/companion/v1/conversations')
    async def conversations(request:Request):return {'conversations':store.list(access(request,'read'),tenant_id,application_id,now=now())}
    @app.post('/companion/v1/conversations')
    async def create(body:CreateConversation,request:Request):return store.create(access(request,'converse'),tenant_id,application_id,now=now(),tone=body.tone)
    @app.get('/companion/v1/conversations/{id}')
    async def get(id:str,request:Request):return store.get(access(request,'read'),tenant_id,application_id,id,now=now())
    @app.delete('/companion/v1/conversations/{id}',status_code=204)
    async def delete(id:str,request:Request):
        store.delete(access(request,'delete'),tenant_id,application_id,id,now=now());return Response(status_code=204)
    @app.post('/companion/v1/conversations/{id}/turns')
    async def turn(id:str,body:Turn,request:Request):
        from .manager import ConversationManager
        value=access(request,'converse')
        bound=knowledge.authorized(lambda:store.authority.check(value,tenant_id,application_id,'converse'))
        scoped=ConversationManager(store,bound,provider=manager.provider,clock=manager.clock)
        return scoped.turn(value,tenant_id,application_id,id,now=now(),**body.model_dump())
    @app.post('/companion/v1/investigations')
    async def investigate(body:Investigation,request:Request):
        from app.services.sre.investigation import run_investigation
        value=access(request,'investigate')
        if sre_store is None:raise SREError('INVESTIGATION_UNAVAILABLE')
        report=run_investigation(sre_store,value,tenant_id,application_id,**body.model_dump())
        store.authority.check(value,tenant_id,application_id,'investigate');return report
    return app
