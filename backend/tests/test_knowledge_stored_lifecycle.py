"""Catalog-only retained sources must never acquire vector-backed status."""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest


@pytest.fixture
def lifecycle(monkeypatch):
    calls, commits = [], []
    document = SimpleNamespace(id='source-id', filename='retained.png',
                               status='stored', chunk_count=0, embedding_model='not_indexed')
    repository = SimpleNamespace(get_by_id=lambda identifier: document if identifier == document.id else None)
    monkeypatch.setitem(sys.modules, 'app.repositories.document_repository',
                        SimpleNamespace(DocumentRepository=lambda db: repository))
    monkeypatch.setitem(sys.modules, 'app.services.qdrant_service', SimpleNamespace(
        client=SimpleNamespace(set_payload=lambda **kwargs: calls.append(kwargs)),
        COLLECTION_NAME='test-knowledge'))
    # Load a private module instance so no real vector client or database is
    # initialized and other tests retain their normal imported service module.
    path = Path(__file__).parents[1] / 'app/services/knowledge_management_service.py'
    spec = importlib.util.spec_from_file_location('_stored_lifecycle_service', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    db = SimpleNamespace(commit=lambda: commits.append(document.status))
    return module.KnowledgeManagementService(db), document, calls, commits


@pytest.mark.parametrize('chunks,model', [(0, 'not_indexed'), (None, 'not_indexed'),
                                         (0, 'embedding-model'), (5, 'not_indexed')])
def test_stored_source_archive_restore_never_touches_vectors(lifecycle, chunks, model):
    service, document, calls, commits = lifecycle
    document.chunk_count, document.embedding_model = chunks, model
    assert service.archive_document(document.id)['status'] == 'archived'
    assert document.status == 'archived'
    assert service.restore_document(document.id)['status'] == 'restored'
    assert document.status == 'stored'
    assert calls == []
    assert commits == ['archived', 'stored']


def test_indexed_source_archive_restore_updates_only_its_points(lifecycle):
    service, document, calls, commits = lifecycle
    document.status, document.chunk_count, document.embedding_model = 'indexed', 3, 'embedding-model'
    service.archive_document(document.id)
    assert document.status == 'archived'
    service.restore_document(document.id)
    assert document.status == 'indexed'
    assert commits == ['archived', 'indexed']
    assert [call['payload'] for call in calls] == [{'status': 'archived'}, {'status': 'indexed'}]
    for call in calls:
        assert call['collection_name'] == 'test-knowledge'
        assert call['wait'] is True
        conditions = call['points'].must
        assert len(conditions) == 1
        assert conditions[0].key == 'document_id'
        assert conditions[0].match.value == document.id


@pytest.mark.parametrize('operation', ['archive_document', 'restore_document'])
def test_missing_source_changes_neither_catalog_nor_vectors(lifecycle, operation):
    service, _, calls, commits = lifecycle
    assert getattr(service, operation)('missing') == {'status': 'not_found'}
    assert calls == commits == []
