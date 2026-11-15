import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import net from 'node:net';
import {canonical,digest,syntheticProposal,createHarness} from './protocol.mjs';
test('Canonical runtime imports only crypto and the pinned schema',async()=>{
 const text=await readFile(new URL('./protocol.mjs',import.meta.url),'utf8');
 assert.deepEqual([...text.matchAll(/from\s+'([^']+)'/g)].map(m=>m[1]),['node:crypto','./proposal-v1.schema.json']);
 assert.equal(/\b(fetch|process|eval|Function)\s*[.(]/.test(text),false);
});
test('Security test runtime denies sockets and fetch',()=>{
 assert.throws(()=>net.connect(443,'example.com'),/NETWORK_DISABLED_FOR_SYNTHETIC_TEST/);
 assert.throws(()=>fetch('https://example.com'),/NETWORK_DISABLED_FOR_SYNTHETIC_TEST/);
});
test('Unknown credential fields and order-control payloads cannot enter protocol',()=>{
 for(const field of ['api_key','password','order','allowed','authorizationId']){
  const p=syntheticProposal();p[field]='synthetic-invalid-field';
  assert.equal(createHarness({evaluationTime:'2026-11-15T12:00:00.000Z'}).assess(canonical(p)).assessment.result,'INVALID');
 }
});
test('Oversight hash agrees with fixed JS canonical golden vector',()=>{
 assert.equal(digest({b:2,a:1}),'43258cff783fe7036d8a43033f830adfc60ec037382473548ac742b888292777');
});
