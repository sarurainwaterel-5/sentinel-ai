import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import net from 'node:net';
import {initializeStore,openDurableStore} from './durable.mjs';
import {canonical,syntheticProposal} from './protocol.mjs';
test('Durable runtime import graph excludes network, broker, execution and credential clients',()=>{
 const source=readFileSync(new URL('./durable.mjs',import.meta.url),'utf8');
 assert.deepEqual([...source.matchAll(/from\s+'([^']+)'/g)].map(x=>x[1]),['node:sqlite','node:fs','node:path','node:crypto','./protocol.mjs','./strategy/evaluator.mjs']);
 assert.equal(/process\.env|fetch\s*\(|\bspawn\s*\(|\bexecFile\s*\(/.test(source),false);
});
test('Durable security tests run with active socket and fetch denial',()=>{
 assert.throws(()=>net.connect(443,'example.com'),/NETWORK_DISABLED_FOR_SYNTHETIC_TEST/);
 assert.throws(()=>fetch('https://example.com'),/NETWORK_DISABLED_FOR_SYNTHETIC_TEST/);
});
test('Stored, duplicate, conflict and replay paths all retain denied authority',t=>{
 const dir=mkdtempSync(join(tmpdir(),'durable-security-')),path=join(dir,'history.sqlite');t.after(()=>rmSync(dir,{recursive:true,force:true}));
 initializeStore({path});const s=openDurableStore({path}).store;t.after(()=>s.close());
 const p=syntheticProposal(),first=s.submit(canonical(p),{evaluationTime:'2026-11-15T12:00:00.000Z'});
 const duplicate=s.submit(canonical(p),{evaluationTime:'2026-11-15T12:00:00.000Z'});
 p.quantity=2;const conflict=s.submit(canonical(p),{evaluationTime:'2026-11-15T12:00:00.000Z'});
 const replay=s.replay(first.assessment.assessment_id,{replayedAt:'2026-11-15T13:00:00.000Z'});
 for(const r of [first,duplicate,conflict,replay]){assert.equal(r.authority.execution_authorized,false);assert.equal(r.authority.live_authorized,false);if(r.assessment)assert.equal(r.assessment.governance_checks.operational_authorization,'DENIED');}
 for(const r of s.history().records)assert.equal(r.payload.authority.execution_authorized,false);
});
