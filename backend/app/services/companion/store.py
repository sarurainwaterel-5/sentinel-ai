"""Private owner-scoped conversation context, never operational knowledge."""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import json
import sqlite3
import uuid
import threading
import re
from app.services.sre.store import _path
from app.services.sre.authorization import SREAuthorizer
from app.services.sre.contracts import SREError, canonical, digest, identifier, timestamp

@dataclass(frozen=True)
class CompanionGrant:
    principal_id: str
    tenant_id: str
    application_id: str
    actions: frozenset

class ConversationAuthority:
    def __init__(self,sre_authorizer,grants):
        if type(sre_authorizer) is not SREAuthorizer or type(grants) is not tuple or len(grants)>256:raise SREError('INVALID_GRANTS')
        for grant in grants:
            if type(grant) is not CompanionGrant or type(grant.actions) is not frozenset or not grant.actions or not grant.actions<=frozenset({'read','converse','delete','inspect','investigate'}):raise SREError('INVALID_GRANTS')
            for value in (grant.principal_id,grant.tenant_id,grant.application_id):identifier(value)
        self.sre=sre_authorizer;self.grants=grants
    def check(self,access,tenant,app,action):
        actor=self.sre.check(access,tenant,app,'read')
        if not any(type(g) is CompanionGrant and (g.principal_id,g.tenant_id,g.application_id)==(actor,tenant,app) and action in g.actions for g in self.grants):raise SREError('COMPANION_ACCESS_DENIED')
        return actor

_AUDIT_SCHEMA='CREATE TABLE audit (sequence INTEGER PRIMARY KEY, document TEXT NOT NULL, digest TEXT NOT NULL)'
_SCHEMA='CREATE TABLE conversations (tenant TEXT, app TEXT, owner TEXT, id TEXT, document TEXT NOT NULL, digest TEXT NOT NULL, PRIMARY KEY(tenant,app,owner,id))'
class ConversationStore:
    def __init__(self,path,authority,*,create=False,retention_seconds=86400,max_conversations=32,max_turns=50):
        if type(authority) is not ConversationAuthority:raise SREError('EXPLICIT_AUTHORITY_REQUIRED')
        if any(type(v) is not int or v<1 for v in (retention_seconds,max_conversations,max_turns)) or retention_seconds>2592000 or max_conversations>128 or max_turns>100:raise SREError('INVALID_RESOURCE_LIMITS')
        self.authority=authority;self.retention=retention_seconds;self.maximum=max_conversations;self.turns=max_turns
        self.lock=threading.RLock()
        self.db=sqlite3.connect(str(_path(path,create=create)),isolation_level=None,check_same_thread=False);self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA secure_delete=ON")
        if create:
            self.db.execute(_SCHEMA);self.db.execute(_AUDIT_SCHEMA);self.db.execute('PRAGMA user_version=1')
        if self.db.execute('PRAGMA user_version').fetchone()[0]!=1 or self.db.execute("SELECT sql FROM sqlite_master WHERE name='conversations'").fetchone()[0]!=_SCHEMA:raise SREError('SCHEMA_INTEGRITY')
    def close(self):self.db.close()
    @contextmanager
    def transaction(self,access,t,a,action):
        self.lock.acquire()
        try:
            owner=self.authority.check(access,t,a,action)
        except Exception:
            self.lock.release();raise
        try:
            self.db.execute('BEGIN IMMEDIATE');self._verify();yield owner
            self.authority.check(access,t,a,action);self.db.execute('COMMIT')
        except Exception as error:
            if self.db.in_transaction:self.db.execute('ROLLBACK')
            if isinstance(error,SREError):raise
            raise SREError('CONVERSATION_OPERATION_FAILED') from None
        finally:self.lock.release()
    def _verify(self):
        schema=[tuple(row) for row in self.db.execute("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY name")]
        if schema!=[('audit',_AUDIT_SCHEMA),('conversations',_SCHEMA)] or self.db.execute('PRAGMA user_version').fetchone()[0]!=1:raise SREError('SCHEMA_INTEGRITY')
        previous='0'*64;latest={}
        for seq,row in enumerate(self.db.execute('SELECT * FROM audit ORDER BY sequence'),1):
            doc=json.loads(row['document'])
            if row['sequence']!=seq or digest(doc)!=row['digest'] or doc['previous_hash']!=previous:raise SREError('AUDIT_INTEGRITY')
            latest[tuple(doc['key'])]=doc['entity_hash'];previous=row['digest']
        found=set()
        for row in self.db.execute('SELECT * FROM conversations'):
            key=tuple(row[x] for x in ('tenant','app','owner','id'));found.add(key)
            if digest(json.loads(row['document']))!=row['digest'] or latest.get(key)!=row['digest']:raise SREError('CONVERSATION_INTEGRITY')
        if found!={k for k,v in latest.items() if v is not None}:raise SREError('AUDIT_INTEGRITY')
    def _audit(self,key,entity_hash):
        row=self.db.execute('SELECT sequence,digest FROM audit ORDER BY sequence DESC LIMIT 1').fetchone()
        seq=row[0]+1 if row else 1
        if seq>100000:raise SREError('AUDIT_CAPACITY')
        doc={'key':list(key),'entity_hash':entity_hash,'previous_hash':row[1] if row else '0'*64}
        self.db.execute('INSERT INTO audit VALUES (?,?,?)',(seq,canonical(doc),digest(doc)))
    def _read(self,t,a,o,id,now):
        identifier(id)
        row=self.db.execute('SELECT document,digest FROM conversations WHERE tenant=? AND app=? AND owner=? AND id=?',(t,a,o,id)).fetchone()
        if not row:raise SREError('CONVERSATION_UNAVAILABLE')
        doc=json.loads(row[0])
        if digest(doc)!=row[1] or (doc['tenant_id'],doc['application_id'],doc['owner_id'],doc['conversation_id'])!=(t,a,o,id):raise SREError('CONVERSATION_INTEGRITY')
        if now>=doc['expires_at']:raise SREError('CONVERSATION_EXPIRED')
        return doc
    def _save(self,doc):
        self._audit((doc['tenant_id'],doc['application_id'],doc['owner_id'],doc['conversation_id']),digest(doc))
        self.db.execute('INSERT OR REPLACE INTO conversations VALUES (?,?,?,?,?,?)',(doc['tenant_id'],doc['application_id'],doc['owner_id'],doc['conversation_id'],canonical(doc),digest(doc)))
    def create(self,access,t,a,*,now,tone='direct'):
        now=timestamp(now)
        if tone not in ('direct','friendly','technical'):raise SREError('INVALID_TONE')
        with self.transaction(access,t,a,'converse') as owner:
            self._purge(t,a,owner,now)
            if self.db.execute('SELECT COUNT(*) FROM conversations WHERE tenant=? AND app=? AND owner=?',(t,a,owner)).fetchone()[0]>=self.maximum:raise SREError('CONVERSATION_CAPACITY')
            doc={'schema_version':1,'tenant_id':t,'application_id':a,'owner_id':owner,'conversation_id':str(uuid.uuid4()),'title':'New conversation','tone':tone,'revision':0,'created_at':now,'updated_at':now,'expires_at':timestamp((datetime.fromisoformat(now.replace('Z','+00:00'))+timedelta(seconds=self.retention)).isoformat()),'messages':[],'summary':'No conversation context yet.','memory_class':'CONVERSATION_CONTEXT'}
            self._save(doc);return doc
    def _purge(self,t,a,o,now):
        for row in self.db.execute('SELECT id,document,digest FROM conversations WHERE tenant=? AND app=? AND owner=?',(t,a,o)).fetchall():
            doc=json.loads(row['document'])
            if digest(doc)!=row['digest']:raise SREError('CONVERSATION_INTEGRITY')
            if doc['expires_at']<=now:
                self._audit((t,a,o,row['id']),None)
                self.db.execute('DELETE FROM conversations WHERE tenant=? AND app=? AND owner=? AND id=?',(t,a,o,row['id']))
    def list(self,access,t,a,*,now):
        now=timestamp(now)
        with self.transaction(access,t,a,'read') as owner:
            self._purge(t,a,owner,now)
            return [self._read(t,a,owner,r[0],now) for r in self.db.execute('SELECT id FROM conversations WHERE tenant=? AND app=? AND owner=? ORDER BY id',(t,a,owner)).fetchall()]
    def get(self,access,t,a,id,*,now):
        with self.transaction(access,t,a,'read') as owner:return self._read(t,a,owner,id,timestamp(now))
    def delete(self,access,t,a,id,*,now):
        with self.transaction(access,t,a,'delete') as owner:
            self._read(t,a,owner,id,timestamp(now));self._audit((t,a,owner,id),None);self.db.execute('DELETE FROM conversations WHERE tenant=? AND app=? AND owner=? AND id=?',(t,a,owner,id))
    def append(self,access,t,a,id,*,now,turn_id,text,expected_revision,response):
        identifier(turn_id);now=timestamp(now)
        if isinstance(text,str) and re.search(r'(?:sk-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{8,}|(?:password|api[_ -]?key|secret|authorization)\s*[:=]\s*\S+)',text,re.I):raise SREError('SENSITIVE_MESSAGE_DENIED')
        if type(text) is not str or not text.strip() or len(text)>4000:raise SREError('INVALID_MESSAGE')
        with self.transaction(access,t,a,'converse') as owner:
            doc=self._read(t,a,owner,id,now)
            prior=[m for m in doc['messages'] if m['turn_id']==turn_id]
            if prior:
                if prior[0]['content']!=text:raise SREError('TURN_CONFLICT')
                return doc
            if type(expected_revision) is not int or expected_revision!=doc['revision']:raise SREError('STALE_CONVERSATION')
            if doc['revision']>=self.turns:raise SREError('CONVERSATION_CAPACITY')
            doc['messages'] += [{'role':'user','content':text,'sources':[],'status':'CONTEXT_ONLY','turn_id':turn_id},dict(response,role='assistant',turn_id=turn_id)]
            doc['revision']+=1;doc['updated_at']=now;doc['title']='Conversation '+id[:8]
            doc['summary']=f"{doc['revision']} turns retained as unverified conversation context; latest topic: {response.get('topic','unknown')}."
            self._save(doc);return doc
