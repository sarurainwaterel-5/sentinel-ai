"""Synthetic offline negative controls; no trading readiness claim."""
import json
from pathlib import Path
import pytest
from evaluation.trading_oversight.contracts import parse_snapshot, canonical, digest
from evaluation.trading_oversight.evaluator import assess_snapshot
F=Path(__file__).parents[1]/'evaluation/trading_oversight/fixtures'
@pytest.fixture
def data(): return json.loads((F/'snapshot.json').read_text())
def run(d,now=None):
 e=json.loads((F/'expectations.json').read_text())
 return assess_snapshot(parse_snapshot(json.dumps(d).encode()),expected_scope=e['scope'],expected_policy_hashes=e['policy_hashes'],now=now or e['now'])
def codes(r): return {x['code'] for x in r['findings']}
def bind(d): d['payload_sha256']=digest({k:v for k,v in d.items() if k!='payload_sha256'});return d
def test_deterministic_never_authorizes(data):
 r=run(data);assert r==run(data);assert r['overall_status']=='BLOCKED'
 assert r['integrity']=='SELF_CONSISTENT_UNANCHORED'
 assert r['strategy']==r['risk']=='UNVERIFIED'
 assert r['authority']=={'advisory_only':True,'execution_authorized':False,'live_authorized':False}
 assert {'IMAF_DEFINITIONS_UNAPPROVED','SOURCE_AUTHENTICITY_UNVERIFIED','ACCOUNT_RISK_UNVERIFIED'}<=codes(r)
@pytest.mark.parametrize('raw',[b'{"a":1,"a":2}',b'{"x":NaN}',b'{"x":1.5}',b'{"x":9007199254740992}',b'['*18+b'0'+b']'*18,b'{"password":"x"}',b'\xff',b' '*1048577])
def test_reject_bad_input(raw):
 with pytest.raises(ValueError):parse_snapshot(raw)
@pytest.mark.parametrize('field,value',[('execution_authorized',True),('live_authorized',True),('advisory_only',False),('advisory_only',1)])
def test_authority(data,field,value):
 data['authority'][field]=value
 with pytest.raises(ValueError):parse_snapshot(json.dumps(data).encode())
@pytest.mark.parametrize('mutation',['extra','bad_time','known_null','unknown_zero','credential','float','unsafe','bad_imaf','live'])
def test_closed(data,mutation):
 if mutation=='extra':data['extra']=1
 elif mutation=='bad_time':data['clock']['created_at']='2026-02-30T12:00:00.000Z'
 elif mutation=='known_null':data['account_state']['position_quantity']=None
 elif mutation=='unknown_zero':data['account_state']['position_status']='UNKNOWN'
 elif mutation=='credential':data['source']['build_id']='Bearer privatevalue'
 elif mutation=='float':data['account_state']['position_quantity']=0.0
 elif mutation=='unsafe':data['account_state']['position_quantity']=9007199254740992
 elif mutation=='bad_imaf':data['readiness']['imaf_status']='APPROVED'
 else:data['scope']['environment']='LIVE'
 with pytest.raises(ValueError):parse_snapshot(json.dumps(data).encode())
def test_binding(data):
 data['scope']['account_id']='another';data['policy_binding']['risk']='f'*64
 assert {'ACCOUNT_SCOPE_MISMATCH','POLICY_HASH_MISMATCH','PAYLOAD_HASH_MISMATCH'}<=codes(run(data))
@pytest.mark.parametrize('kind',['hash','sequence','head','scope','epoch','future','prior'])
def test_audit(data,kind):
 e=data['audit']['events'][0]
 if kind=='hash':e['hash']='f'*64
 elif kind=='sequence':e['sequence']=2
 elif kind=='head':data['state_binding']['latest_head']='f'*64
 elif kind=='scope':e['payload']['account_id']='wrong'
 elif kind=='epoch':e['payload']['observation_epoch']=2
 elif kind=='future':e['timestamp']='2026-11-15T13:00:00.000Z'
 else:data['state_binding']['prior_sequence']=1
 if kind in {'scope','epoch','future'}:
  e['hash']=digest({k:v for k,v in e.items() if k!='hash'});data['state_binding']['latest_head']=e['hash']
 r=run(bind(data));assert 'AUDIT_CHAIN_INVALID' in codes(r);assert r['integrity']=='INVALID'
def test_unknown(data):
 a=data['account_state'];a['position_status']='UNKNOWN';a['position_quantity']=None
 data['readiness']['reconciliation']='UNKNOWN'
 assert {'EXPOSURE_UNKNOWN','SNAPSHOT_STALE','RECONCILIATION_REQUIRED'}<=codes(run(bind(data),now='2026-11-15T12:05:00.000Z'))
def test_clock_domain(data):
 data['clock']['domain']='WALL';assert 'CLOCK_PROVENANCE_MISMATCH' in codes(run(bind(data)))
def test_canonical():
 assert canonical({'\ue000':1,'😀':2})=='{"😀":2,"\ue000":1}'
 assert canonical({'z':[None,True,-2],'a':'line\n雪'})=='{"a":"line\\n雪","z":[null,true,-2]}'
 for v in [float('nan'),1.5,9007199254740992,'\ud800']:
  with pytest.raises(ValueError):canonical(v)
@pytest.mark.parametrize('value,expected',[
 ({'z':[None,True,-2],'a':'line\n雪'},'4519fd5f61f5418a962fe19ee016889b3bc5e34699c52b24e0877b825a367fb3'),
 ({'\ue000':1,'😀':2},'28c95d1bbb2209223307e62f489020e8f9e0cfa16adf2daf6d88127a1e8dd22a'),
 ({'n':9007199254740991,'text':'\u2028\u2029'},'ce7520de257faa1f34d8c6d48213ae8cbc8838f51a0767b221ab15af0f262e9b')])
def test_actual_trading_js_digest_vectors(value,expected):
 # Generated directly with read-only packages/audit/index.js at pinned source hash.
 assert digest(value)==expected
def test_maximum_invalid_proposals_stays_bounded_and_blocked(data):
 data['proposals']=[{'candidate_id':f'candidate-{i}','candidate_sha256':'b'*64,'direction':'long','entry_ticks':10,'stop_ticks':11,'target_ticks':9,'quantity':1,'expected_costs_cents':0,'imaf_decision_sha256':None,'evidence_refs':[]} for i in range(128)]
 r=run(bind(data))
 assert 'PROPOSAL_GEOMETRY_INVALID' in codes(r)
 assert r['overall_status']=='BLOCKED'
 assert len(next(x for x in r['findings'] if x['code']=='PROPOSAL_GEOMETRY_INVALID')['evidence'])==128

def test_stale_account_cannot_hide_behind_fresh_export(data):
 data['account_state']['as_of']='2026-11-15T11:00:00.000Z'
 assert 'ACCOUNT_STATE_STALE' in codes(run(bind(data)))
