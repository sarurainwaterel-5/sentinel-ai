/** Durable synthetic history only. SQLite is the sole authority for this store. */
import {DatabaseSync} from 'node:sqlite';
import {readFileSync,openSync,closeSync,lstatSync,unlinkSync,realpathSync} from 'node:fs';
import {resolve,dirname} from 'node:path';
import {createHash} from 'node:crypto';
import {validateWire,createHarness,verifyJournal,VERSION} from './protocol.mjs';
const authority=()=>({advisory_only:true,execution_authorized:false,live_authorized:false});
const hash=s=>createHash('sha256').update(s).digest('hex');
// Storage envelopes include canonical wire as a string and a larger history array.
// This does not change Phase 1 wire bounds or its validator/canonicalizer.
export function storageCanonical(v,depth=0){
 if(depth>24)throw Error('STORE_BOUNDS');
 if(v===null||typeof v==='boolean')return JSON.stringify(v);
 if(typeof v==='number'&&Number.isSafeInteger(v))return JSON.stringify(v);
 if(typeof v==='string'&&v.length<=131072&&!/[\uD800-\uDFFF]/u.test(v))return JSON.stringify(v);
 if(Array.isArray(v)&&v.length<=4096)return '['+v.map(x=>storageCanonical(x,depth+1)).join(',')+']';
 if(v&&typeof v==='object'&&Object.getPrototypeOf(v)===Object.prototype&&Object.keys(v).length<=128)return '{'+Object.keys(v).sort().map(k=>storageCanonical(k,depth+1)+':'+storageCanonical(v[k],depth+1)).join(',')+'}';
 throw Error('STORE_BOUNDS');
}
const canonical=storageCanonical,digest=v=>hash(storageCanonical(v));
const migration=()=>readFileSync(new URL('./migrations/001-durable.sql',import.meta.url),'utf8');
const utc=s=>typeof s==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s))&&new Date(s).toISOString()===s;
const copy=x=>JSON.parse(canonical(x));
const denied=(code,extra={})=>({status:code,assessment:null,authority:authority(),...extra});
const MAX_RECORDS=4096;
function dependencies() {
 return {evaluator_sha256:hash(readFileSync(new URL('./protocol.mjs',import.meta.url))),schema_sha256:hash(readFileSync(new URL('./proposal-v1.schema.json',import.meta.url))),wrapper_sha256:hash(readFileSync(new URL('./durable.mjs',import.meta.url))),node_version:process.versions.node};
}
function filePath(path,exists=true) {
 if(typeof path!=='string'||!path||path===':memory:')throw Error('EXPLICIT_DISK_PATH_REQUIRED');
 const full=resolve(path),parent=dirname(full);
 if(realpathSync(parent)!==parent)throw Error('SYMLINK_PATH_REJECTED');
 const directory=lstatSync(parent);
 if(!directory.isDirectory()||(directory.mode&0o077)!==0)throw Error('PRIVATE_DIRECTORY_REQUIRED');
 if(exists){const f=lstatSync(full);if(!f.isFile()||f.isSymbolicLink()||(f.mode&0o077)!==0)throw Error('PRIVATE_REGULAR_DATABASE_REQUIRED');}
 return full;
}
function configure(db){db.exec('PRAGMA busy_timeout=5000; PRAGMA foreign_keys=ON; PRAGMA synchronous=FULL; PRAGMA trusted_schema=OFF;');}
const shape=db=>db.prepare("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name").all().map(x=>({...x}));
let expectedShape;
function schemaShape(){
 if(!expectedShape){const db=new DatabaseSync(':memory:');try{db.exec(migration());expectedShape=canonical(shape(db));}finally{db.close();}}
 return expectedShape;
}
function verifySchema(db){
 if(db.prepare('PRAGMA user_version').get().user_version!==1||canonical(shape(db))!==schemaShape())throw Error('SCHEMA_INTEGRITY');
 const rows=db.prepare('SELECT * FROM schema_migrations').all();
 if(rows.length!==1||rows[0].version!==1||rows[0].schema_sha256!==hash(migration()))throw Error('SCHEMA_INTEGRITY');
 if(db.prepare('PRAGMA quick_check').get().quick_check!=='ok')throw Error('DATABASE_INTEGRITY');
}
export function initializeStore({path}={}) {
 let full,created=false,db;
 try {
  full=filePath(path,false);const fd=openSync(full,'wx',0o600);closeSync(fd);created=true;
  db=new DatabaseSync(full);configure(db);db.exec('PRAGMA journal_mode=DELETE; BEGIN IMMEDIATE;');
  db.exec(migration());db.prepare('INSERT INTO schema_migrations(version,schema_sha256) VALUES(1,?)').run(hash(migration()));db.exec('COMMIT');
  verifySchema(db);return {status:'INITIALIZED',schema_version:1,authority:authority()};
 }catch{return denied('INITIALIZATION_FAILED');}
 finally{if(db){try{db.close();}catch{}}if(created&&full){try{const check=new DatabaseSync(full,{readOnly:true});try{verifySchema(check);}finally{check.close();}}catch{try{unlinkSync(full);}catch{}}}}
}
function inspect(db) {
 verifySchema(db);
 const rows=db.prepare('SELECT * FROM audit_records ORDER BY seq').all();
 if(rows.length>MAX_RECORDS)throw Error('STORE_BOUNDS');
 let previous='0'.repeat(64);const records=[],decisions=new Map();
 for(const row of rows){
  if(row.seq!==records.length+1||row.previous_hash!==previous||row.payload.length>131072)throw Error('AUDIT_INTEGRITY');
  const payload=JSON.parse(row.payload);
  if(canonical(payload)!==row.payload||payload.authority?.advisory_only!==true||payload.authority?.execution_authorized!==false||payload.authority?.live_authorized!==false)throw Error('AUDIT_INTEGRITY');
  const base={seq:row.seq,kind:row.kind,record_id:row.record_id,payload,previous_hash:row.previous_hash};
  if(digest(base)!==row.record_hash||row.record_id!=='record:'+digest({kind:row.kind,payload,seq:row.seq,previous_hash:previous}))throw Error('AUDIT_INTEGRITY');
  if(row.kind==='DECISION'||row.kind==='INVALID'){
   if(typeof payload.wire!=='string'||hash(payload.wire)!==payload.input_hash||!verifyJournal([payload.assessment])||payload.assessment.input_hash!==payload.input_hash)throw Error('PAYLOAD_INTEGRITY');
  }
  if(row.kind==='DECISION'){
   const p=JSON.parse(payload.wire);
   if(p.proposal_id!==payload.proposal_id||p.event_id!==payload.event_id||p.correlation_id!==payload.correlation_id||p.proposal_id!==payload.assessment.proposal_id)throw Error('IDENTITY_INTEGRITY');
   if(payload.supersedes!==null&&![...decisions.values()].some(d=>d.assessment.assessment_id===payload.supersedes))throw Error('SUPERSESSION_INTEGRITY');
   decisions.set(row.seq,payload);
  }
  if(row.kind==='REPLAY'||row.kind==='CONFLICT'){
   const original=records.find(r=>r.kind==='DECISION'&&r.record_id===payload.original_record_id);
   if(!original||original.payload.assessment.assessment_id!==payload.original_assessment_id)throw Error('HISTORICAL_REFERENCE_INTEGRITY');
   if(row.kind==='REPLAY'&&(!['REPLAY_MATCH','REPLAY_MISMATCH','REPLAY_UNAVAILABLE'].includes(payload.status)||(payload.reproduced_assessment!==null&&!verifyJournal([payload.reproduced_assessment]))))throw Error('REPLAY_INTEGRITY');
  }
  records.push({...base,record_hash:row.record_hash});previous=row.record_hash;
 }
 const claims=db.prepare('SELECT * FROM proposal_claims ORDER BY record_seq').all();
 if(claims.length!==decisions.size)throw Error('CLAIM_INTEGRITY');
 for(const c of claims){const p=decisions.get(c.record_seq);if(!p||p.proposal_id!==c.proposal_id||p.event_id!==c.event_id||p.input_hash!==c.input_hash||p.correlation_id!==c.correlation_id||p.assessment.assessment_id!==c.assessment_id)throw Error('CLAIM_INTEGRITY');}
 return {records,claims};
}
function append(db,records,kind,payload) {
 if(records.length>=MAX_RECORDS)throw Error('STORE_CAPACITY');
 const seq=records.length+1,previous_hash=records.at(-1)?.record_hash??'0'.repeat(64);
 const record_id='record:'+digest({kind,payload,seq,previous_hash});
 const base={seq,kind,record_id,payload,previous_hash},record_hash=digest(base);
 db.prepare('INSERT INTO audit_records(seq,kind,record_id,payload,previous_hash,record_hash) VALUES(?,?,?,?,?,?)').run(seq,kind,record_id,canonical(payload),previous_hash,record_hash);
 return {...base,record_hash};
}
export function openDurableStore({path}={}) {
 let db;
 try{const full=filePath(path);db=new DatabaseSync(full);configure(db);verifySchema(db);}catch{if(db){try{db.close();}catch{}}return {...denied('STORAGE_UNAVAILABLE'),store:null};}
 let closed=false;
 function transaction(work){
  if(closed)return denied('STORAGE_UNAVAILABLE');
  try{db.exec('BEGIN IMMEDIATE');const history=inspect(db),result=work(history);db.exec('COMMIT');return result;}
  catch{try{db.exec('ROLLBACK');}catch{}return denied('STORAGE_FAILURE_OR_INTEGRITY_ERROR');}
 }
 function submit(wire,options={}){
  if(!options||typeof options!=='object'||Array.isArray(options))return denied('INVALID_REQUEST');
  const {evaluationTime,serviceAvailable=true,supersedes=null}=options;
  if(typeof wire!=='string'||Buffer.byteLength(wire)>32768||!utc(evaluationTime)||typeof serviceAvailable!=='boolean'||(supersedes!==null&&typeof supersedes!=='string'))return denied('INVALID_REQUEST');
  return transaction(({records,claims})=>{
   const {value:p}=validateWire(wire),input_hash=hash(wire);
   let identity=p;
   if(!identity){try{const raw=JSON.parse(wire);const bounded=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(x);identity={proposal_id:bounded(raw?.proposal_id)?raw.proposal_id:null,event_id:bounded(raw?.event_id)?raw.event_id:null};}catch{identity={};}}
   {
    const identical=claims.find(c=>c.input_hash===input_hash&&records[c.record_seq-1].payload.wire===wire);
    const existing=claims.find(c=>c.proposal_id===identity.proposal_id),event=claims.find(c=>c.event_id===identity.event_id);
    if(identical){
     const original=records[identical.record_seq-1];
     if(original.payload.supersedes!==supersedes)return conflict('SUPERSESSION_CONTEXT_CONFLICT',original);
     return {status:'DUPLICATE',assessment:copy(original.payload.assessment),record:copy(original),authority:authority()};
    }
    if(existing||event)return conflict(existing?'PROPOSAL_ID_CONFLICT':'EVENT_ID_CONFLICT',records[(existing??event).record_seq-1]);
   }
   function conflict(reason,original){const record=append(db,records,'CONFLICT',{reason,input_hash,original_record_id:original.record_id,original_assessment_id:original.payload.assessment.assessment_id,proposal_id:identity.proposal_id??null,evaluated_at:evaluationTime,authority:authority()});return denied('CONFLICT',{reason,record});}
   if(supersedes!==null&&!records.some(r=>r.kind==='DECISION'&&r.payload.assessment.assessment_id===supersedes))return denied('SUPERSEDED_RECORD_NOT_FOUND');
   const assessment=createHarness({evaluationTime,serviceAvailable}).assess(wire).assessment;
   const context={contract_version:VERSION,...dependencies(),evidence_inventory_sha256:hash(canonical(p?.evidence??[])),evaluation_time:evaluationTime,service_available:serviceAvailable,evaluator_context:'ISOLATED_INITIAL_PROPOSAL'};
   const payload={wire,input_hash,proposal_id:p?.proposal_id??null,event_id:p?.event_id??null,correlation_id:p?.correlation_id??null,contract_version:VERSION,context,assessment,supersedes,authority:authority()};
   const record=append(db,records,p?'DECISION':'INVALID',payload);
   if(p)db.prepare('INSERT INTO proposal_claims(proposal_id,event_id,input_hash,assessment_id,record_seq,correlation_id) VALUES(?,?,?,?,?,?)').run(p.proposal_id,p.event_id,input_hash,assessment.assessment_id,record.seq,p.correlation_id);
   return {status:p?'STORED':'INVALID',assessment,record,authority:authority()};
  });
 }
 function replay(assessmentId,options={}){
  if(!options||typeof options!=='object'||Array.isArray(options))return denied('INVALID_REQUEST');
  const {replayedAt}=options;
  if(typeof assessmentId!=='string'||!utc(replayedAt))return denied('INVALID_REQUEST');
  const outcome=transaction(({records})=>{
   const original=records.find(r=>r.kind==='DECISION'&&r.payload.assessment.assessment_id===assessmentId);
   if(!original)return denied('ASSESSMENT_NOT_FOUND');
   const p=original.payload;let status='REPLAY_UNAVAILABLE',reason='HISTORICAL_DEPENDENCIES_UNAVAILABLE',reproduced=null;
   try{
    if(p.context.contract_version!==VERSION||p.contract_version!==VERSION)reason='UNSUPPORTED_HISTORICAL_CONTRACT';
    else if(canonical(dependencies())!==canonical({evaluator_sha256:p.context.evaluator_sha256,schema_sha256:p.context.schema_sha256,wrapper_sha256:p.context.wrapper_sha256,node_version:p.context.node_version}))reason='EVALUATOR_OR_SCHEMA_UNAVAILABLE';
    else if(!validateWire(p.wire).value||hash(canonical(validateWire(p.wire).value.evidence))!==p.context.evidence_inventory_sha256)reason='HISTORICAL_EVIDENCE_UNAVAILABLE';
    else {
     const result=createHarness({evaluationTime:p.context.evaluation_time,serviceAvailable:p.context.service_available}).assess(p.wire).assessment;
     reproduced=result;status=canonical(result)===canonical(p.assessment)?'REPLAY_MATCH':'REPLAY_MISMATCH';reason=status==='REPLAY_MATCH'?'EXACT_HISTORICAL_MATCH':'ASSESSMENT_DIFFERS';
    }
   }catch{}
   const payload={original_record_id:original.record_id,original_assessment_id:assessmentId,replayed_at:replayedAt,status,reason,reproduced_assessment:reproduced,authority:authority()};
   const record=append(db,records,'REPLAY',payload);
   return {status,reason,assessment:null,reproduced_assessment:reproduced,record,recorded:true,authority:authority()};
  });
  return outcome.status==='STORAGE_FAILURE_OR_INTEGRITY_ERROR'||outcome.status==='STORAGE_UNAVAILABLE'?denied('REPLAY_UNAVAILABLE',{reason:outcome.status,recorded:null}):outcome;
 }
 return {status:'OPEN',store:Object.freeze({submit,replay,history:()=>transaction(({records})=>({status:'VERIFIED',records:copy(records),authority:authority()})),close:()=>{if(!closed){closed=true;db.close();}}}),authority:authority()};
}
