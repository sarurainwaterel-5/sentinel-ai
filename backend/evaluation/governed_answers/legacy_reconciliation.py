"""Bounded, pure legacy snapshot audit. Metadata agreement grants no authority.

Inputs must exclude text, paths, filenames and credentials. Digests bind only the
explicit snapshots; capture completeness is a caller assertion, not live proof.
"""
import hashlib
import json
import re
from collections import Counter

from .legacy_source_capture import MAX_SOURCE_BYTES

MAX_ROWS = 100000
MAX_DOCUMENTS = 1000
SCOPE = ('module', 'topic', 'collection', 'organization_id')
CATALOG = {'id', 'file_hash', *SCOPE, 'chunk_count', 'status', 'embedding_model'}
SOURCE = {'sha256', 'byte_length', 'readable', 'extraction_chunk_hashes'}
POINT = {'point_id', 'document_id', 'file_hash', *SCOPE, 'status', 'embedding_model', 'chunk_index', 'chunk_sha256', 'chunk_byte_length'}
CAPTURE = {f'{name}_complete' for name in ('catalog', 'sources', 'points', 'extraction')} | {'catalog_count', 'source_count', 'point_count'}


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()).hexdigest()


def _name(value):
    return type(value) is str and 0 < len(value) <= 256 and not any(ord(c) < 32 for c in value)


def _sha(value):
    return type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None


def _integer(value, minimum=0):
    return type(value) is int and minimum <= value <= MAX_ROWS


def reconcile_inventory(catalog, sources, points, capture):
    """Return sanitized quarantine/review findings; never migration eligibility."""
    report = {'schema_version': 1, 'classification': 'quarantined', 'eligible': False,
              'real_index_verified': False, 'epochs_verified': False,
              'authorization_verified': False, 'release_allowed': False,
              'snapshot_sha256': None, 'documents': [], 'reason_counts': {}}
    reasons = Counter()
    def blocked(reason):
        reasons[reason] += 1
        report['reason_counts'] = dict(sorted(reasons.items()))
        return report
    if (type(catalog) is not list or type(sources) is not list or type(points) is not list
            or len(catalog) > MAX_DOCUMENTS or len(sources) > MAX_DOCUMENTS or len(points) > MAX_ROWS):
        return blocked('invalid_inventory_bounds')
    if (type(capture) is not dict or set(capture) != CAPTURE
            or any(type(capture[k]) is not bool for k in CAPTURE if k.endswith('_complete'))
            or any(not _integer(capture[k]) for k in CAPTURE if k.endswith('_count'))):
        return blocked('invalid_capture')
    complete = all(capture[k] for k in CAPTURE if k.endswith('_complete'))
    if not complete:
        reasons['incomplete_capture'] += 1
    if [capture[k] for k in ('catalog_count', 'source_count', 'point_count')] != list(map(len, (catalog, sources, points))):
        return blocked('capture_count_mismatch')
    # Reject extra fields before hashing, to avoid accepting text/private metadata.
    for rows, keys in ((catalog, CATALOG), (sources, SOURCE), (points, POINT)):
        if any(type(row) is not dict or set(row) != keys for row in rows):
            return blocked('invalid_row_schema')
    for row in catalog:
        if (not all(_name(row[k]) for k in ('id', *SCOPE, 'status', 'embedding_model'))
                or not _sha(row['file_hash']) or not _integer(row['chunk_count'], 1)):
            return blocked('invalid_catalog_row')
    if sum(row['chunk_count'] for row in catalog) > MAX_ROWS:
        return blocked('invalid_catalog_chunk_bounds')
    for row in sources:
        hashes = row['extraction_chunk_hashes']
        if (not _sha(row['sha256']) or type(row['readable']) is not bool
                or type(row['byte_length']) is not int or not 0 <= row['byte_length'] <= MAX_SOURCE_BYTES
                or (hashes is not None and (type(hashes) is not list or not 1 <= len(hashes) <= MAX_ROWS or not all(_sha(h) for h in hashes)))):
            return blocked('invalid_source_row')
    if sum(len(row['extraction_chunk_hashes'] or []) for row in sources) > MAX_ROWS:
        return blocked('invalid_extraction_bounds')
    for row in points:
        if (not all(_name(row[k]) for k in ('point_id', 'document_id', *SCOPE, 'status', 'embedding_model'))
                or not _sha(row['file_hash']) or not _sha(row['chunk_sha256'])
                or not _integer(row['chunk_index']) or type(row['chunk_byte_length']) is not int
                or not 0 < row['chunk_byte_length'] <= 1048576):
            return blocked('invalid_point_row')
    report['snapshot_sha256'] = _hash({'catalog': catalog, 'sources': sources, 'points': points, 'capture': capture})
    ids = Counter(r['id'] for r in catalog)
    catalog_hashes = Counter(r['file_hash'] for r in catalog)
    hashes = Counter(r['sha256'] for r in sources)
    point_ids = Counter(r['point_id'] for r in points)
    source_map = {r['sha256']: r for r in sources}
    grouped = {}
    for p in points:
        grouped.setdefault(p['document_id'], []).append(p)
    if any(n > 1 for n in point_ids.values()):
        reasons['duplicate_point_id'] += 1
    if set(grouped) - set(ids):
        reasons['orphan_points'] += len(set(grouped) - set(ids))
    if set(hashes) - {r['file_hash'] for r in catalog}:
        reasons['unreferenced_sources'] += len(set(hashes) - {r['file_hash'] for r in catalog})
    for row in catalog:
        failures = set()
        if not complete: failures.add('incomplete_capture')
        if ids[row['id']] != 1: failures.add('duplicate_document_id')
        if catalog_hashes[row['file_hash']] != 1: failures.add('duplicate_catalog_file_hash')
        src = source_map.get(row['file_hash'])
        if src is None: failures.add('missing_source')
        elif hashes[row['file_hash']] != 1: failures.add('ambiguous_source')
        elif not src['readable']: failures.add('unreadable_source')
        if row['status'] != 'indexed': failures.add('catalog_not_indexed')
        chunks = grouped.get(row['id'], [])
        ordered = sorted(chunks, key=lambda p: p['chunk_index'])
        if len(chunks) != row['chunk_count']: failures.add('chunk_count_mismatch')
        if [p['chunk_index'] for p in ordered] != list(range(row['chunk_count'])):
            failures.add('noncontiguous_chunks')
        for p in chunks:
            if point_ids[p['point_id']] != 1: failures.add('duplicate_point_id')
            if any(p[k] != row[k] for k in ('file_hash', *SCOPE, 'status', 'embedding_model')):
                failures.add('point_catalog_mismatch')
        if src is None or src['extraction_chunk_hashes'] is None:
            failures.add('unverified_extraction')
        elif src['extraction_chunk_hashes'] != [p['chunk_sha256'] for p in ordered]:
            failures.add('extraction_digest_mismatch')
        reasons.update(failures)
        report['documents'].append({'document_id_sha256': _hash(row['id']),
            'classification': 'quarantined' if failures else 'ready_for_migration_review',
            'eligible': False, 'reasons': sorted(failures)})
    if not catalog: reasons['empty_catalog'] += 1
    if not reasons: report['classification'] = 'ready_for_migration_review'
    report['reason_counts'] = dict(sorted(reasons.items()))
    return report
