"""Synthetic local CSV evidence tests; no TradingView session or network."""
import json
import os
import pytest
from evaluation.trading_oversight.tradingview import capture, summarize_csv, main


def test_capture_preserves_bytes_unknowns_and_rejects_reuse(tmp_path):
    raw=b'Order ID,Status,Price\r\nsynthetic-1,Filled,100.25\r\n'
    path=tmp_path/'paper.csv';path.write_bytes(raw);out=tmp_path/'evidence'
    result=capture(inputs=[path],organization_id='default',account_id='paper-demo',captured_at='2026-11-15T12:00:00.000Z',output_dir=out)
    assert (out/'evidence-001.csv').read_bytes()==raw
    assert result['files'][0]['data_rows']==1
    assert result['files'][0]['export_tab']=='UNKNOWN'
    assert result['files'][0]['coverage']=='UNKNOWN'
    assert result['trade_count'] is None and result['position']['status']=='UNKNOWN'
    assert result['semantic_mapping']=='NOT_IMPLEMENTED' and not result['source_authenticated']
    assert result['authority']=={'advisory_only':True,'execution_authorized':False,'live_authorized':False}
    assert os.stat(out).st_mode&0o777==0o700
    assert os.stat(out/'evidence.json').st_mode&0o777==0o600
    with pytest.raises(FileExistsError):capture(inputs=[path],organization_id='default',account_id='paper-demo',captured_at='2026-11-15T12:00:00.000Z',output_dir=out)
    assert json.loads((out/'evidence.json').read_text())==result


@pytest.mark.parametrize('raw',[b'',b'a,a\n1,2\n',b'a\n1,2\n',b'password\nx\n',b'a\n"unterminated',b'a\n\x00',b'a\n\xff',b'a\n'+b'v\n'*10001])
def test_bad_csv_rejected(raw):
    with pytest.raises((ValueError,UnicodeError)):summarize_csv(raw)


def test_link_or_bad_input_creates_no_output(tmp_path):
    p=tmp_path/'original.csv';p.write_text('A,B\n1,2\n');link=tmp_path/'link.csv';link.symlink_to(p)
    with pytest.raises(OSError):capture(inputs=[link],organization_id='default',account_id='paper-demo',captured_at='2026-11-15T12:00:00.000Z',output_dir=tmp_path/'out')
    assert not (tmp_path/'out').exists()
    with pytest.raises(ValueError):capture(inputs=[p,p],organization_id='default',account_id='paper-demo',captured_at='2026-11-15T12:00:00.000Z',output_dir=tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_explicit_tabs_bind_by_input_order_without_establishing_semantics(tmp_path):
    paths=[tmp_path/'one.csv',tmp_path/'two.csv']
    paths[0].write_bytes(b'Example\nfirst\n')
    paths[1].write_bytes(b'Example\nsecond\n')
    result=capture(inputs=paths,tabs=['POSITIONS','HISTORY'],organization_id='default',
                   account_id='paper-demo',captured_at='2026-11-15T12:00:00.000Z',output_dir=tmp_path/'out')
    assert [f['export_tab'] for f in result['files']]==['POSITIONS','HISTORY']
    assert all(f['export_tab_source']=='OPERATOR_SUPPLIED' and f['coverage']=='UNKNOWN' for f in result['files'])
    assert result['position']['status']=='UNKNOWN' and result['trade_count'] is None
    assert result['semantic_mapping']=='NOT_IMPLEMENTED' and not result['source_authenticated']


@pytest.mark.parametrize('tabs',[[],['POSITIONS','HISTORY'],['positions'],['PASSWORD'],[False],'POSITIONS'])
def test_bad_tab_labels_create_no_bundle(tmp_path,tabs):
    path=tmp_path/'one.csv';path.write_bytes(b'Example\nvalue\n')
    with pytest.raises(ValueError):
        capture(inputs=[path],tabs=tabs,organization_id='default',account_id='paper-demo',
                captured_at='2026-11-15T12:00:00.000Z',output_dir=tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_cli_retains_export_tab_label(tmp_path,capsys):
    path=tmp_path/'input.csv';path.write_bytes(b'Example\nvalue\n')
    out=tmp_path/'out'
    assert main(['capture','--input',str(path),'--tab','ORDERS','--organization-id','default',
                 '--account-id','paper-demo','--captured-at','2026-11-15T12:00:00.000Z',
                 '--output-dir',str(out)])==0
    assert json.loads((out/'evidence.json').read_text())['files'][0]['export_tab']=='ORDERS'
    assert json.loads(capsys.readouterr().out)['execution_authorized'] is False
