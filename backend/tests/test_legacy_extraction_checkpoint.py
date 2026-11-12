import copy
import hashlib

import pytest

from evaluation.governed_answers.legacy_extraction_checkpoint import (
    MAX_CHUNK_HASHES, checkpoint_key, create_checkpoint, extraction_policy_digest,
    reusable_chunk_hashes,
)


def h(value):
    return hashlib.sha256(value.encode()).hexdigest()


@pytest.fixture
def binding():
    return {'source_sha256': h('pdf'), 'byte_length': 100,
            'policy_digest': extraction_policy_digest(pdf_service_sha256=h('extract'),
                                                     chunking_service_sha256=h('chunk'),
                                                     pypdf_version='6.0.0')}


def test_roundtrip_and_no_shared_mutable_lists(binding):
    hashes = [h('one'), h('two'), h('one')]
    record = create_checkpoint(**binding, extraction_chunk_hashes=hashes)
    hashes.clear()
    restored = reusable_chunk_hashes(record, **binding)
    assert restored == [h('one'), h('two'), h('one')]
    restored.clear()
    assert len(record['extraction_chunk_hashes']) == 3


@pytest.mark.parametrize('field,value', [
    ('source_sha256', h('another')), ('byte_length', 101),
    ('policy_digest', h('new_policy')),
])
def test_changed_binding_cannot_resume(binding, field, value):
    record = create_checkpoint(**binding, extraction_chunk_hashes=[h('chunk')])
    assert reusable_chunk_hashes(record, **{**binding, field: value}) is None


@pytest.mark.parametrize('change', [
    {'status': 'failed'}, {'status': 'partial'}, {'status': None},
    {'schema_version': True}, {'schema_version': 2}, {'chunk_count': True},
    {'chunk_count': 2}, {'byte_length': True}, {'checkpoint_key': h('wrong')},
    {'integrity_digest': h('wrong')}, {'source_sha256': 'A' * 64},
    {'extraction_chunk_hashes': []}, {'extraction_chunk_hashes': [h('changed')]},
    {'extraction_chunk_hashes': ('a' * 64,)}, {'extraction_chunk_hashes': ['raw text']},
    {'filename': 'private.pdf'}, {'production_enabled': True},
])
def test_malformed_or_modified_records_fail_closed(binding, change):
    record = create_checkpoint(**binding, extraction_chunk_hashes=[h('chunk')])
    record.update(change)
    assert reusable_chunk_hashes(record, **binding) is None


@pytest.mark.parametrize('value', [None, [], 'private path', 7, True])
def test_nonrecord_is_not_reusable(binding, value):
    assert reusable_chunk_hashes(value, **binding) is None


def test_missing_every_field_fails_closed(binding):
    record = create_checkpoint(**binding, extraction_chunk_hashes=[h('chunk')])
    for name in record:
        partial = copy.deepcopy(record)
        del partial[name]
        assert reusable_chunk_hashes(partial, **binding) is None


@pytest.mark.parametrize('length', [0, -1, True, 1.0, 1024 ** 3 + 1])
def test_source_bounds(binding, length):
    binding['byte_length'] = length
    with pytest.raises(ValueError):
        create_checkpoint(**binding, extraction_chunk_hashes=[h('chunk')])
    assert reusable_chunk_hashes({}, **binding) is None


def test_maximum_source_and_chunk_bounds(binding):
    binding['byte_length'] = 1024 ** 3
    hashes = [h('chunk')] * MAX_CHUNK_HASHES
    record = create_checkpoint(**binding, extraction_chunk_hashes=hashes)
    assert len(reusable_chunk_hashes(record, **binding)) == MAX_CHUNK_HASHES
    with pytest.raises(ValueError):
        create_checkpoint(**binding, extraction_chunk_hashes=hashes + [h('extra')])


@pytest.mark.parametrize('hashes', [None, [], (), [None], ['f' * 63], ['F' * 64]])
def test_invalid_extraction_cannot_be_checkpointed(binding, hashes):
    with pytest.raises(ValueError):
        create_checkpoint(**binding, extraction_chunk_hashes=hashes)


def test_policy_binds_both_files_and_parser_version():
    values = dict(pdf_service_sha256=h('pdf_service'),
                  chunking_service_sha256=h('chunk_service'), pypdf_version='6.0.0')
    original = extraction_policy_digest(**values)
    for name in values:
        changed = {**values, name: '6.0.1' if name == 'pypdf_version' else h('changed')}
        assert extraction_policy_digest(**changed) != original
    assert checkpoint_key(source_sha256=h('source'), byte_length=1, policy_digest=original) != original


@pytest.mark.parametrize('version', ['', None, 'some/path', 'x' * 129, '6.0\nsecret'])
def test_parser_version_has_no_path_or_unbounded_text(version):
    with pytest.raises(ValueError):
        extraction_policy_digest(pdf_service_sha256=h('pdf'),
                                 chunking_service_sha256=h('chunk'), pypdf_version=version)
