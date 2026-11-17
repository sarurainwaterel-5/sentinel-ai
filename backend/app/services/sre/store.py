"""Opt-in private local SQLite SRE store. No network, scheduler or startup hooks.

All supported operations enforce authenticated scope and verify stored integrity.
Filesystem ownership is a trust boundary; unkeyed hashes are not anti-admin proofs.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat
from .contracts import (SREError,canonical,digest,identifier,timestamp,evidence,record,
                        service_record,observation_record)
from .authorization import SREAuthorizer
from . import GOVERNANCE

MIGRATIONS=Path(__file__).with_name('migrations')
SCHEMA_VERSION=2

@dataclass(frozen=True)
class Limits:
    services: int=256
    observations: int=10000
    audit: int=50000
    dependencies: int=1024
    incidents: int=1000


def _migration(version):
    return sorted(MIGRATIONS.glob('*.sql'))[version-1].read_text()


def _schema(db):
    return tuple(tuple(row) for row in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))


def _expected(version):
    with sqlite3.connect(':memory:') as db:
        for v in range(1,version+1):db.executescript(_migration(v))
        return _schema(db)


def _path(value,create=False):
    p=Path(value)
    if not p.is_absolute() or p.resolve(strict=False)!=p or not p.parent.is_dir(): raise SREError('PRIVATE_ABSOLUTE_PATH_REQUIRED')
    parent=p.parent.stat()
    if parent.st_uid!=os.geteuid() or stat.S_IMODE(parent.st_mode)&0o077: raise SREError('PRIVATE_DIRECTORY_REQUIRED')
    if create:
        fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);os.close(fd)
    info=p.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid!=os.geteuid() or stat.S_IMODE(info.st_mode)&0o077: raise SREError('PRIVATE_DATABASE_REQUIRED')
    return p


class SREStore:
    def __init__(self,path,authorizer,limits):
        if type(authorizer) is not SREAuthorizer or type(limits) is not Limits:raise SREError('EXPLICIT_AUTHORITY_REQUIRED')
        if any(type(v) is not int or not 1<=v<=100000 for v in vars(limits).values()):raise SREError('INVALID_RESOURCE_LIMITS')
        self.path=path;self.authorizer=authorizer;self.limits=limits
        self._db=sqlite3.connect(str(path),isolation_level=None,timeout=2)
        self._db.row_factory=sqlite3.Row
        self._db.execute('PRAGMA foreign_keys=ON');self._db.execute('PRAGMA synchronous=FULL');self._db.execute('PRAGMA busy_timeout=2000')

    @classmethod
    def create(cls,path,authorizer,*,limits=Limits(),version=SCHEMA_VERSION):
        if type(authorizer) is not SREAuthorizer:raise SREError('EXPLICIT_AUTHORITY_REQUIRED')
        if type(version) is not int or not 1<=version<=SCHEMA_VERSION:raise SREError('UNSUPPORTED_STORAGE_VERSION')
        p=_path(path,create=True);instance=cls(p,authorizer,limits)
        try:
            for v in range(1,version+1):instance._migrate(v)
            instance._verify_schema(version)
            return instance
        except Exception:
            instance.close();raise

    @classmethod
    def open(cls,path,authorizer,*,limits=Limits()):
        p=_path(path);instance=cls(p,authorizer,limits)
        try:
            rows=instance._db.execute('SELECT version,migration_hash FROM sre_metadata ORDER BY version').fetchall()
            if not rows or len(rows)>SCHEMA_VERSION or [r['version'] for r in rows]!=list(range(1,len(rows)+1)):raise SREError('UNSUPPORTED_STORAGE_VERSION')
            for r in rows:
                if r['migration_hash']!=hashlib.sha256(_migration(r['version']).encode()).hexdigest():raise SREError('MIGRATION_INTEGRITY')
            instance._verify_schema(len(rows))
            if len(rows)!=SCHEMA_VERSION:raise SREError('EXPLICIT_MIGRATION_REQUIRED')
            return instance
        except Exception:
            instance.close();raise SREError('STORAGE_OPEN_DENIED') from None

    @classmethod
    def upgrade(cls,path,authorizer,*,limits=Limits()):
        """Explicit local migration only. Never opens installed application DBs."""
        p=_path(path);instance=cls(p,authorizer,limits)
        try:
            rows=instance._db.execute('SELECT version,migration_hash FROM sre_metadata ORDER BY version').fetchall()
            version=len(rows)
            if not 1<=version<=SCHEMA_VERSION or [r['version'] for r in rows]!=list(range(1,version+1)):raise SREError('UNSUPPORTED_STORAGE_VERSION')
            instance._verify_schema(version)
            if any(r['migration_hash']!=hashlib.sha256(_migration(r['version']).encode()).hexdigest() for r in rows):raise SREError('MIGRATION_INTEGRITY')
            for v in range(version+1,SCHEMA_VERSION+1):instance._migrate(v)
            instance._verify_schema(SCHEMA_VERSION)
            return instance
        except Exception:
            instance.close();raise SREError('MIGRATION_DENIED') from None

    def _migrate(self,version):
        script=_migration(version)
        try:
            self._db.execute('BEGIN IMMEDIATE')
            for statement in script.split(';'):
                if statement.strip():self._db.execute(statement)
            self._db.execute('INSERT INTO sre_metadata VALUES (?,?)',(version,hashlib.sha256(script.encode()).hexdigest()))
            self._db.execute('COMMIT')
        except Exception:
            self._db.execute('ROLLBACK');raise

    def _verify_schema(self,version=SCHEMA_VERSION):
        if _schema(self._db)!=_expected(version) or self._db.execute('PRAGMA foreign_key_check').fetchone():raise SREError('SCHEMA_INTEGRITY')

    def close(self):self._db.close()

    def _authorize(self,access,tenant,app,action):return self.authorizer.check(access,tenant,app,action)

    @contextmanager
    def _transaction(self,access,tenant,app,action,*,write=False):
        actor=self._authorize(access,tenant,app,action)
        try:
            self._db.execute('BEGIN IMMEDIATE' if write else 'BEGIN')
            self._verify(tenant,app)
            yield actor
            self._authorize(access,tenant,app,action)
            self._db.execute('COMMIT')
        except Exception as error:
            if self._db.in_transaction:self._db.execute('ROLLBACK')
            if isinstance(error,SREError):raise
            raise SREError('STORAGE_OPERATION_FAILED') from None

    def _verify(self,tenant,app):
        self._verify_schema()
        migrations=self._db.execute('SELECT version,migration_hash FROM sre_metadata ORDER BY version').fetchall()
        if [tuple(r) for r in migrations]!=[(v,hashlib.sha256(_migration(v).encode()).hexdigest()) for v in range(1,SCHEMA_VERSION+1)]:raise SREError('MIGRATION_INTEGRITY')
        previous='0'*64;latest={};service_revisions={}
        rows=self._db.execute('SELECT * FROM sre_audit WHERE tenant=? AND app=? ORDER BY sequence',(tenant,app)).fetchall()
        for sequence,row in enumerate(rows,1):
            doc=json.loads(row['document'])
            if row['sequence']!=sequence or digest(doc)!=row['digest'] or doc['previous_hash']!=previous or (doc['tenant_id'],doc['application_id'])!=(tenant,app):raise SREError('AUDIT_INTEGRITY')
            previous=row['digest'];latest[(doc['entity_type'],doc['entity_id'])]=doc['entity_hash']
            if doc['entity_type']=='service':service_revisions[doc['entity_id']]=service_revisions.get(doc['entity_id'],0)+1
        for entity,table in [('service','sre_services'),('observation','sre_observations'),('validation','sre_validations'),('dependency','sre_dependencies'),('incident','sre_incidents')]:
            found=set()
            for row in self._db.execute(f'SELECT * FROM {table} WHERE tenant=? AND app=?',(tenant,app)):
                doc=json.loads(row['document']);found.add(row['id'])
                if (doc['tenant_id'],doc['application_id'])!=(tenant,app) or digest(doc)!=row['digest'] or latest.get((entity,row['id']))!=row['digest']:raise SREError('EVIDENCE_INTEGRITY')
                identity_key={'service':'service_id','observation':'observation_id','validation':'observation_id','dependency':'dependency_id','incident':'incident_id'}[entity]
                if doc[identity_key]!=row['id']:raise SREError('INDEX_INTEGRITY')
                if entity in ('observation','incident') and doc['service_id']!=row['service']:raise SREError('INDEX_INTEGRITY')
                if entity=='observation' and (doc['source_timestamp']!=row['source_time'] or doc['ingested_at']!=row['ingested_at']):raise SREError('INDEX_INTEGRITY')
                if entity=='dependency' and (doc['source_service_id']!=row['source'] or doc['dependent_service_id']!=row['dependent']):raise SREError('INDEX_INTEGRITY')
                if entity=='service' and row['revision']!=service_revisions.get(row['id'],0):raise SREError('REVISION_INTEGRITY')
            if found!={key[1] for key in latest if key[0]==entity}:raise SREError('MISSING_EVIDENCE_ROW')
        return previous

    def _quota(self,table,tenant,app,maximum):
        if self._db.execute(f'SELECT COUNT(*) FROM {table} WHERE tenant=? AND app=?',(tenant,app)).fetchone()[0]>=maximum:raise SREError('RETENTION_CAPACITY_REACHED')

    def _audit(self,tenant,app,actor,action,entity,id,hash,at):
        self._quota('sre_audit',tenant,app,self.limits.audit)
        row=self._db.execute('SELECT sequence,digest FROM sre_audit WHERE tenant=? AND app=? ORDER BY sequence DESC LIMIT 1',(tenant,app)).fetchone()
        seq=row['sequence']+1 if row else 1
        doc={'schema_version':1,'tenant_id':tenant,'application_id':app,'sequence':seq,'actor_id':actor,'action':action,'entity_type':entity,'entity_id':id,'entity_hash':hash,'timestamp':at,'previous_hash':row['digest'] if row else '0'*64}
        self._db.execute('INSERT INTO sre_audit VALUES (?,?,?,?,?)',(tenant,app,seq,canonical(doc),digest(doc)))

    def _service(self,tenant,app,id):
        identifier(id);r=self._db.execute('SELECT * FROM sre_services WHERE tenant=? AND app=? AND id=?',(tenant,app,id)).fetchone()
        if not r:raise SREError('SERVICE_UNAVAILABLE')
        return r

    def register_service(self,access,value):
        r=service_record(value);t,a,id=r['tenant_id'],r['application_id'],r['service_id']
        with self._transaction(access,t,a,'configure',write=True) as actor:
            existing=self._db.execute('SELECT digest FROM sre_services WHERE tenant=? AND app=? AND id=?',(t,a,id)).fetchone()
            if existing:
                if existing[0]==digest(r):return {'status':'DUPLICATE','service_id':id}
                raise SREError('REGISTRATION_CONFLICT')
            self._quota('sre_services',t,a,self.limits.services)
            self._db.execute('INSERT INTO sre_services VALUES (?,?,?,?,?,1)',(t,a,id,canonical(r),digest(r)))
            self._audit(t,a,actor,'REGISTER','service',id,digest(r),r['registered_at'])
        return {'status':'REGISTERED','service_id':id}

    def update_service(self,access,tenant,app,id,patch,expected_revision,updated_at):
        if type(patch) is not dict or not patch or set(patch)-{'service_name','monitoring_enabled','health_policy','configuration_ref'} or type(expected_revision) is not int:raise SREError('INVALID_SERVICE_UPDATE')
        at=timestamp(updated_at)
        with self._transaction(access,tenant,app,'configure',write=True) as actor:
            row=self._service(tenant,app,id);doc=json.loads(row['document'])
            if row['revision']!=expected_revision or at<doc['updated_at']:raise SREError('STALE_CONFIGURATION')
            doc.update(patch);doc['updated_at']=at;doc=service_record(doc)
            self._db.execute('UPDATE sre_services SET document=?,digest=?,revision=revision+1 WHERE tenant=? AND app=? AND id=?',(canonical(doc),digest(doc),tenant,app,id))
            self._audit(tenant,app,actor,'UPDATE','service',id,digest(doc),at)
        return {'status':'UPDATED','revision':expected_revision+1}

    def services(self,access,tenant,app):
        with self._transaction(access,tenant,app,'read'):
            result=[]
            for row in self._db.execute('SELECT * FROM sre_services WHERE tenant=? AND app=? ORDER BY id',(tenant,app)):
                d=json.loads(row['document']);d['revision']=row['revision']
                d['dependency_references']=[r[0] for r in self._db.execute('SELECT id FROM sre_dependencies WHERE tenant=? AND app=? AND dependent=? ORDER BY id',(tenant,app,row['id']))];result.append(d)
            return result

    def ingest(self,access,value):
        r=observation_record(value);t,a,id=r['tenant_id'],r['application_id'],r['observation_id']
        with self._transaction(access,t,a,'ingest',write=True) as actor:
            self._service(t,a,r['service_id'])
            existing=self._db.execute('SELECT digest FROM sre_observations WHERE tenant=? AND app=? AND id=?',(t,a,id)).fetchone()
            if existing:
                if existing[0]==digest(r):return {'status':'DUPLICATE','observation_id':id}
                raise SREError('OBSERVATION_CONFLICT')
            self._quota('sre_observations',t,a,self.limits.observations)
            self._db.execute('INSERT INTO sre_observations VALUES (?,?,?,?,?,?,?,?)',(t,a,id,r['service_id'],r['source_timestamp'],r['ingested_at'],canonical(r),digest(r)))
            self._audit(t,a,actor,'INGEST','observation',id,digest(r),r['ingested_at'])
        return {'status':'INGESTED','observation_id':id}

    def validate_observation(self,access,tenant,app,id,reviewed_at,evidence_ref):
        identifier(id);at=timestamp(reviewed_at);evidence(evidence_ref)
        with self._transaction(access,tenant,app,'validate',write=True) as actor:
            row=self._db.execute('SELECT * FROM sre_observations WHERE tenant=? AND app=? AND id=?',(tenant,app,id)).fetchone()
            if not row or at<row['ingested_at'] or json.loads(row['document'])['data_quality']=='INVALID':raise SREError('VALIDATION_UNAVAILABLE')
            doc={'schema_version':1,'tenant_id':tenant,'application_id':app,'observation_id':id,'observation_hash':row['digest'],'reviewer_id':actor,'reviewed_at':at,'evidence_ref':evidence_ref}
            prior=self._db.execute('SELECT digest FROM sre_validations WHERE tenant=? AND app=? AND id=?',(tenant,app,id)).fetchone()
            if prior:
                if prior[0]==digest(doc):return {'status':'DUPLICATE'}
                raise SREError('VALIDATION_CONFLICT')
            self._db.execute('INSERT INTO sre_validations VALUES (?,?,?,?,?)',(tenant,app,id,canonical(doc),digest(doc)))
            self._audit(tenant,app,actor,'VALIDATE','validation',id,digest(doc),at)
        return {'status':'VALIDATED'}

    def observations(self,access,tenant,app,service_id,limit=100):
        if type(limit) is not int or not 1<=limit<=10000:raise SREError('QUERY_LIMIT')
        with self._transaction(access,tenant,app,'read'):
            self._service(tenant,app,service_id);result=[]
            rows=self._db.execute('SELECT * FROM sre_observations WHERE tenant=? AND app=? AND service=? ORDER BY source_time DESC,id DESC LIMIT ?',(tenant,app,service_id,limit)).fetchall()
            for row in reversed(rows):
                d=json.loads(row['document']);v=self._db.execute('SELECT document FROM sre_validations WHERE tenant=? AND app=? AND id=?',(tenant,app,row['id'])).fetchone()
                d['source_data_quality']=d['data_quality'];d['record_sha256']=row['digest']
                if v:
                    d['validation']=json.loads(v[0]);d['data_quality']='VALIDATED'
                result.append(d)
            return result

    def add_dependency(self,access,value):
        r=record(value,('schema_version','tenant_id','application_id','dependency_id','source_service_id','dependent_service_id','relationship_type','created_at','evidence_ref'))
        for k in ('dependency_id','source_service_id','dependent_service_id'):identifier(r[k])
        if r['relationship_type'] not in ('REQUIRES','USES'):raise SREError('INVALID_DEPENDENCY_TYPE')
        r['created_at']=timestamp(r['created_at']);evidence(r['evidence_ref']);t,a,id=r['tenant_id'],r['application_id'],r['dependency_id']
        with self._transaction(access,t,a,'configure',write=True) as actor:
            for s in (r['source_service_id'],r['dependent_service_id']):self._service(t,a,s)
            existing=self._db.execute('SELECT digest FROM sre_dependencies WHERE tenant=? AND app=? AND id=?',(t,a,id)).fetchone()
            if existing:
                if existing[0]==digest(r):return {'status':'DUPLICATE'}
                raise SREError('DEPENDENCY_CONFLICT')
            edges=[(row[0],row[1]) for row in self._db.execute('SELECT source,dependent FROM sre_dependencies WHERE tenant=? AND app=?',(t,a))]
            source,dependent=r['source_service_id'],r['dependent_service_id'];frontier=[dependent];seen=set()
            while frontier:
                node=frontier.pop()
                if node==source:raise SREError('DEPENDENCY_CYCLE')
                if node not in seen:seen.add(node);frontier.extend(y for x,y in edges if x==node)
            self._quota('sre_dependencies',t,a,self.limits.dependencies)
            self._db.execute('INSERT INTO sre_dependencies VALUES (?,?,?,?,?,?,?)',(t,a,id,source,dependent,canonical(r),digest(r)))
            self._audit(t,a,actor,'ADD_DEPENDENCY','dependency',id,digest(r),r['created_at'])
        return {'status':'REGISTERED'}

    def dependencies(self,access,tenant,app):
        with self._transaction(access,tenant,app,'read'):
            return [json.loads(r[0]) for r in self._db.execute('SELECT document FROM sre_dependencies WHERE tenant=? AND app=? ORDER BY id',(tenant,app))]

    def create_incident(self,access,value):
        r=record(value,('schema_version','tenant_id','application_id','service_id','incident_id','initial_observation_ids','evidence_refs','status','created_at','updated_at'))
        for k in ('service_id','incident_id'):identifier(r[k])
        if r['status']!='DRAFT' or type(r['initial_observation_ids']) is not list or not 1<=len(r['initial_observation_ids'])<=100 or any(type(x) is not str for x in r['initial_observation_ids']) or len(set(r['initial_observation_ids']))!=len(r['initial_observation_ids']) or type(r['evidence_refs']) is not list or not 1<=len(r['evidence_refs'])<=100:raise SREError('MANUAL_INCIDENT_DRAFT_REQUIRED')
        for x in r['evidence_refs']:evidence(x)
        for k in ('created_at','updated_at'):r[k]=timestamp(r[k])
        if r['updated_at']!=r['created_at']:raise SREError('INCIDENT_CREATION_TIME')
        t,a,id=r['tenant_id'],r['application_id'],r['incident_id']
        with self._transaction(access,t,a,'incident',write=True) as actor:
            self._service(t,a,r['service_id'])
            for ref in r['initial_observation_ids']:
                identifier(ref)
                if not self._db.execute('SELECT 1 FROM sre_observations WHERE tenant=? AND app=? AND id=? AND service=?',(t,a,ref,r['service_id'])).fetchone():raise SREError('INCIDENT_EVIDENCE_UNAVAILABLE')
            existing=self._db.execute('SELECT digest FROM sre_incidents WHERE tenant=? AND app=? AND id=?',(t,a,id)).fetchone()
            if existing:
                if existing[0]==digest(r):return {'status':'DUPLICATE'}
                raise SREError('INCIDENT_CONFLICT')
            self._quota('sre_incidents',t,a,self.limits.incidents)
            self._db.execute('INSERT INTO sre_incidents VALUES (?,?,?,?,?,?)',(t,a,id,r['service_id'],canonical(r),digest(r)))
            self._audit(t,a,actor,'CREATE_DRAFT','incident',id,digest(r),r['created_at'])
        return {'status':'DRAFT'}

    def incidents(self,access,tenant,app):
        with self._transaction(access,tenant,app,'read'):
            return [json.loads(r[0]) for r in self._db.execute('SELECT document FROM sre_incidents WHERE tenant=? AND app=? ORDER BY id',(tenant,app))]

    def audit(self,access,tenant,app):
        with self._transaction(access,tenant,app,'read'):
            return [dict(json.loads(r['document']),record_sha256=r['digest']) for r in self._db.execute('SELECT document,digest FROM sre_audit WHERE tenant=? AND app=? ORDER BY sequence',(tenant,app))]

    def verify_integrity(self,access,tenant,app):
        with self._transaction(access,tenant,app,'read'):
            return {'status':'VERIFIED_BYTE_INTEGRITY','scope':[tenant,app],'audit_head':self._verify(tenant,app),'semantic_accuracy':'NOT_ESTABLISHED'}

    def health(self,access,tenant,app,service_id,*,evaluated_at):
        from .health import evaluate_health
        # Both snapshots and reauthorization share one read transaction.
        with self._transaction(access,tenant,app,'read'):
            row=self._service(tenant,app,service_id);service=json.loads(row['document']);observations=[]
            for r in self._db.execute('SELECT o.document,v.document AS review FROM sre_observations o LEFT JOIN sre_validations v ON v.tenant=o.tenant AND v.app=o.app AND v.id=o.id WHERE o.tenant=? AND o.app=? AND o.service=? ORDER BY o.source_time,o.id',(tenant,app,service_id)):
                d=json.loads(r['document'])
                if r['review'] and json.loads(r['review'])['reviewed_at']<=timestamp(evaluated_at):d['data_quality']='VALIDATED'
                observations.append(d)
            return evaluate_health(service,observations,evaluated_at=evaluated_at)

    def collect_local(self,access,tenant,app,*,observed_at,observation_id,correlation_id):
        from .local_adapter import collect_local_observation
        self._authorize(access,tenant,app,'ingest');self._authorize(access,tenant,app,'validate')
        with self._transaction(access,tenant,app,'read'):
            service=json.loads(self._service(tenant,app,'sentinel-api')['document'])
        claim=collect_local_observation(service,observed_at=timestamp(observed_at),observation_id=observation_id,correlation_id=correlation_id)
        self.ingest(access,claim)
        self.validate_observation(access,tenant,app,observation_id,claim['ingested_at'],claim['evidence_ref'])
        return {'status':'LOCAL_LIVENESS_OBSERVED','observation_id':observation_id,'claim_scope':'PROCESS_LIVENESS_ONLY',**GOVERNANCE}

    def investigation_package(self,access,tenant,app,service_id):
        """No investigation is launched; scoped immutable-by-digest handoff only."""
        with self._transaction(access,tenant,app,'read'):
            service=json.loads(self._service(tenant,app,service_id)['document'])
            observations=[json.loads(r[0]) for r in self._db.execute('SELECT document FROM sre_observations WHERE tenant=? AND app=? AND service=? ORDER BY source_time DESC,id DESC LIMIT 100',(tenant,app,service_id))]
            body={'schema_version':1,'tenant_id':tenant,'application_id':app,'service':service,'source_claims':list(reversed(observations)),'audit_head':self._verify(tenant,app),'capabilities_active':False,'governance':dict(GOVERNANCE)}
            return {'package':body,'sha256':digest(body)}

    def investigation_snapshot(self,access,tenant,application,service_id,*,evaluated_at,observation_ids=None,incident_id=None,max_observations=100,max_dependencies=128):
        """Atomic explicit selection; health uses complete service context."""
        from .health import evaluate_health
        at=timestamp(evaluated_at)
        if (observation_ids is None)==(incident_id is None):raise SREError('EXPLICIT_SELECTION_REQUIRED')
        if type(max_observations) is not int or not 1<=max_observations<=100 or type(max_dependencies) is not int or not 0<=max_dependencies<=128:raise SREError('QUERY_LIMIT')
        with self._transaction(access,tenant,application,'read'):
            service=json.loads(self._service(tenant,application,service_id)['document']);incident=None
            if incident_id is not None:
                identifier(incident_id)
                row=self._db.execute('SELECT document FROM sre_incidents WHERE tenant=? AND app=? AND id=? AND service=?',(tenant,application,incident_id,service_id)).fetchone()
                if not row:raise SREError('INCIDENT_UNAVAILABLE')
                incident=json.loads(row[0]);observation_ids=incident['initial_observation_ids']
            if type(observation_ids) is not list or not 1<=len(observation_ids)<=max_observations or any(type(x) is not str for x in observation_ids) or len(set(observation_ids))!=len(observation_ids):raise SREError('INVALID_SELECTION')
            for value in observation_ids:identifier(value)
            all_observations=[];selected=[]
            for row in self._db.execute('SELECT o.*,v.document AS review FROM sre_observations o LEFT JOIN sre_validations v ON v.tenant=o.tenant AND v.app=o.app AND v.id=o.id WHERE o.tenant=? AND o.app=? AND o.service=? ORDER BY o.source_time,o.id',(tenant,application,service_id)):
                doc=json.loads(row['document']);doc['source_data_quality']=doc['data_quality'];doc['record_sha256']=row['digest']
                if row['review'] and json.loads(row['review'])['reviewed_at']<=at:
                    doc['validation']=json.loads(row['review']);doc['data_quality']='VALIDATED'
                all_observations.append(doc)
                if doc['observation_id'] in observation_ids:selected.append(doc)
            if len(selected)!=len(observation_ids):raise SREError('EVIDENCE_UNAVAILABLE')
            dependencies=[json.loads(row[0]) for row in self._db.execute('SELECT document FROM sre_dependencies WHERE tenant=? AND app=? AND (source=? OR dependent=?) ORDER BY id',(tenant,application,service_id,service_id))]
            if len(dependencies)>max_dependencies:raise SREError('QUERY_LIMIT')
            body={'schema_version':1,'scope':{'tenant_id':tenant,'application_id':application,'service_id':service_id},'service':service,'evaluated_at':at,'selection':{'kind':'INCIDENT' if incident_id else 'OBSERVATIONS','observation_ids':sorted(observation_ids),'incident_id':incident_id},'observations':selected,'health':evaluate_health(service,all_observations,evaluated_at=at),'dependencies':dependencies,'incident':incident,'audit_head':self._verify(tenant,application)}
            return dict(body,snapshot_sha256=digest(body))
