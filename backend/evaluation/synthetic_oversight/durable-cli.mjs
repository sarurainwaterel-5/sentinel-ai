/** Explicit local CLI. No default path, credential lookup or network. */
import {parseArgs} from 'node:util';
import {openSync,closeSync,fstatSync,readFileSync,constants} from 'node:fs';
import {pathToFileURL} from 'node:url';
import {initializeStore,openDurableStore,storageCanonical} from './durable.mjs';
function input(path,maxBytes=32768){const fd=openSync(path,constants.O_RDONLY|constants.O_NOFOLLOW|constants.O_NONBLOCK);try{const before=fstatSync(fd);if(!before.isFile()||before.size>maxBytes)throw Error('INVALID_INPUT');const raw=readFileSync(fd,'utf8'),after=fstatSync(fd);if(before.size!==after.size||before.mtimeMs!==after.mtimeMs||Buffer.byteLength(raw)>maxBytes)throw Error('INPUT_CHANGED');return raw;}finally{closeSync(fd);}}
export function runCLI(args){
 let store;
 try{
  const {values}=parseArgs({args,strict:true,options:{command:{type:'string'},db:{type:'string'},input:{type:'string'},'strategy-input':{type:'string'},at:{type:'string'},id:{type:'string'},supersedes:{type:'string'}}});
  const allowed={init:['command','db'],submit:['command','db','input','strategy-input','at','supersedes'],replay:['command','db','id','at'],history:['command','db']}[values.command];
  if(!allowed||!values.db||Object.keys(values).some(k=>!allowed.includes(k))||(values.command==='submit'&&(!values.input||!values.at))||(values.command==='replay'&&(!values.id||!values.at)))throw Error('INVALID_ARGUMENTS');
  let result;
  if(values.command==='init')result=initializeStore({path:values.db});
  else{
   const opened=openDurableStore({path:values.db});store=opened.store;
   if(!store)result=opened;
   else if(values.command==='submit'){let strategyReview=null;if(values['strategy-input']){const raw=input(values['strategy-input'],65536);strategyReview=JSON.parse(raw);if(storageCanonical(strategyReview)!==raw)throw Error('NON_CANONICAL_STRATEGY_INPUT');}result=store.submit(input(values.input),{evaluationTime:values.at,supersedes:values.supersedes??null,strategyReview});}
   else if(values.command==='replay')result=store.replay(values.id,{replayedAt:values.at});
   else result=store.history();
  }
  return {exitCode:['INITIALIZED','STORED','DUPLICATE','VERIFIED','REPLAY_MATCH'].includes(result.status)?0:2,result};
 }catch{return {exitCode:2,result:{status:'REQUEST_OR_STORAGE_FAILURE',assessment:null,authority:{advisory_only:true,execution_authorized:false,live_authorized:false}}};}
 finally{if(store)store.close();}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const out=runCLI(process.argv.slice(2));console.log(JSON.stringify(out.result));process.exitCode=out.exitCode;}
