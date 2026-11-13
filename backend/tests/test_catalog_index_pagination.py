"""Index page failure injection, no external services or embedding claims."""
import uuid
from types import SimpleNamespace
import pytest
from evaluation.governed_answers.catalog_index_reconciler import GovernedRehearsalIndex,ReconciliationDenied,CatalogIndexReconciler,FixtureVectorAdapter


def index_with_pages(pages):
    index=object.__new__(GovernedRehearsalIndex)
    index.collection='synthetic'
    iterator=iter(pages)
    index.http=SimpleNamespace(call=lambda *args:next(iterator))
    return index


def point(identifier):return dict(id=identifier,payload={})


def test_late_duplicate_across_pages_denies():
    identity=str(uuid.uuid4());cursor=str(uuid.uuid4())
    index=index_with_pages([dict(points=[point(identity)],next_page_offset=cursor),dict(points=[point(identity)],next_page_offset=None)])
    with pytest.raises(ReconciliationDenied,match='duplicate'):index.read_all('document')


def test_repeated_scroll_cursor_denies():
    cursor=str(uuid.uuid4())
    index=index_with_pages([dict(points=[point(str(uuid.uuid4()))],next_page_offset=cursor),dict(points=[point(str(uuid.uuid4()))],next_page_offset=cursor)])
    with pytest.raises(ReconciliationDenied,match='cursor'):index.read_all('document')


def test_oversized_page_and_non_uuid_cursor_deny():
    for page in [dict(points=[point(str(uuid.uuid4())) for _ in range(257)],next_page_offset=None),dict(points=[point(str(uuid.uuid4()))],next_page_offset=True)]:
        with pytest.raises(ReconciliationDenied):index_with_pages([page]).read_all('document')


def test_dimension_mismatch_denies_before_io():
    with pytest.raises(ReconciliationDenied,match='dimension'):
        CatalogIndexReconciler(None,chunk_store=None,index=SimpleNamespace(dimension=2),vector_adapter=FixtureVectorAdapter())


@pytest.mark.parametrize('timeout,lease',[(0,120),(3601,120),(True,120),(float('nan'),120),(1,0),(1,121),(1,True)])
def test_worker_budget_denies_before_claim(timeout,lease):
    worker=CatalogIndexReconciler(None,chunk_store=None,index=None)
    with pytest.raises(ValueError):worker.reconcile_once(timeout_seconds=timeout,lease_seconds=lease)
