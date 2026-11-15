/** Canonical owner: Sentinel AI. Synthetic, process-local, informational only. */
import {createHash} from 'node:crypto';
import schema from './proposal-v1.schema.json' with {type:'json'};
export const VERSION='sentinel.synthetic.proposal.v1';
export const OUTCOMES=Object.freeze(['OBSERVED','COMPLIANT','NON_COMPLIANT','INSUFFICIENT_EVIDENCE','REVIEW_REQUIRED','INVALID']);
const authority=()=>({advisory_only:true,execution_authorized:false,live_authorized:false});
const plain=v=>v!==null&&typeof v==='object'&&!Array.isArray(v);
export function canonical(v,depth=0) {
  if(depth>16) throw Error('BOUNDS');
  if(v===null||typeof v==='boolean') return JSON.stringify(v);
  if(typeof v==='number'&&Number.isSafeInteger(v))return JSON.stringify(v);
  if(typeof v==='string'&&v.length<=8192&&!/[\uD800-\uDFFF]/u.test(v))return JSON.stringify(v);
  if(Array.isArray(v)&&v.length<=128)return '['+v.map(x=>canonical(x,depth+1)).join(',')+']';
  if(plain(v)&&Object.keys(v).length<=128)return '{'+Object.keys(v).sort().map(k=>canonical(k,depth+1)+':'+canonical(v[k],depth+1)).join(',')+'}';
  throw Error('BOUNDS');
}
export const digest=v=>createHash('sha256').update(canonical(v)).digest('hex');
const hash=raw=>createHash('sha256').update(raw).digest('hex');
const utc=t=>typeof t==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(t)&&Number.isFinite(Date.parse(t))&&new Date(t).toISOString()===t;
function valid(v,s) {
  if('const'in s&&v!==s.const)return false;
  if(s.enum&&!s.enum.includes(v))return false;
  if(s.type==='object')return plain(v)&&s.required.every(k=>Object.hasOwn(v,k))&&Object.keys(v).every(k=>Object.hasOwn(s.properties,k))&&Object.entries(s.properties).every(([k,x])=>valid(v[k],x));
  if(s.type==='string')return typeof v==='string'&&v.length>=s.minLength&&v.length<=s.maxLength&&(!s.pattern||new RegExp(s.pattern).test(v));
  if(s.type==='integer')return Number.isSafeInteger(v)&&v>=s.minimum&&v<=s.maximum;
  if(s.type==='array')return Array.isArray(v)&&v.length<=s.maxItems&&(!s.uniqueItems||new Set(v.map(x=>canonical(x))).size===v.length)&&v.every(x=>valid(x,s.items));
  return true;
}
export function validateWire(raw) {
  let value=null;const errors=[];
  try {
    if(typeof raw!=='string'||Buffer.byteLength(raw)>32768)throw Error('BOUNDS');
    value=JSON.parse(raw);
    // Canonical wire form also rejects duplicate keys, nonfinite/unsafe numbers and ambiguous encodings.
    if(canonical(value)!==raw)errors.push('NON_CANONICAL_WIRE');
    if(!valid(value,schema))errors.push('SCHEMA_INVALID');
    if(plain(value)&&value.contract_version!==VERSION)errors.push('UNSUPPORTED_VERSION');
    if(!errors.length&&(!utc(value.occurred_at)||!utc(value.market_data_as_of)))errors.push('TIMESTAMP_INVALID');
  }catch {errors.push('INVALID_JSON_OR_BOUNDS');}
  return {value:errors.length?null:value,errors:[...new Set(errors)]};
}
export function createHarness({evaluationTime,serviceAvailable=true,maxRecords=256}={}) {
  if(!utc(evaluationTime)||typeof serviceAvailable!=='boolean'||!Number.isSafeInteger(maxRecords)||maxRecords<1||maxRecords>4096)throw Error('INVALID_HARNESS_CONFIGURATION');
  const events=new Map(),proposals=new Map(),records=[];
  const copy=v=>JSON.parse(canonical(v));
  function assess(raw) {
    const parsed=validateWire(raw),p=parsed.value;
    const inputHash=hash(typeof raw==='string'?raw:'INVALID_NON_STRING');
    if(p&&events.has(p.event_id)&&events.get(p.event_id).input_hash===inputHash)
      return {duplicate:true,assessment:copy(events.get(p.event_id).assessment)};
    if(records.length>=maxRecords)return {duplicate:false,assessment:null,error_code:'JOURNAL_CAPACITY_REACHED'};
    let errors=[...parsed.errors],findings=[],result='INVALID',strategy='UNVERIFIED',risk='UNVERIFIED';
    let advance=false,previous=p?proposals.get(p.proposal_id):null;
    if(p) {
      if(events.has(p.event_id))errors.push('EVENT_ID_CONFLICT');
      if(previous&&(previous.account_id!==p.account_id||previous.correlation_id!==p.correlation_id))errors.push('PROPOSAL_SCOPE_CONFLICT');
      if(p.event_type==='PROPOSAL_SUBMITTED'?(!!previous||p.revision!==1):(!previous||previous.state==='WITHDRAWN'||p.revision!==previous.revision+1))errors.push('INVALID_STATE_TRANSITION');
      if(previous&&p.occurred_at<previous.occurred_at)errors.push('EVENT_TIME_REGRESSION');
      if(p.occurred_at>evaluationTime||p.market_data_as_of>p.occurred_at)errors.push('FUTURE_TIMESTAMP');
      if(p.instrument.symbol!=='MNQ')errors.push('UNSUPPORTED_INSTRUMENT');
      if(new Set(p.evidence.map(e=>e.sha256)).size!==p.evidence.length)errors.push('DUPLICATE_EVIDENCE');
      if(p.evidence.some(e=>digest(e.body)!==e.sha256))errors.push('EVIDENCE_HASH_MISMATCH');
      const evidence=new Map(p.evidence.map(e=>[e.sha256,e.body]));
      const check=(refs,kind)=>refs.every(ref=>evidence.get(ref)?.kind===kind);
      if(!check(p.strategy.evidence_refs,'STRATEGY')||!check(p.risk.evidence_refs,'RISK'))errors.push('EVIDENCE_REFERENCE_INVALID');
      if(!errors.length) {
        advance=true;
        const missing=!p.strategy.evidence_refs.length||!p.risk.evidence_refs.length;
        const stale=Date.parse(evaluationTime)-Date.parse(p.market_data_as_of)>2000;
        const strategyConflict=p.strategy.evidence_refs.some(ref=>evidence.get(ref).policy_id!==p.strategy.strategy_id);
        const riskConflict=p.risk.evidence_refs.some(ref=>evidence.get(ref).policy_id!==p.risk.policy_id);
        const supportedStrategy=p.strategy.strategy_id==='synthetic-ict'&&p.strategy.version==='1';
        const supportedRisk=p.risk.policy_id==='synthetic-risk-v1';
        const geometry=p.direction==='long'?p.stop_ticks<p.entry_ticks&&p.entry_ticks<p.target_ticks:p.target_ticks<p.entry_ticks&&p.entry_ticks<p.stop_ticks;
        const loss=Math.abs(p.entry_ticks-p.stop_ticks)*50*p.quantity+p.risk.expected_costs_cents;
        const gain=Math.abs(p.target_ticks-p.entry_ticks)*50*p.quantity-p.risk.expected_costs_cents;
        const safeRisk=geometry&&p.quantity===1&&p.risk.max_loss_cents<=5000&&loss<=p.risk.max_loss_cents&&gain>=2*loss;
        if(missing)findings.push('MISSING_STRATEGY_OR_RISK_EVIDENCE');
        if(stale)findings.push('STALE_MARKET_DATA');
        if(strategyConflict)findings.push('CONFLICTING_STRATEGY_METADATA');
        if(riskConflict)findings.push('CONFLICTING_RISK_METADATA');
        if(!supportedStrategy||!supportedRisk)findings.push('UNSUPPORTED_SYNTHETIC_POLICY');
        if(!safeRisk)findings.push('SYNTHETIC_RISK_LIMIT_VIOLATION');
        strategy=missing?'UNVERIFIED':strategyConflict?'FAIL':supportedStrategy?'SYNTHETIC_CHECK_PASS':'UNVERIFIED';
        risk=missing?'UNVERIFIED':riskConflict||!safeRisk?'FAIL':supportedRisk?'SYNTHETIC_CHECK_PASS':'UNVERIFIED';
        result=strategyConflict||riskConflict||!safeRisk?'NON_COMPLIANT':missing||stale?'INSUFFICIENT_EVIDENCE':!supportedStrategy||!supportedRisk?'REVIEW_REQUIRED':p.event_type==='PROPOSAL_WITHDRAWN'?'OBSERVED':'COMPLIANT';
        if(!serviceAvailable){findings.push('OVERSIGHT_SERVICE_UNAVAILABLE');result='REVIEW_REQUIRED';advance=false;strategy='UNVERIFIED';risk='UNVERIFIED';}
      }
    }
    const assessment={assessment_id:'',proposal_id:p?.proposal_id??null,event_id:p?.event_id??null,
      contract_version:VERSION,evaluated_at:evaluationTime,result,correlation_id:p?.correlation_id??null,
      input_hash:inputHash,technical_validity:errors.length?'INVALID':'VALID',
      strategy_compliance:strategy,risk_compliance:risk,compliance_domain:'SYNTHETIC_FIXTURE_ONLY',
      supporting_evidence_refs:p?[...new Set([...p.strategy.evidence_refs,...p.risk.evidence_refs])].filter(ref=>p.evidence.some(e=>e.sha256===ref&&digest(e.body)===ref)):[],
      governance_checks:{synthetic_only:true,imaf_entry_lock:'UNCHANGED_UNRESOLVED',operational_authorization:'DENIED',service_available:serviceAvailable},
      validation_errors:errors,findings,authority:authority(),sequence:records.length+1,previous_hash:records.at(-1)?.record_hash??'0'.repeat(64)};
    assessment.assessment_id='assessment:'+digest(assessment);
    const record={...assessment,record_hash:digest(assessment)};
    records.push(copy(record));
    if(p&&!errors.length){events.set(p.event_id,{input_hash:inputHash,assessment:copy(record)});if(advance)proposals.set(p.proposal_id,{account_id:p.account_id,correlation_id:p.correlation_id,revision:p.revision,state:p.event_type==='PROPOSAL_WITHDRAWN'?'WITHDRAWN':'PROPOSED',occurred_at:p.occurred_at});}
    return {duplicate:false,assessment:copy(record)};
  }
  return Object.freeze({assess,journal:()=>copy(records)});
}
export function verifyJournal(records) {
  try {
    let previous='0'.repeat(64);const ids=new Set();
    return Array.isArray(records)&&records.every((r,i)=>{
      const {record_hash,...body}=r;const {assessment_id,...withoutId}=body;
      const ok=r.sequence===i+1&&r.previous_hash===previous&&record_hash===digest(body)&&assessment_id==='assessment:'+digest({...withoutId,assessment_id:''})&&!ids.has(assessment_id)&&OUTCOMES.includes(r.result)&&r.authority.advisory_only===true&&r.authority.execution_authorized===false&&r.authority.live_authorized===false;
      ids.add(assessment_id);previous=record_hash;return ok;
    });
  }catch{return false;}
}
export function syntheticProposal() {
  const bodies=[{kind:'STRATEGY',policy_id:'synthetic-ict',assertion:'SYNTHETIC_FIXTURE'},{kind:'RISK',policy_id:'synthetic-risk-v1',assertion:'SYNTHETIC_FIXTURE'}];
  const evidence=bodies.map(body=>({sha256:digest(body),body}));
  return {contract_version:VERSION,environment:'SYNTHETIC',event_id:'synthetic-event-1',proposal_id:'synthetic-proposal-1',correlation_id:'synthetic-correlation-1',account_id:'synthetic-account',event_type:'PROPOSAL_SUBMITTED',revision:1,occurred_at:'2026-11-15T12:00:00.000Z',market_data_as_of:'2026-11-15T11:59:59.000Z',instrument:{symbol:'MNQ',contract_month:'2026-12'},direction:'long',entry_ticks:100,stop_ticks:90,target_ticks:130,quantity:1,risk:{policy_id:'synthetic-risk-v1',max_loss_cents:5000,expected_costs_cents:0,evidence_refs:[evidence[1].sha256]},strategy:{strategy_id:'synthetic-ict',version:'1',evidence_refs:[evidence[0].sha256]},evidence,authority:authority()};
}
