import test from 'node:test';
import assert from 'node:assert/strict';
export function registerContractTests(api,label='canonical') {
 const {canonical,digest,createHarness,syntheticProposal,verifyJournal,validateWire}=api;
 const time='2026-11-15T12:00:00.000Z';
 const fresh=options=>createHarness({evaluationTime:time,...options});
 const evaluate=(mutate=()=>{},options)=>{const p=syntheticProposal();mutate(p);return fresh(options).assess(canonical(p)).assessment;};
 const check=r=>{assert.equal(r.authority.execution_authorized,false);assert.equal(r.authority.live_authorized,false);assert.equal(r.governance_checks.operational_authorization,'DENIED');assert.equal(r.compliance_domain,'SYNTHETIC_FIXTURE_ONLY');};
 test(`${label}: valid synthetic proposal produces informational compliance`,()=>{const r=evaluate();assert.equal(r.result,'COMPLIANT');assert.equal(r.technical_validity,'VALID');check(r);});
 const cases=[
 ['missing required field',p=>delete p.risk,'INVALID'],
 ['invalid data type',p=>p.quantity='1','INVALID'],
 ['numeric authority bypass',p=>p.authority.execution_authorized=0,'INVALID'],
 ['live authority bypass',p=>p.authority.live_authorized=true,'INVALID'],
 ['unknown fields',p=>p.order_endpoint='forbidden','INVALID'],
 ['unsupported version',p=>p.contract_version='sentinel.synthetic.proposal.v2','INVALID'],
 ['unsupported instrument',p=>p.instrument.symbol='NQ','INVALID'],
 ['invalid calendar timestamp',p=>p.occurred_at='2026-02-30T12:00:00.000Z','INVALID'],
 ['timezone offset forbidden',p=>p.occurred_at='2026-11-15T06:00:00.000-06:00','INVALID'],
 ['future data',p=>p.market_data_as_of='2026-11-15T12:00:01.000Z','INVALID'],
 ['stale data',p=>p.market_data_as_of='2026-11-15T11:59:57.999Z','INSUFFICIENT_EVIDENCE'],
 ['missing strategy evidence',p=>p.strategy.evidence_refs=[],'INSUFFICIENT_EVIDENCE'],
 ['missing risk evidence',p=>p.risk.evidence_refs=[],'INSUFFICIENT_EVIDENCE'],
 ['broken evidence reference',p=>p.strategy.evidence_refs=['0'.repeat(64)],'INVALID'],
 ['tampered evidence body',p=>p.evidence[0].body.policy_id='other','INVALID'],
 ['duplicate evidence',p=>p.evidence.push(p.evidence[0]),'INVALID'],
 ['conflicting strategy metadata',p=>p.strategy.strategy_id='other','NON_COMPLIANT'],
 ['conflicting risk metadata',p=>p.risk.policy_id='other','NON_COMPLIANT'],
 ['unknown strategy version',p=>p.strategy.version='2','REVIEW_REQUIRED'],
 ['negative risk data',p=>p.risk.max_loss_cents=-1,'INVALID'],
 ['malformed risk data',p=>p.risk.expected_costs_cents=null,'INVALID'],
 ['excessive synthetic risk',p=>p.risk.max_loss_cents=5001,'NON_COMPLIANT'],
 ['invalid stop geometry',p=>p.stop_ticks=101,'NON_COMPLIANT'],
 ['insufficient net reward',p=>p.target_ticks=105,'NON_COMPLIANT'],
 ['invalid initial transition',p=>p.event_type='PROPOSAL_REVISED','INVALID'],
 ['non synthetic environment',p=>p.environment='PAPER','INVALID']
 ];
 for(const [name,mutate,status]of cases)test(`${label}: ${name}`,()=>{const r=evaluate(mutate);assert.equal(r.result,status);check(r);});
 for(const [name,raw]of [['malformed JSON','{'],['duplicate JSON keys','{"a":1,"a":2}'],['oversize','x'.repeat(32769)],['not a string',null],['excess depth','['.repeat(30)+'0'+']'.repeat(30)]])test(`${label}: ${name} fails safely`,()=>{const r=fresh().assess(raw).assessment;assert.equal(r.result,'INVALID');assert.ok(r.validation_errors.length);check(r);});
 test(`${label}: duplicate submission and replay return original record`,()=>{const h=fresh(),wire=canonical(syntheticProposal()),a=h.assess(wire);assert.deepEqual(h.assess(wire),{duplicate:true,assessment:a.assessment});assert.equal(h.journal().length,1);assert.ok(verifyJournal(h.journal()));});
 test(`${label}: conflicting duplicate cannot overwrite original`,()=>{const h=fresh(),p=syntheticProposal(),wire=canonical(p),a=h.assess(wire);p.target_ticks=150;assert.equal(h.assess(canonical(p)).assessment.result,'INVALID');assert.deepEqual(h.assess(wire).assessment,a.assessment);assert.ok(verifyJournal(h.journal()));});
 test(`${label}: proposal collision with new event is invalid`,()=>{const h=fresh(),p=syntheticProposal();h.assess(canonical(p));p.event_id='different';assert.equal(h.assess(canonical(p)).assessment.result,'INVALID');});
 test(`${label}: revision and withdrawal transitions`,()=>{const h=fresh(),p=syntheticProposal();h.assess(canonical(p));p.event_id='revision';p.revision=2;p.event_type='PROPOSAL_REVISED';assert.equal(h.assess(canonical(p)).assessment.result,'COMPLIANT');p.event_id='withdraw';p.revision=3;p.event_type='PROPOSAL_WITHDRAWN';assert.equal(h.assess(canonical(p)).assessment.result,'OBSERVED');p.event_id='after-withdraw';p.revision=4;p.event_type='PROPOSAL_REVISED';assert.equal(h.assess(canonical(p)).assessment.result,'INVALID');assert.ok(verifyJournal(h.journal()));});
 test(`${label}: account scope and correlation cannot change`,()=>{for(const field of ['account_id','correlation_id']){const h=fresh(),p=syntheticProposal();h.assess(canonical(p));p.event_id='revision';p.event_type='PROPOSAL_REVISED';p.revision=2;p[field]='other';assert.equal(h.assess(canonical(p)).assessment.result,'INVALID');}});
 test(`${label}: oversight unavailable is observable and non executable`,()=>{const h=fresh({serviceAvailable:false}),wire=canonical(syntheticProposal()),r=h.assess(wire).assessment;assert.equal(r.result,'REVIEW_REQUIRED');assert.ok(r.findings.includes('OVERSIGHT_SERVICE_UNAVAILABLE'));check(r);assert.deepEqual(h.assess(wire).assessment,r);});
 test(`${label}: deterministic audit reproduction and tamper rejection`,()=>{const a=fresh(),b=fresh();for(const raw of [canonical(syntheticProposal()),'{']){a.assess(raw);b.assess(raw);}assert.deepEqual(a.journal(),b.journal());assert.ok(verifyJournal(a.journal()));const altered=a.journal();altered[0].result='OBSERVED';assert.equal(verifyJournal(altered),false);});
 test(`${label}: assessment evidence, governance, errors and correlation fields`,()=>{const r=evaluate();for(const k of ['assessment_id','proposal_id','contract_version','evaluated_at','result','supporting_evidence_refs','governance_checks','validation_errors','correlation_id'])assert.ok(Object.hasOwn(r,k));assert.equal(r.supporting_evidence_refs.length,2);});
 test(`${label}: raw wire must be canonical`,()=>assert.ok(validateWire(JSON.stringify(syntheticProposal(),null,2)).errors.includes('NON_CANONICAL_WIRE')));
 test(`${label}: assessment copies cannot mutate the audit`,()=>{const h=fresh(),r=h.assess(canonical(syntheticProposal()));r.assessment.authority.execution_authorized=true;assert.equal(h.journal()[0].authority.execution_authorized,false);});
 test(`${label}: journal capacity fails without overwriting or crashing`,()=>{const h=fresh({maxRecords:1}),wire=canonical(syntheticProposal());h.assess(wire);assert.equal(h.assess('{').error_code,'JOURNAL_CAPACITY_REACHED');assert.equal(h.journal().length,1);assert.equal(h.assess(wire).duplicate,true);});
 test(`${label}: replay after withdrawal cannot reopen a proposal`,()=>{const h=fresh(),p=syntheticProposal(),wire=canonical(p),first=h.assess(wire);p.event_id='withdraw';p.event_type='PROPOSAL_WITHDRAWN';p.revision=2;h.assess(canonical(p));assert.deepEqual(h.assess(wire),{duplicate:true,assessment:first.assessment});assert.equal(h.journal().length,2);p.event_id='new-revision';p.event_type='PROPOSAL_REVISED';p.revision=3;assert.equal(h.assess(canonical(p)).assessment.result,'INVALID');});
 test(`${label}: audit reordering and truncating the head are detected`,()=>{const h=fresh();h.assess(canonical(syntheticProposal()));h.assess('{');const records=h.journal();assert.equal(verifyJournal([...records].reverse()),false);assert.equal(verifyJournal(records.slice(1)),false);});
}
