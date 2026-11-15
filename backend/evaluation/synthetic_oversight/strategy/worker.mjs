// Test-only independent process driver. Private file IPC, never imported by runtime.
import {readFileSync,writeFileSync} from 'node:fs';
import {openDurableStore} from '../durable.mjs';
import {canonical} from '../protocol.mjs';
const [action,path,inputPath,reply]=process.argv.slice(2),snapshot=JSON.parse(readFileSync(inputPath,'utf8'));
const opened=openDurableStore({path});let result=opened;
if(opened.store){try{if(action==='submit')result=opened.store.submit(canonical(snapshot.proposal),{evaluationTime:snapshot.as_of,strategyReview:snapshot});else{const original=opened.store.history().records.find(r=>r.kind==='DECISION');result=opened.store.replay(original.payload.assessment.assessment_id,{replayedAt:new Date(Date.parse(snapshot.as_of)+3600000).toISOString()});}}finally{opened.store.close();}}
writeFileSync(reply,JSON.stringify(result),{mode:0o600,flag:'wx'});
