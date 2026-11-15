"""Independent adversarial checks of the offline advisory boundary."""
import ast
import copy
import json
import os
from pathlib import Path
import socket
import pytest
from evaluation.trading_oversight import cli, contracts, evaluator, report
from evaluation.trading_oversight.reader import read_local
BASE = Path(contracts.__file__).parent
FIXTURES = BASE / 'fixtures'
def values():
    return json.loads((FIXTURES/'snapshot.json').read_bytes()),json.loads((FIXTURES/'expectations.json').read_bytes())
def assess(s):
    s=copy.deepcopy(s); _,e=values()
    s['payload_sha256']=contracts.digest({k:v for k,v in s.items() if k!='payload_sha256'})
    return evaluator.assess_snapshot(contracts.parse_snapshot(json.dumps(s).encode()),expected_scope=e['scope'],expected_policy_hashes=e['policy_hashes'],now=e['now'])
@pytest.mark.parametrize('key,value',[('advisory_only',1),('execution_authorized',0),('live_authorized',0)])
def test_authority_requires_actual_boolean(key,value):
    s,_=values();s['authority'][key]=value
    with pytest.raises(ValueError):contracts.parse_snapshot(json.dumps(s).encode())
@pytest.mark.parametrize('mutation,code',[('account','ACCOUNT_SCOPE_MISMATCH'),('policy','POLICY_HASH_MISMATCH'),('replay','CLOCK_PROVENANCE_MISMATCH'),('unknown','EXPOSURE_UNKNOWN')])
def test_changed_claims_fail_closed(mutation,code):
    s,_=values()
    if mutation=='account':s['scope']['account_id']='another-account'
    if mutation=='policy':s['policy_binding']['risk']='0'*64
    if mutation=='replay':s['provenance']['kind']='historical-replay'
    if mutation=='unknown':s['account_state'].update(position_status='UNKNOWN',position_quantity=None)
    result=assess(s)
    assert code in {f['code'] for f in result['findings']}
    assert result['overall_status']=='BLOCKED' and result['authority']==report.AUTHORITY

def test_tv_claims_cannot_authenticate_origin_or_risk():
    s,_=values();result=assess(s)
    assert result['integrity']=='SELF_CONSISTENT_UNANCHORED'
    assert {'SOURCE_AUTHENTICITY_UNVERIFIED','ACCOUNT_RISK_UNVERIFIED','IMAF_DEFINITIONS_UNAPPROVED'}<={f['code'] for f in result['findings']}
    s['provenance']['authenticity']='VERIFIED_CHANNEL'
    with pytest.raises(ValueError):assess(s)

def test_symlink_components_and_fifo_rejected(tmp_path):
    p=tmp_path/'source';p.write_bytes(b'{}')
    a=tmp_path/'alias';a.symlink_to(p)
    d=tmp_path/'parent';d.symlink_to(tmp_path,target_is_directory=True)
    f=tmp_path/'fifo';os.mkfifo(f)
    for candidate in (a,d/p.name,f):
        with pytest.raises((OSError,ValueError)):read_local(candidate)

def test_cli_offline_and_review_has_no_authority_effect(tmp_path,monkeypatch):
    def forbidden(*a,**k):raise AssertionError('network attempted')
    monkeypatch.setattr(socket,'socket',forbidden);monkeypatch.setattr(socket,'create_connection',forbidden)
    s,e=values();p=tmp_path/'snapshot.json';p.write_text(json.dumps(s))
    x=tmp_path/'expectations.json';x.write_text(json.dumps(e));out=tmp_path/'report'
    cli.inspect(input_path=str(p),expectations_path=str(x),now=e['now'],output_dir=str(out))
    before={f.name:f.read_bytes() for f in out.iterdir()}
    cli.review(report_dir=str(out),decision='accept',reviewer='Rain',at=e['now'])
    r=json.loads((out/'human-review.json').read_bytes())
    assert r['authority']==report.AUTHORITY and r['decision']=='accept'
    assert all((out/name).read_bytes()==raw for name,raw in before.items())
    assert p.read_text()==json.dumps(s)
    with pytest.raises(FileExistsError):cli.review(report_dir=str(out),decision='accept',reviewer='Rain',at=e['now'])

def test_renderer_escapes_untrusted_text():
    html=report.render_report({'observation':'</pre><script>alert(1)</script>'}).decode()
    assert '<script>' not in html and '&lt;script&gt;' in html and "default-src 'none'" in html

def test_no_service_database_broker_or_execution_imports():
    allowed={'__future__','argparse','csv','datetime','hashlib','html','io','json','os','pathlib','pydantic','re','stat','sys','typing'}
    for p in BASE.glob('*.py'):
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node,ast.Import):assert all(a.name.split('.')[0] in allowed for a in node.names),p
            if isinstance(node,ast.ImportFrom) and not node.level:assert node.module.split('.')[0] in allowed,p
