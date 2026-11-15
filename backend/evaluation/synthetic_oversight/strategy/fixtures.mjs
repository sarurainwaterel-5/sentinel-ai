/** Synthetic test data only. Not a signal generator or historical market series. */
import {syntheticProposal} from '../protocol.mjs';
import {VERSION,SPEC_ID,newYork} from './evaluator.mjs';
export function fixture({direction='long',executionMs=60000,asOf='2026-11-16T14:33:00.000Z'}={}){
 const time=Date.parse(asOf),iso=x=>new Date(x).toISOString(),date=newYork(asOf).date;
 const base=[[109,112,108,110],[110,114,109,112],[110,113,107,109],[109,111,106,108],[108,110,105,107],[102,105,99,103],[103,119,102,118],[118,120,110,115],[112,114,105,110]];
 const candle=(values,t)=>{let [open,high,low,close]=values;if(direction==='short')[open,high,low,close]=[250-open,250-low,250-high,250-close];return {timestamp:iso(t),available_at:iso(t+executionMs),symbol:'MNQ',contract_month:'2026-12',open,high,low,close,volume:100};};
 const execStart=time-base.length*executionMs,execution={timeframe_ms:executionMs,opens_at:iso(execStart),closes_at:asOf,candles:base.map((v,i)=>candle(v,execStart+i*executionMs))};
 const analysisMs=Object.entries({'14400000':900000,'3600000':300000,'900000':60000,'300000':15000}).find(([k,v])=>v===executionMs)?.[0]??900000;
 const analysisEnd=Math.floor(execStart/Number(analysisMs))*Number(analysisMs),analysisStart=analysisEnd-3*Number(analysisMs);
 const analysis={timeframe_ms:Number(analysisMs),opens_at:iso(analysisStart),closes_at:iso(analysisEnd),candles:Array.from({length:3},(_,i)=>({...candle([120,180,80,130],analysisStart+i*Number(analysisMs)),available_at:iso(analysisStart+(i+1)*Number(analysisMs))}))};
 const poolEnd=execStart-executionMs,poolStart=poolEnd-3*executionMs;
 const liquidity_session={timeframe_ms:executionMs,opens_at:iso(poolStart),closes_at:iso(poolEnd),candles:Array.from({length:3},(_,i)=>candle([120,150,100,125],poolStart+i*executionMs))};
 const proposal=syntheticProposal();Object.assign(proposal,{direction,occurred_at:asOf,market_data_as_of:asOf,entry_ticks:direction==='long'?106:144,stop_ticks:direction==='long'?98:152,target_ticks:direction==='long'?150:100});
 // Explicit synthetic schedules, including the 23/25-hour DST transition dates.
 const schedules={'2026-11-16':['05:00','21:00','14:30','16:00'],'2026-07-06':['04:00','20:00','13:30','15:00'],'2026-03-08':['05:00','20:00','13:30','15:00'],'2026-11-01':['04:00','21:00','14:30','16:00']};
 const times=schedules[date];if(!times)throw Error('EXPLICIT_TEST_SCHEDULE_REQUIRED');
 const [opens,closes,opportunityStart,opportunityEnd]=times.map(t=>`${date}T${t}:00.000Z`);
 const schedule={timezone:'America/New_York',session_date:date,session_opens_at:opens,session_closes_at:closes,opportunity:{opens_at:opportunityStart,closes_at:opportunityEnd,available_at:opens,reference:'synthetic-explicit-opportunity'}};
 return {version:VERSION,spec_version:SPEC_ID,strategy_version:'ict-paper-validation-v1',as_of:asOf,proposal,execution,analysis,liquidity_session,anchors:{sweep_index:5,mss_index:6,fvg_end_index:7,entry_index:8},schedule,risk_state:{source:'SYNTHETIC_FIXTURE',session_date:date,as_of:asOf,available_at:asOf,valid_until:iso(time+3600000),entries_today:0,realized_pnl_cents:0,open_positions:0,pending_orders:0,last_execution_error_at:null,error_history_complete:true,out_of_balance:false},claims:{sweep:true,mss:true,displacement:true,fvg:true,entry_zone:true,target:true,htf_location:true}};
}
