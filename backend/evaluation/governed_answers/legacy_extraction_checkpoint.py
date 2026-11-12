"""Pure integrity checks for resumable legacy extraction, never release evidence.

A digest detects changed checkpoint data; it does not authenticate the extractor
or grant catalog, retrieval, or production eligibility.
"""
import hashlib
import json
import re

MAX_CHUNK_HASHES = 100_000
MAX_SOURCE_BYTES = 1024 ** 3
_HASH = re.compile(r'[0-9a-f]{64}')
_VERSION = re.compile(r'[A-Za-z0-9][A-Za-z0-9.+!_-]{0,127}')
_FIELDS = frozenset({
    'schema_version', 'status', 'source_sha256', 'byte_length', 'policy_digest',
    'checkpoint_key', 'chunk_count', 'extraction_chunk_hashes', 'integrity_digest',
})


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=True).encode('ascii')).hexdigest()


def _hash(value):
    if type(value) is not str or _HASH.fullmatch(value) is None:
        raise ValueError('invalid_digest')
    return value


def extraction_policy_digest(*, pdf_service_sha256, chunking_service_sha256, pypdf_version):
    """Bind the exact two extraction implementations and parser version."""
    if type(pypdf_version) is not str or _VERSION.fullmatch(pypdf_version) is None:
        raise ValueError('invalid_parser_version')
    return _digest({'domain': 'sentinel-legacy-extraction-policy-v1',
                    'pdf_service_sha256': _hash(pdf_service_sha256),
                    'chunking_service_sha256': _hash(chunking_service_sha256),
                    'pypdf_version': pypdf_version})


def checkpoint_key(*, source_sha256, byte_length, policy_digest):
    """Return a content identity, not a secret-key authentication code."""
    if type(byte_length) is not int or not 0 < byte_length <= MAX_SOURCE_BYTES:
        raise ValueError('invalid_source_length')
    return _digest({'domain': 'sentinel-legacy-extraction-checkpoint-v1',
                    'source_sha256': _hash(source_sha256), 'byte_length': byte_length,
                    'policy_digest': _hash(policy_digest)})


def _chunks(value):
    if type(value) is not list or not 0 < len(value) <= MAX_CHUNK_HASHES:
        raise ValueError('invalid_chunk_hashes')
    return [_hash(item) for item in value]


def create_checkpoint(*, source_sha256, byte_length, policy_digest, extraction_chunk_hashes):
    """Record only an extraction that the caller observed finishing successfully.

    Callers must not invoke this for a timeout, partial extraction, or failure.
    This function cannot independently establish that the extraction completed.
    """
    key = checkpoint_key(source_sha256=source_sha256, byte_length=byte_length,
                         policy_digest=policy_digest)
    hashes = _chunks(extraction_chunk_hashes)
    record = {'schema_version': 1, 'status': 'complete',
              'source_sha256': source_sha256, 'byte_length': byte_length,
              'policy_digest': policy_digest, 'checkpoint_key': key,
              'chunk_count': len(hashes), 'extraction_chunk_hashes': hashes}
    return {**record, 'integrity_digest': _digest(record)}


def reusable_chunk_hashes(checkpoint, *, source_sha256, byte_length, policy_digest):
    """Return a fresh hash list only for an intact, complete, exact-bound record."""
    try:
        key = checkpoint_key(source_sha256=source_sha256, byte_length=byte_length,
                             policy_digest=policy_digest)
        if type(checkpoint) is not dict or checkpoint.keys() != _FIELDS:
            return None
        if type(checkpoint['schema_version']) is not int or checkpoint['schema_version'] != 1:
            return None
        if type(checkpoint['status']) is not str or checkpoint['status'] != 'complete':
            return None
        hashes = _chunks(checkpoint['extraction_chunk_hashes'])
        if type(checkpoint['chunk_count']) is not int or checkpoint['chunk_count'] != len(hashes):
            return None
        actual_key = checkpoint_key(source_sha256=checkpoint['source_sha256'],
                                    byte_length=checkpoint['byte_length'],
                                    policy_digest=checkpoint['policy_digest'])
        if actual_key != key or checkpoint['checkpoint_key'] != key:
            return None
        body = {name: value for name, value in checkpoint.items() if name != 'integrity_digest'}
        if _hash(checkpoint['integrity_digest']) != _digest(body):
            return None
        return hashes
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        return None
