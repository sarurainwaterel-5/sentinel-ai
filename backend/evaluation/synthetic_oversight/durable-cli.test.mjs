import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,writeFileSync,rmSync,symlinkSync} from 'node:fs';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {runCLI} from './durable-cli.mjs';
import {canonical,syntheticProposal} from './protocol.mjs';
test('Offline CLI explicitly initializes, stores, duplicates, replays and reads immutable history',t=>{
 const dir=mkdtempSync(join(tmpdir(),'durable-cli-'));t.after(()=>rmSync(dir,{recursive:true,force:true}));const db=join(dir,'history.sqlite'),input=join(dir,'proposal.json');writeFileSync(input,canonical(syntheticProposal()),{mode:0o600});
 assert.equal(runCLI(['--command','init','--db',db]).exitCode,0);
 const args=['--command','submit','--db',db,'--input',input,'--at','2026-11-15T12:00:00.000Z'];
 const stored=runCLI(args);assert.equal(stored.result.status,'STORED');assert.equal(runCLI(args).result.status,'DUPLICATE');
 const replay=runCLI(['--command','replay','--db',db,'--id',stored.result.assessment.assessment_id,'--at','2026-11-15T13:00:00.000Z']);assert.equal(replay.result.status,'REPLAY_MATCH');
 assert.equal(runCLI(['--command','history','--db',db]).result.records.length,2);
});
test('CLI rejects missing options, unknown commands and unavailable storage without authority',()=>{
 for(const args of [[],['--command','broker'],['--command','submit','--db','/nonexistent/db'],['--unknown','anything'],['--command','history','--db','/nonexistent/db']]){const r=runCLI(args);assert.equal(r.exitCode,2);assert.equal(r.result.authority.execution_authorized,false);assert.equal(r.result.assessment,null);}
});
test('CLI cannot read symlink input or invent a decision on failed local input',t=>{
 const dir=mkdtempSync(join(tmpdir(),'durable-cli-link-'));t.after(()=>rmSync(dir,{recursive:true,force:true}));const db=join(dir,'db'),real=join(dir,'real'),link=join(dir,'link');writeFileSync(real,canonical(syntheticProposal()));symlinkSync(real,link);runCLI(['--command','init','--db',db]);
 assert.equal(runCLI(['--command','submit','--db',db,'--input',link,'--at','2026-11-15T12:00:00.000Z']).exitCode,2);
 assert.equal(runCLI(['--command','history','--db',db]).result.records.length,0);
});
