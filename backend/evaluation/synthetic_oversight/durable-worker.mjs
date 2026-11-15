// Test driver for actual independent processes/crash boundaries; never imported by runtime.
import {DatabaseSync} from 'node:sqlite';
import {initializeStore,openDurableStore} from './durable.mjs';
import {writeFileSync} from 'node:fs';
const [action,path,encoded,reply]=process.argv.slice(2);
const respond=value=>writeFileSync(reply,JSON.stringify(value),{mode:0o600,flag:'wx'});
const wire=encoded?Buffer.from(encoded,'base64').toString('utf8'):'';
if(action==='hold-lock'){
 const db=new DatabaseSync(path);db.exec('BEGIN EXCLUSIVE');respond({status:'LOCKED'});setInterval(()=>{},1000);
}else{
 if(action==='rollback-once'){
  const prepare=DatabaseSync.prototype.prepare;let failed=false;
  DatabaseSync.prototype.prepare=function(sql){if(!failed&&sql.startsWith('INSERT INTO proposal_claims')){failed=true;throw Error('INJECTED_TRANSACTION_FAILURE');}return prepare.call(this,sql);};
 }
 if(action==='crash-before-commit'||action==='crash-after-commit'){
  const exec=DatabaseSync.prototype.exec;
  DatabaseSync.prototype.exec=function(sql){if(sql==='COMMIT'){if(action==='crash-before-commit')process.kill(process.pid,'SIGKILL');const result=exec.call(this,sql);process.kill(process.pid,'SIGKILL');return result;}return exec.call(this,sql);};
 }
 const opened=openDurableStore({path});
 if(!opened.store){respond(opened);process.exitCode=2;}
 else{
  const first=opened.store.submit(wire,{evaluationTime:'2026-11-15T12:00:00.000Z'});
  const result=action==='rollback-once'?{first,afterRollback:opened.store.history(),second:opened.store.submit(wire,{evaluationTime:'2026-11-15T12:00:00.000Z'})}:first;
  opened.store.close();respond(result);
 }
}
