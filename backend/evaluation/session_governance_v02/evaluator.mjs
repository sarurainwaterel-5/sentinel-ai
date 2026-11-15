// Isolated offline fixture interpreter. Not imported by any application/runtime.
import importedSpec from './specification.json' with {type:'json'};
import {createHash} from 'node:crypto';
const freeze=x=>{if(x&&typeof x==='object'){Object.values(x).forEach(freeze);Object.freeze(x);}return x;};
const spec=freeze(structuredClone(importedSpec));
export const VERSION=spec.version;
export function canonical(x){if(x===null)return 'null';if(typeof x==='number'){if(!Number.isFinite(x))throw Error('NON_JSON_NUMBER');return JSON.stringify(x);}if(typeof x==='string'||typeof x==='boolean')return JSON.stringify(x);if(typeof x!=='object')throw Error('NON_JSON_VALUE');if(Array.isArray(x))return '['+x.map(canonical).join(',')+']';return '{'+Object.keys(x).sort().map(k=>JSON.stringify(k)+':'+canonical(x[k])).join(',')+'}';}
export const hash=x=>createHash('sha256').update(typeof x==='string'?x:canonical(x)).digest('hex');
export const utc=x=>typeof x==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(x)&&Number.isFinite(Date.parse(x))&&new Date(x).toISOString()===x;
const id=x=>typeof x==='string'&&/^[a-zA-Z0-9_.:-]{1,128}$/.test(x);
const shape=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
export function local(t,zone='America/Chicago'){const p=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:zone,year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).formatToParts(new Date(t)).map(x=>[x.type,x.value]));return {date:`${p.year}-${p.month}-${p.day}`,clock:`${p.hour}:${p.minute}:${p.second}`};}
export function normalizeNewYorkTimestamp(t){if(typeof t!=='string'||!/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}[+-]\d\d:\d\d$/.test(t)||!Number.isFinite(Date.parse(t)))return null;const instant=new Date(t).toISOString(),ny=local(instant,'America/New_York');return `${ny.date}T${ny.clock}`===t.slice(0,19)?instant:null;}
const authority=()=>({execution_authorization:'DENIED',execution_authorized:false,live_authorized:false});
function structure(p){
 if(!shape(p,['version','case_id','at','event','calendar','account','setup','prior_setup','position'])||p.version!==VERSION||!id(p.case_id)||!utc(p.at)||!['DISCOVER','ENTRY','MANAGE'].includes(p.event))return 'INVALID_ENVELOPE';
 for(const s of [p.setup,p.prior_setup])if(s!==null&&(!shape(s,['id','event_id','model_version','origin','discovered_at','event_at','event_available_at','expires_at','state','discovery_evidence_ref','expiry_evidence_ref'])||![s.id,s.event_id,s.model_version].every(id)||!['MORNING','AFTERNOON'].includes(s.origin)||![s.discovered_at,s.event_at,s.event_available_at].every(utc)||(s.expires_at!==null&&!utc(s.expires_at))||!['DISCOVERED','DEVELOPING','CONFIRMED','INVALIDATED','EXPIRED'].includes(s.state)||![s.discovery_evidence_ref,s.expiry_evidence_ref].every(x=>x===null||id(x))))return 'INVALID_SETUP';
 const pos=p.position;if(pos!==null&&(!shape(pos,['id','opened_at','state','exit'])||!id(pos.id)||!utc(pos.opened_at)||!['OPEN','CLOSED'].includes(pos.state)||(pos.exit!==null&&(!shape(pos.exit,['kind','at','available_at'])||!['TARGET','STOP'].includes(pos.exit.kind)||![pos.exit.at,pos.exit.available_at].every(utc)))))return 'INVALID_POSITION';
 return null;
}
function calendarAt(c,at){
 if(!shape(c,['id','version','source','available_at','valid_until','holiday_coverage','early_close_coverage','rollover_coverage','days'])||!id(c.id)||!id(c.version)||c.source!=='SYNTHETIC_FIXTURE'||![c.available_at,c.valid_until].every(utc)||c.available_at>at||c.valid_until<=at||!['holiday_coverage','early_close_coverage','rollover_coverage'].every(k=>c[k]==='TEST_COVERED')||!Array.isArray(c.days)||!c.days.length||c.days.length>4)return null;
 let previous=null;
 for(const day of c.days){if(!shape(day,['trading_day_id','policy_date','opens_at','closes_at','morning_opens_at'])||!id(day.trading_day_id)||!utc(day.policy_date+'T00:00:00.000Z')||![day.opens_at,day.closes_at].every(utc)||day.opens_at>=day.closes_at||(previous&&previous>day.opens_at)||(day.morning_opens_at!==null&&(!utc(day.morning_opens_at)||local(day.morning_opens_at).date!==day.policy_date||local(day.morning_opens_at).clock>=spec.morning_discovery_closes||day.morning_opens_at<day.opens_at||day.morning_opens_at>=day.closes_at)))return null;previous=day.closes_at;}
 const days=c.days.filter(x=>x.opens_at<=at&&at<x.closes_at);return days.length===1?days[0]:null;
}
function accountAt(a,c,day,at){return shape(a,['source','calendar_id','calendar_version','trading_day_id','as_of','available_at','valid_until','trades_today'])&&a.source==='SYNTHETIC_FIXTURE'&&a.calendar_id===c.id&&a.calendar_version===c.version&&a.trading_day_id===day.trading_day_id&&[a.as_of,a.available_at,a.valid_until].every(utc)&&a.as_of<=a.available_at&&a.available_at<=at&&a.valid_until>at&&Number.isSafeInteger(a.trades_today)&&a.trades_today>=0?a:null;}
function setupReason(s,prior,at,c,day,event){
 if(!s)return 'SETUP_REQUIRED';
 if(s.event_at>s.event_available_at||s.event_available_at>s.discovered_at||s.discovered_at>at)return 'SETUP_EVIDENCE_UNAVAILABLE';
 // Discovery must be causally linked to the supplied qualifying event, never re-dated.
 if(s.discovered_at!==s.event_available_at)return 'DISCOVERY_EVENT_ALIGNMENT_UNRESOLVED';
 if(prior){const identity=['id','event_id','model_version','origin','discovered_at','event_at','event_available_at','expires_at','discovery_evidence_ref','expiry_evidence_ref'];if(identity.some(k=>s[k]!==prior[k]))return 'ORIGINAL_SETUP_OR_EXPIRY_CHANGED';if(['EXPIRED','INVALIDATED'].includes(prior.state)&&s.state!==prior.state)return 'TERMINAL_SETUP_REVIVAL';const rank={DISCOVERED:0,DEVELOPING:1,CONFIRMED:2,INVALIDATED:3,EXPIRED:3};if(rank[s.state]<rank[prior.state])return 'STATE_REGRESSION';if(prior.state!==s.state&&rank[prior.state]===3)return 'TERMINAL_STATE_REWRITE';}
 const discovered=local(s.discovered_at),now=local(at);
 if(discovered.date!==day.policy_date||now.date!==day.policy_date||!calendarAt(c,s.discovered_at)||calendarAt(c,s.discovered_at).trading_day_id!==day.trading_day_id)return 'SETUP_DAY_OR_CALENDAR_MISMATCH';
 if(s.origin==='MORNING'){if(!day.morning_opens_at)return 'MORNING_START_UNDEFINED';if(s.discovered_at<day.morning_opens_at||discovered.clock>=spec.morning_discovery_closes)return 'MORNING_DISCOVERY_CLOSED';if(now.clock>=spec.afternoon_opens)return 'MORNING_CARRYOVER_PROHIBITED';}
 else {if(discovered.clock<spec.afternoon_opens||discovered.clock>=spec.mandatory_flatten)return 'AFTERNOON_DISCOVERY_CLOSED';const ev=local(s.event_at);if(ev.date!==discovered.date||ev.clock<spec.afternoon_opens)return 'AFTERNOON_REQUIRES_NEW_EVENT';}
 if(s.state==='INVALIDATED')return 'SETUP_INVALIDATED';if(s.state==='EXPIRED')return 'SETUP_EXPIRED';
 if(s.expires_at===null||s.expiry_evidence_ref===null)return 'MODEL_EXPIRY_UNDEFINED';if(s.expires_at<=s.discovered_at)return 'NONFINITE_OR_NONPOSITIVE_EXPIRY';if(at>=s.expires_at)return 'SETUP_EXPIRED';
 if(s.discovery_evidence_ref===null)return 'MODEL_DISCOVERY_UNDEFINED';
 if(event==='DISCOVER'&&(at!==s.discovered_at||s.state!=='DISCOVERED'))return 'NEW_DISCOVERY_IDENTITY_REQUIRES_CURRENT_EVENT';
 if(event==='ENTRY'&&s.state!=='CONFIRMED')return 'SETUP_NOT_CONFIRMED';return null;
}
export function evaluateSession(p){
 let wire;try{wire=canonical(p);if(typeof wire!=='string'||Buffer.byteLength(wire)>32768)throw Error();}catch{return result(null,'INVALID','INVALID_OR_UNBOUNDED_JSON');}
 const error=structure(p);if(error)return result(p,'INVALID',error);
 const now=local(p.at),pos=p.position;
 if(p.event==='MANAGE'){
  if(!pos)return result(p,'INSUFFICIENT_EVIDENCE','POSITION_REQUIRED');
  if(pos.opened_at>p.at||local(pos.opened_at).date>now.date)return result(p,'INVALID','POSITION_FROM_FUTURE');
  if(pos.exit&&(pos.exit.at<pos.opened_at||pos.exit.available_at<pos.exit.at))return result(p,'INVALID','POSITION_EXIT_ORDER_INVALID');
  if(pos.state==='CLOSED')return result(p,'POSITION_ALREADY_CLOSED','NO_OPEN_POSITION');
  // Simulated known target/stop before the deadline is factual, never a routed order.
  if(pos.exit&&pos.exit.at<=p.at&&pos.exit.available_at<=p.at&&local(pos.exit.at).date===now.date&&local(pos.exit.at).clock<spec.mandatory_flatten)return result(p,'SIMULATED_PLAN_CLOSE',pos.exit.kind);
  if(local(pos.opened_at).date<now.date||now.clock>=spec.mandatory_flatten)return result(p,'MANDATORY_FLATTEN_CONDITION','DAILY_FLATTEN_REACHED');
  return result(p,'MAINTAIN_PREDEFINED_PLAN','ENTRY_CUTOFF_DOES_NOT_FLATTEN');
 }
 if(now.clock>=spec.mandatory_flatten)return result(p,'PROHIBITED','AT_OR_AFTER_FLATTEN');
 if(p.event==='DISCOVER'&&now.clock>=spec.morning_discovery_closes&&now.clock<spec.afternoon_opens)return result(p,'PROHIBITED','MORNING_DISCOVERY_CLOSED');
 if(p.event==='ENTRY'&&now.clock>=spec.morning_entry_closes&&now.clock<spec.afternoon_opens)return result(p,'PROHIBITED','MORNING_ENTRY_CLOSED');
 const day=calendarAt(p.calendar,p.at);if(!day)return result(p,'INSUFFICIENT_EVIDENCE','CALENDAR_UNAVAILABLE_OR_UNCOVERED');
 if(now.date!==day.policy_date)return result(p,'INSUFFICIENT_EVIDENCE','LOCAL_POLICY_DATE_UNCOVERED');
 const issue=setupReason(p.setup,p.prior_setup,p.at,p.calendar,day,p.event);if(issue)return result(p,['UNDEFINED','UNRESOLVED'].some(x=>issue.includes(x))?'INSUFFICIENT_EVIDENCE':'PROHIBITED',issue,day);
 if(p.event==='ENTRY'){
  if(pos?.state==='OPEN')return result(p,'PROHIBITED','EXISTING_EXPOSURE');
  const account=accountAt(p.account,p.calendar,day,p.at);if(!account)return result(p,'INSUFFICIENT_EVIDENCE','AUTHORITATIVE_COUNT_NOT_ESTABLISHED',day);
  if(account.trades_today>=1)return result(p,'PROHIBITED','EXCHANGE_DAY_TRADE_ALREADY_USED',day);
 }
 return result(p,'CONDITIONAL_RESEARCH_REVIEW','SYNTHETIC_TEMPORAL_CHECKS_ONLY',day);
}
function result(p,interpretation,reason,day=null){const body={spec_id:spec.id,spec_version:VERSION,spec_sha256:hash(spec),case_id:id(p?.case_id)?p.case_id:null,at:utc(p?.at)?p.at:null,input_sha256:p?hash(p):null,session_interpretation:interpretation,reason,trading_day_id:day?.trading_day_id??null,market_observations:'NOT_EVALUATED',strategy_compliance:'UNVERIFIED_MODEL_PREDICATES_NULL',account_risk_compliance:'NOT_AUTHENTICATED_SYNTHETIC_INPUT_ONLY',supervisory_assessment:'NOT_ISSUED_BY_FIXTURE_INTERPRETER',model_discovery_predicate:null,model_expiry_predicate:null,...authority()};return {...body,decision_id:'session:'+hash(body)};}
