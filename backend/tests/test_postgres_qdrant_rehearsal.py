"""Actual dedicated services required; skipped execution is not acceptance."""
import os

import pytest

from evaluation.governed_answers.postgres_qdrant_rehearsal import (
    _Index, run_composition_rehearsal,
)


@pytest.mark.parametrize('url', ['http://127.0.0.1:6333', 'http://localhost:7000',
    'https://127.0.0.1:7000', 'http://127.0.0.1:7000/private',
    'http://user:secret@127.0.0.1:7000', 'http://127.0.0.1:7000?x=1'])
def test_refuse_non_dedicated_qdrant_endpoint_before_io(url):
    with pytest.raises(ValueError):
        _Index(url)


def test_missing_explicit_services_denies_before_io():
    with pytest.raises(ValueError):
        run_composition_rehearsal(dsn=None, qdrant_url=None)


def test_actual_disposable_postgres_qdrant_composition():
    dsn = os.environ.get('SENTINEL_ISOLATED_POSTGRES_DSN')
    url = os.environ.get('SENTINEL_ISOLATED_QDRANT_URL')
    if not dsn or not url:
        pytest.skip('explicit disposable PostgreSQL16 and Qdrant required')
    report = run_composition_rehearsal(dsn=dsn, qdrant_url=url)
    assert report['execution_source'] == 'actual_disposable_postgres_qdrant'
    assert len(report['checks']) == 14
    assert all(report['checks'].values())
    assert report['owned_collection_and_schema_removed'] is True
    assert report['chunks'] == 2 and report['source_bytes'] == 61
    assert report['vector_kind'] == 'fixed_synthetic_not_embeddings'
    for key in ('application_migrated', 'production_enabled', 'release_authorized',
                'governed_eligible', 'authenticated_application_principal', 'semantic_grounding_verified'):
        assert report[key] is False
    assert report['proposition_to_inference'] == 'closed'
    assert 'dsn' not in report and 'text' not in report
