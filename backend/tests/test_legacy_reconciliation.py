"""Pure synthetic inventory audit: no files, network, or live data."""
from copy import deepcopy
import json
import pytest
from evaluation.governed_answers.legacy_reconciliation import reconcile_inventory


def inventory():
    scope = dict(module='m', topic='t', collection='c', organization_id='o')
    catalog = [dict(id='private-document', file_hash='a'*64, **scope, chunk_count=2, status='indexed', embedding_model='embedding')]
    sources = [dict(sha256='a'*64, byte_length=100, readable=True, extraction_chunk_hashes=['b'*64, 'c'*64])]
    points = [dict(point_id=str(i), document_id='private-document', file_hash='a'*64, **scope, status='indexed', embedding_model='embedding', chunk_index=i, chunk_sha256=h*64, chunk_byte_length=10) for i,h in enumerate(('b','c'))]
    capture = dict(catalog_complete=True, sources_complete=True, points_complete=True, extraction_complete=True, catalog_count=1, source_count=1, point_count=2)
    return catalog, sources, points, capture


def test_agreement_is_only_review_ready_and_safe():
    args = inventory()
    before = deepcopy(args)
    report = reconcile_inventory(*args)
    assert report['classification'] == 'ready_for_migration_review'
    assert report['reason_counts'] == {}
    for key in ('eligible', 'real_index_verified', 'epochs_verified', 'authorization_verified', 'release_allowed'):
        assert report[key] is False
    assert args == before
    assert 'private-document' not in json.dumps(report)
    assert report == reconcile_inventory(*args)


@pytest.mark.parametrize('field', ['module','topic','collection','organization_id','file_hash','embedding_model','status'])
def test_point_metadata_mismatch(field):
    args = inventory()
    args[2][0][field] = 'd'*64 if field == 'file_hash' else 'different'
    assert 'point_catalog_mismatch' in reconcile_inventory(*args)['reason_counts']


@pytest.mark.parametrize('change,reason', [
    ('missing_source','missing_source'), ('no_extraction','unverified_extraction'),
    ('wrong_digest','extraction_digest_mismatch'), ('duplicate_point','duplicate_point_id'),
    ('gap','noncontiguous_chunks'), ('duplicate_document','duplicate_document_id'),
    ('unreadable','unreadable_source'), ('source_duplicate','ambiguous_source'),
    ('orphan','orphan_points'), ('partial','incomplete_capture')])
def test_fail_closed(change, reason):
    c,s,p,a = inventory()
    if change == 'missing_source': s.clear(); a['source_count']=0
    elif change == 'no_extraction': s[0]['extraction_chunk_hashes']=None
    elif change == 'wrong_digest': p[0]['chunk_sha256']='d'*64
    elif change == 'duplicate_point': p[1]['point_id']=p[0]['point_id']
    elif change == 'gap': p[1]['chunk_index']=2
    elif change == 'duplicate_document': c.append(deepcopy(c[0])); a['catalog_count']=2
    elif change == 'unreadable': s[0]['readable']=False
    elif change == 'source_duplicate': s.append(deepcopy(s[0])); a['source_count']=2
    elif change == 'orphan': p[0]['document_id']='orphan'
    elif change == 'partial': a['points_complete']=False
    report = reconcile_inventory(c,s,p,a)
    assert report['classification']=='quarantined'
    assert reason in report['reason_counts']


@pytest.mark.parametrize('kind', ['text','bool_count','bad_hash','bad_capture','oversized','null','bool_index'])
def test_malformed_is_sanitized(kind):
    c,s,p,a=inventory()
    if kind=='text': p[0]['text']='secret never output'
    elif kind=='bool_count': c[0]['chunk_count']=True
    elif kind=='bad_hash': s[0]['sha256']='secret never output'
    elif kind=='bad_capture': a['exception']='secret never output'
    elif kind=='oversized': c*=10001
    elif kind=='null': p=None
    elif kind=='bool_index': p[0]['chunk_index']=False
    report=reconcile_inventory(c,s,p,a)
    assert report['classification']=='quarantined'
    assert report['snapshot_sha256'] is None
    assert 'secret never output' not in json.dumps(report)


def test_duplicate_catalog_hash_across_distinct_documents_quarantines_both():
    c,s,p,a = inventory()
    second = dict(c[0], id='another-document')
    c.append(second)
    p.extend([dict(point, point_id='second-'+point['point_id'], document_id=second['id'])
              for point in list(p)])
    a.update(catalog_count=2, point_count=4)
    report = reconcile_inventory(c,s,p,a)
    assert report['classification'] == 'quarantined'
    assert report['reason_counts'] == {'duplicate_catalog_file_hash': 2}
    assert len(report['documents']) == 2
    assert all(doc['classification'] == 'quarantined' and
               doc['reasons'] == ['duplicate_catalog_file_hash']
               for doc in report['documents'])
