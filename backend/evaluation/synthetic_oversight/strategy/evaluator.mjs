/** Independent verification of supplied synthetic proposals. No signal search or orders. */
import importedSpec from './specification-v1.json' with {type:'json'};
import {canonical,digest,validateWire,OUTCOMES} from '../protocol.mjs';
const freeze=value=>{if(value&&typeof value==='object'){Object.values(value).forEach(freeze);Object.freeze(value);}return value;};
const spec=freeze(structuredClone(importedSpec));
export const SPEC_ID=spec.id,VERSION='sentinel.imaf.synthetic.review.v1';
const r=spec.rules,authority=()=>({advisory_only:true,execution_authorized:false,live_authorized:false});
const utc=s=>typeof s==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$/.test(s)&&Number.isFinite(Date.parse(s))&&new Date(s).toISOString()===s;
const at=t=>new Date(t).toISOString(),ms=s=>Date.parse(s),integer=x=>Number.isSafeInteger(x),positive=x=>integer(x)&&x>0&&x<=1000000000;
const closed=(x,keys)=>x&&typeof x==='object'&&!Array.isArray(x)&&Object.keys(x).length===keys.length&&keys.every(k=>Object.hasOwn(x,k));
const id=x=>typeof x==='string'&&/^[A-Za-z0-9_.:-]{1,128}$/.test(x);
export function verifyStrategyAssessment(value){try{const {assessment_id,...body}=value;return assessment_id==='strategy:'+digest(body)&&OUTCOMES.includes(value.result)&&value.authority?.advisory_only===true&&value.authority?.execution_authorized===false&&value.authority?.live_authorized===false&&value.governance_checks?.operational_authorization==='DENIED'&&value.observations.every(({evidence_ref,...observation})=>digest(observation)===evidence_ref);}catch{return false;}}
const localFormatter=new Intl.DateTimeFormat('en-CA',{timeZone:'America/New_York',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'});
export function newYork(t){const p=Object.fromEntries(localFormatter.formatToParts(new Date(t)).map(p=>[p.type,p.value]));return {date:`${p.year}-${p.month}-${p.day}`,clock:`${p.hour}:${p.minute}:${p.second}`};}
function validate(input,evaluatedAt){
 const errors=[];
 try{if(Buffer.byteLength(canonical(input))>65536)throw Error();}catch{return ['BOUNDED_JSON_REQUIRED'];}
 if(!closed(input,['version','spec_version','strategy_version','as_of','proposal','execution','analysis','liquidity_session','anchors','schedule','risk_state','claims'])||input.version!==VERSION||input.spec_version!==SPEC_ID)return ['REVIEW_CONTRACT_OR_SPEC_INVALID'];
 if(!utc(evaluatedAt)||!utc(input.as_of)||input.as_of>evaluatedAt)return ['INVALID_CUTOFF'];
 if(!id(input.strategy_version))errors.push('STRATEGY_METADATA_TYPE_INVALID');
 const proposal=validateWire(canonical(input.proposal));if(proposal.errors.length)errors.push('PROPOSAL_CONTRACT_INVALID');
 if(proposal.value&&(input.proposal.occurred_at!==input.as_of||input.proposal.market_data_as_of>input.as_of))errors.push('PROPOSAL_CLOCK_MISMATCH');
 if(proposal.value){
  const p=proposal.value,refs=new Map(p.evidence.map(e=>[e.sha256,e.body]));
  if(p.event_type!=='PROPOSAL_SUBMITTED'||p.revision!==1)errors.push('UNSUPPORTED_PROPOSAL_LIFECYCLE');
  if(refs.size!==p.evidence.length||p.evidence.some(e=>digest(e.body)!==e.sha256))errors.push('PROPOSAL_EVIDENCE_INTEGRITY');
  if(!p.strategy.evidence_refs.length||!p.risk.evidence_refs.length)errors.push('MISSING_PROPOSAL_EVIDENCE');
  if(p.strategy.evidence_refs.some(x=>refs.get(x)?.kind!=='STRATEGY'||refs.get(x)?.policy_id!==p.strategy.strategy_id)||p.risk.evidence_refs.some(x=>refs.get(x)?.kind!=='RISK'||refs.get(x)?.policy_id!==p.risk.policy_id))errors.push('PROPOSAL_EVIDENCE_REFERENCE_CONFLICT');
  if(p.risk.policy_id!=='synthetic-risk-v1')errors.push('UNSUPPORTED_RISK_POLICY');
 }
 const seriesKeys=['timeframe_ms','opens_at','closes_at','candles'];
 for(const [name,maxBars]of [['execution',128],['analysis',32],['liquidity_session',64]]){
  const s=input[name];if(!closed(s,seriesKeys)||!integer(s.timeframe_ms)||s.timeframe_ms<=0||!utc(s.opens_at)||!utc(s.closes_at)||!Array.isArray(s.candles)||s.candles.length>maxBars){errors.push('SERIES_CONTRACT_INVALID:'+name);continue;}
  if(!s.candles.length){errors.push('MISSING_CANDLES:'+name);continue;}
  for(let i=0;i<s.candles.length;i++){
   const c=s.candles[i];if(!closed(c,['timestamp','available_at','symbol','contract_month','open','high','low','close','volume'])||!utc(c.timestamp)||!utc(c.available_at)||![c.open,c.high,c.low,c.close].every(positive)||!integer(c.volume)||c.volume<0||c.high<Math.max(c.open,c.close)||c.low>Math.min(c.open,c.close)||c.symbol!=='MNQ'||c.contract_month!==input.proposal?.instrument?.contract_month){errors.push('CANDLE_INVALID:'+name);continue;}
   const start=ms(c.timestamp),end=start+s.timeframe_ms;
   if(start%s.timeframe_ms!==0||(i&&start!==ms(s.candles[i-1].timestamp)+s.timeframe_ms))errors.push('CANDLE_GRID_OR_GAP:'+name);
   if(ms(c.available_at)<end||c.available_at>input.as_of||end>ms(input.as_of))errors.push('FUTURE_OR_UNAVAILABLE_CANDLE:'+name);
  }
  if(s.opens_at!==s.candles[0]?.timestamp||ms(s.closes_at)!==ms(s.candles.at(-1)?.timestamp)+s.timeframe_ms)errors.push('SERIES_BOUNDARIES_INVALID:'+name);
 }
 if(spec.hierarchy[input.analysis?.timeframe_ms]!==input.execution?.timeframe_ms||input.liquidity_session?.timeframe_ms!==input.execution?.timeframe_ms)errors.push('UNSUPPORTED_TIMEFRAME_PAIR');
 if(!closed(input.anchors,['sweep_index','mss_index','fvg_end_index','entry_index'])||!Object.values(input.anchors).every(i=>integer(i)&&i>=0&&i<(input.execution?.candles?.length??0)))errors.push('ANCHORS_INVALID');
 else if(!(input.anchors.sweep_index<input.anchors.mss_index&&input.anchors.fvg_end_index===input.anchors.mss_index+1&&input.anchors.entry_index>input.anchors.fvg_end_index&&input.anchors.entry_index===input.execution.candles.length-1))errors.push('ANCHOR_CAUSALITY_INVALID');
 const s=input.schedule;
 if(!closed(s,['timezone','session_date','session_opens_at','session_closes_at','opportunity'])||s.timezone!=='America/New_York'||!utc(s.session_opens_at)||!utc(s.session_closes_at)||ms(s.session_closes_at)<=ms(s.session_opens_at)||newYork(input.as_of).date!==s.session_date||newYork(s.session_opens_at).date!==s.session_date||newYork(s.session_closes_at).date!==s.session_date)errors.push('EXPLICIT_SESSION_REQUIRED');
 if(s?.opportunity!==null){const w=s?.opportunity;if(!closed(w,['opens_at','closes_at','available_at','reference'])||![w.opens_at,w.closes_at,w.available_at].every(utc)||!id(w.reference)||!(w.opens_at<w.closes_at)||w.available_at>input.as_of||newYork(w.opens_at).date!==s.session_date||newYork(w.closes_at).date!==s.session_date||newYork(w.opens_at).clock<'09:30:00'||w.opens_at<s.session_opens_at||w.closes_at>s.session_closes_at)errors.push('OPPORTUNITY_INVALID');}
 const claimKeys=['sweep','mss','displacement','fvg','entry_zone','target','htf_location'];if(!closed(input.claims,claimKeys)||!Object.values(input.claims).every(v=>v===null||typeof v==='boolean'))errors.push('CLAIMS_INVALID');
 const risk=input.risk_state;
 if(risk!==null&&(!closed(risk,['source','session_date','as_of','available_at','valid_until','entries_today','realized_pnl_cents','open_positions','pending_orders','last_execution_error_at','error_history_complete','out_of_balance'])||risk.source!=='SYNTHETIC_FIXTURE'||typeof risk.session_date!=='string'||!utc(risk.session_date+'T00:00:00.000Z')||![risk.as_of,risk.available_at,risk.valid_until].every(utc)||!['entries_today','open_positions','pending_orders'].every(k=>integer(risk[k])&&risk[k]>=0)||!integer(risk.realized_pnl_cents)||typeof risk.error_history_complete!=='boolean'||![true,false,null].includes(risk.out_of_balance)||(risk.last_execution_error_at!==null&&!utc(risk.last_execution_error_at))))errors.push('RISK_STATE_INVALID');
 return [...new Set(errors)];
}
function reference(series,candle,index){return {series,index,timestamp:candle.timestamp,available_at:candle.available_at,open:candle.open,high:candle.high,low:candle.low,close:candle.close,volume:candle.volume,sha256:digest({series,index,candle})};}
export function evaluateStrategyReview(input,{evaluatedAt}={}){
 let errors;try{errors=validate(input,evaluatedAt);}catch{errors=['REVIEW_INPUT_INVALID'];}
 const observations=[],disagreements=[];
 const emit=(rule,passed,refs=[],levels={},reason=null)=>{const value={rule,status:passed===null?'UNRESOLVED':passed?'PASS':'FAIL',candles:refs,levels,reason};observations.push({...value,evidence_ref:digest(value)});return passed;};
 let subset='UNVERIFIED',riskCompliance='UNVERIFIED',session='UNVERIFIED';
 if(!errors.length){
  const p=input.proposal,cs=input.execution.candles,a=input.anchors,tf=input.execution.timeframe_ms,long=p.direction==='long';
  const ref=(i)=>reference('execution',cs[i],i);
  const s=cs[a.sweep_index],m=cs[a.mss_index],g=cs[a.fvg_end_index],e=cs[a.entry_index];
  const poolCandles=input.liquidity_session.candles,analysis=input.analysis.candles;
  if(input.liquidity_session.closes_at>s.timestamp||poolCandles.some(c=>c.available_at>s.timestamp)||input.analysis.closes_at>cs[0].timestamp||analysis.some(c=>c.available_at>cs[0].timestamp))errors.push('CONTEXT_NOT_AVAILABLE_BEFORE_DISCOVERY');
  if(ms(input.as_of)-ms(cs.at(-1).timestamp)-tf>tf)errors.push('STALE_MARKET_SNAPSHOT');
  if(p.market_data_as_of!==cs.at(-1).available_at)errors.push('MARKET_SNAPSHOT_CLOCK_MISMATCH');
  if(p.instrument.symbol!=='MNQ')errors.push('UNSUPPORTED_INSTRUMENT');
  if(!errors.length){
   const poolLow=Math.min(...poolCandles.map(c=>c.low)),poolHigh=Math.max(...poolCandles.map(c=>c.high)),pool=long?poolLow:poolHigh;
   const poolRefs=poolCandles.map((c,i)=>reference('liquidity_session',c,i));
   emit('SESSION_LIQUIDITY_DERIVED',true,poolRefs,{low:poolLow,high:poolHigh});
   const sweep=emit('STRICT_SWEEP',long?s.low<pool&&s.close>pool:s.high>pool&&s.close<pool,[ref(a.sweep_index)],{pool});
   const swings=[];
   for(let i=r.swing_left;i+r.swing_right<cs.length;i++){
    const peer=cs.slice(i-r.swing_left,i+r.swing_right+1).filter((_,j)=>j!==r.swing_left);
    for(const kind of ['high','low'])if(peer.every(c=>kind==='high'?cs[i].high>c.high:cs[i].low<c.low)){
     const confirmed=i+r.swing_right;swings.push({kind,index:i,confirmed,price:cs[i][kind],available_at:at(Math.max(ms(cs[confirmed].available_at),...cs.slice(i-r.swing_left,confirmed+1).map(c=>ms(c.available_at))))});
    }
   }
   const pivot=swings.filter(x=>x.kind===(long?'high':'low')&&x.confirmed<a.sweep_index&&x.available_at<=s.timestamp).at(-1);
   emit('STRICT_CONFIRMED_SWING',pivot?true:null,pivot?cs.slice(pivot.index-r.swing_left,pivot.confirmed+1).map((c,j)=>ref(pivot.index-r.swing_left+j)):[],pivot?{price:pivot.price,known_at:pivot.available_at}:{},pivot?null:'NO_PRE_SWEEP_CONFIRMED_PIVOT');
   const breakPass=pivot?(long?m.close>pivot.price:m.close<pivot.price):null;
   emit('STRUCTURAL_CLOSE_BREAK',breakPass,[ref(a.mss_index)],pivot?{swing:pivot.price,close:m.close}:{});
   const mss=emit('RESEARCH_MSS_AFTER_SWEEP',pivot?sweep&&breakPass:null,[ref(a.sweep_index),ref(a.mss_index)],pivot?{swing:pivot.price}:{});
   const prior=cs.slice(a.mss_index-r.baseline_bars,a.mss_index),range=m.high-m.low,body=Math.abs(m.close-m.open),sumRange=prior.reduce((v,c)=>v+c.high-c.low,0);
   const displacement=emit('RESEARCH_DISPLACEMENT',prior.length===r.baseline_bars?range>0&&(long?m.close>m.open:m.close<m.open)&&body>=r.min_body_ticks&&body*r.body_ratio_den>=range*r.body_ratio_num&&range*r.range_multiple_den*r.baseline_bars>=sumRange*r.range_multiple_num:null,cs.slice(Math.max(0,a.mss_index-r.baseline_bars),a.mss_index+1).map((c,j)=>ref(Math.max(0,a.mss_index-r.baseline_bars)+j)),{body_ticks:body,range_ticks:range,prior_sum_range_ticks:sumRange},prior.length===r.baseline_bars?null:'INSUFFICIENT_BASELINE');
   const first=cs[a.fvg_end_index-2],gapLow=long?first.high:g.high,gapHigh=long?g.low:first.low;
   const fvg=emit('THREE_CLOSED_BAR_FVG',gapHigh-gapLow>=r.min_gap_ticks,[ref(a.fvg_end_index-2),ref(a.mss_index),ref(a.fvg_end_index)],{low:gapLow,high:gapHigh});
   const leg=cs.slice(a.sweep_index,a.fvg_end_index+1),low=Math.min(...leg.map(c=>c.low)),high=Math.max(...leg.map(c=>c.high)),span=high-low,depth=long?high-p.entry_ticks:p.entry_ticks-low;
   const ote=span>0&&depth*r.ote_den>=span*r.ote_min_num&&depth*r.ote_den<=span*r.ote_max_num;
   const oteLowN=long?high*r.ote_den-span*r.ote_max_num:low*r.ote_den+span*r.ote_min_num;
   const oteHighN=long?high*r.ote_den-span*r.ote_min_num:low*r.ote_den+span*r.ote_max_num;
   const zoneLowN=Math.max(gapLow*r.ote_den,oteLowN),zoneHighN=Math.min(gapHigh*r.ote_den,oteHighN);
   const expectedEntry=Math.floor((zoneLowN+zoneHighN+r.ote_den)/(2*r.ote_den));
   const earlierTouch=cs.slice(a.fvg_end_index+1,a.entry_index).some(c=>c.high*r.ote_den>=zoneLowN&&c.low*r.ote_den<=zoneHighN);
   const stopped=cs.slice(a.fvg_end_index+1).some(c=>long?c.low<=p.stop_ticks:c.high>=p.stop_ticks);
   const expectedStop=long?low-r.stop_buffer_ticks:high+r.stop_buffer_ticks;
   const entry=emit('LATER_FVG_OTE_ENTRY',fvg&&ote&&zoneLowN<=zoneHighN&&p.entry_ticks===expectedEntry&&p.entry_ticks>=gapLow&&p.entry_ticks<=gapHigh&&e.low<=p.entry_ticks&&e.high>=p.entry_ticks&&p.stop_ticks===expectedStop&&!stopped&&!earlierTouch,[ref(a.sweep_index),ref(a.fvg_end_index),ref(a.entry_index)],{impulse_low:low,impulse_high:high,entry:p.entry_ticks,expected_entry:expectedEntry,expected_stop:expectedStop,gap_low:gapLow,gap_high:gapHigh,zone_low_numerator:zoneLowN,zone_high_numerator:zoneHighN,denominator:r.ote_den});
   const target=emit('KNOWN_OPPOSING_SESSION_TARGET',p.target_ticks===(long?poolHigh:poolLow)&& (long?p.target_ticks>p.entry_ticks:p.target_ticks<p.entry_ticks),poolRefs,{target:long?poolHigh:poolLow});
   const rangeLow=Math.min(...analysis.map(c=>c.low)),rangeHigh=Math.max(...analysis.map(c=>c.high));
   const htf=emit('EXPLICIT_RANGE_DISCOUNT_PREMIUM',long?2*p.entry_ticks<rangeHigh+rangeLow&&2*pool<=rangeHigh+rangeLow:2*p.entry_ticks>rangeHigh+rangeLow&&2*pool>=rangeHigh+rangeLow,analysis.map((c,i)=>reference('analysis',c,i)),{low:rangeLow,high:rangeHigh,entry:p.entry_ticks,pool});
   const computed={sweep,mss,displacement,fvg,entry_zone:entry,target,htf_location:htf};
   for(const [name,value]of Object.entries(computed))if(input.claims[name]!==null&&input.claims[name]!==value)disagreements.push({claim:name,declared:input.claims[name],independent:value,supporting_evidence_refs:observations.filter(o=>({sweep:'STRICT_SWEEP',mss:'RESEARCH_MSS_AFTER_SWEEP',displacement:'RESEARCH_DISPLACEMENT',fvg:'THREE_CLOSED_BAR_FVG',entry_zone:'LATER_FVG_OTE_ENTRY',target:'KNOWN_OPPOSING_SESSION_TARGET',htf_location:'EXPLICIT_RANGE_DISCOUNT_PREMIUM'})[name]===o.rule).map(o=>o.evidence_ref)});
   subset=Object.values(computed).some(x=>x===false)?'FAIL':Object.values(computed).some(x=>x===null)?'INSUFFICIENT_EVIDENCE':'RESEARCH_SUBSET_PASS';
   if(input.strategy_version!==spec.research_strategy||p.strategy.strategy_id!=='synthetic-ict'||p.strategy.version!=='1'){emit('STRATEGY_METADATA_CONSISTENCY',false,[],{},'CONFLICTING_STRATEGY_METADATA');subset='FAIL';}
   const ny=newYork(input.as_of),schedule=input.schedule,early=spec.mission_policy.early_windows.some(([start,end])=>ny.clock>=start&&ny.clock<end),w=schedule.opportunity;
   const inSession=input.as_of>=schedule.session_opens_at&&input.as_of<schedule.session_closes_at;
   const permitted=early||(ny.clock>='09:30:00'&&w&&input.as_of>=w.opens_at&&input.as_of<w.closes_at);
   session=!inSession?'FAIL':permitted?'PASS':ny.clock>='09:30:00'&&!w?'INSUFFICIENT_EVIDENCE':'FAIL';
   emit('EXPLICIT_NY_TRADING_WINDOW',session==='INSUFFICIENT_EVIDENCE'?null:session==='PASS',[],{decision:input.as_of,local_date:ny.date,local_clock:ny.clock},session==='INSUFFICIENT_EVIDENCE'?'POST_0930_OPPORTUNITY_NOT_SUPPLIED':null);
   const state=input.risk_state;
   if(state===null||!state.error_history_complete||state.out_of_balance===null||state.session_date!==ny.date||newYork(state.as_of).date!==ny.date||state.as_of>input.as_of||state.available_at<state.as_of||state.available_at>input.as_of||state.valid_until<=input.as_of){riskCompliance='INSUFFICIENT_EVIDENCE';emit('SYNTHETIC_ACCOUNT_HISTORY',null,[],{},'CURRENT_COMPLETE_ACCOUNT_STATE_UNAVAILABLE');}
   else{
    const loss=Math.abs(p.entry_ticks-p.stop_ticks)*r.tick_value_cents*p.quantity+p.risk.expected_costs_cents,gain=Math.abs(p.target_ticks-p.entry_ticks)*r.tick_value_cents*p.quantity-p.risk.expected_costs_cents;
    const pauseUntil=state.last_execution_error_at?at(ms(state.last_execution_error_at)+spec.mission_policy.execution_error_pause_hours*3600000):null;
    const checks={ONE_TRADE_PER_NY_DAY:state.entries_today<1,NO_OPEN_OR_PENDING_EXPOSURE:state.open_positions===0&&state.pending_orders===0,STAND_ASIDE_OUT_OF_BALANCE:state.out_of_balance===false,EXECUTION_ERROR_48H_PAUSE:!pauseUntil||state.last_execution_error_at<=input.as_of&&ms(input.as_of)>=ms(state.last_execution_error_at)+spec.mission_policy.execution_error_pause_hours*3600000,HARD_RISK_ARITHMETIC:p.quantity===1&&loss<=r.planned_risk_cents&&p.risk.max_loss_cents<=r.planned_risk_cents&&loss<=p.risk.max_loss_cents&&gain>=r.net_reward_risk*loss,DAILY_LOSS_LOCKOUT:state.realized_pnl_cents>-r.daily_loss_cents};
    for(const [rule,pass]of Object.entries(checks))emit(rule,pass,[],{state_as_of:state.as_of,entries_today:state.entries_today,loss_cents:loss,gain_cents:gain,pause_until:pauseUntil});
    riskCompliance=Object.values(checks).every(Boolean)?'SYNTHETIC_STATE_CHECK_PASS':'FAIL';
   }
  }
 }
 const unresolved=[...spec.unresolved.map(x=>x.id),...spec.additional_unresolved];
 for(const name of unresolved)emit(name,null,[],{},'NO_APPROVED_OPERATIONAL_DEFINITION');
 const insufficient=errors.some(x=>x.startsWith('MISSING_')||x==='STALE_MARKET_SNAPSHOT');
 const result=errors.length?insufficient?'INSUFFICIENT_EVIDENCE':'INVALID':subset==='FAIL'||riskCompliance==='FAIL'||session==='FAIL'||disagreements.some(x=>x.independent!==null)?'NON_COMPLIANT':subset==='INSUFFICIENT_EVIDENCE'||riskCompliance==='INSUFFICIENT_EVIDENCE'||session==='INSUFFICIENT_EVIDENCE'?'INSUFFICIENT_EVIDENCE':'REVIEW_REQUIRED';
 const base={version:VERSION,spec_version:SPEC_ID,spec_sha256:digest(spec),evaluated_at:utc(evaluatedAt)?evaluatedAt:null,as_of:utc(input?.as_of)?input.as_of:null,proposal_id:id(input?.proposal?.proposal_id)?input.proposal.proposal_id:null,correlation_id:id(input?.proposal?.correlation_id)?input.proposal.correlation_id:null,result,contract_validity:errors.length?'INVALID':'VALID',strategy_compliance:subset,evidence_sufficiency:errors.length||subset==='INSUFFICIENT_EVIDENCE'?'INSUFFICIENT':'RESEARCH_SUBSET_ONLY',risk_compliance:riskCompliance,session_compliance:session,unresolved,validation_errors:errors,observations,disagreements,governance_checks:{imaf_entry_lock:'UNCHANGED_UNRESOLVED',operational_authorization:'DENIED',source:'SYNTHETIC_ONLY_UNAUTHENTICATED',full_imaf_compliance:'INCOMPLETE'},authority:authority()};
 base.observation_ladder={Observe:observations.filter(o=>o.status!=='UNRESOLVED').map(o=>o.evidence_ref),Describe:'CANDLE_LEVELS_AND_AVAILABILITY_RETAINED',Differentiate:{independent_observations:observations.length,platform_disagreements:disagreements.length,unresolved},Interpret:'NO_PARTICIPANT_IDENTITY_OR_INTENT_INFERRED',Hypothesize:'SUPPLIED_PROPOSAL_ONLY_NOT_A_NEW_SIGNAL',Verify:'ONLY_PRE_CUTOFF_EVIDENCE_POST_TRADE_REVIEW_PENDING',Decide:result};
 try{return {...base,assessment_id:'strategy:'+digest(base)};}catch{return {version:VERSION,result:'INVALID',contract_validity:'INVALID',validation_errors:['BOUNDED_REVIEW_OUTPUT'],authority:authority()};}
}
