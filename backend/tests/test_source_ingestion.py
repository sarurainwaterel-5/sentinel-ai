from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from app.services import upload_service as module


@pytest.fixture
def source(tmp_path, monkeypatch):
    path = tmp_path / 'source.png'
    path.write_bytes(b'image')
    uploader = module.UploadService(None)
    records = []
    class Repository:
        def get_by_hash(self, value): return None
        def create_document(self, **data):
            records.append(data)
            return SimpleNamespace(id=data['document_id'], **{k:v for k,v in data.items() if k != 'document_id'})
    uploader.document_repository = Repository()
    return uploader, path, records


def run(source, progress=None):
    uploader, path, _ = source
    return uploader._index_pdf(file_path=path, filename='source.png', module='engineering', topic='general', collection='general', organization_id='default', description=None, progress=progress)


def test_blank_sources_are_stored_without_embeddings(source, monkeypatch):
    monkeypatch.setattr(module, 'extract_source_text', lambda *a, **kw: dict(text=' \n ', media_type='image/png', extraction_method='ocr', warnings=['no readable text'], metadata={}))
    result = run(source)
    assert result['status'] == 'stored' and result['chunks'] == 0
    assert source[2][0]['status'] == 'stored'
    assert source[0].embedding_service is None
    assert source[1].exists()


def test_missing_tools_preserve_source(source, monkeypatch):
    def unavailable(*args, **kwargs): raise HTTPException(503, 'OCR unavailable')
    monkeypatch.setattr(module, 'extract_source_text', unavailable)
    result = run(source)
    assert result['status'] == 'stored'
    assert result['warnings'] == ['OCR unavailable']
    assert source[1].exists()


def test_extractor_progress_is_adapted_to_mission_stage(source, monkeypatch):
    def extract(*args, **kwargs):
        kwargs['progress']({'phase': 'video_ocr', 'completed_frames': 1})
        return dict(text='', media_type='video/mp4', extraction_method='video_ocr', warnings=[], metadata={})
    monkeypatch.setattr(module, 'extract_source_text', extract)
    stages = []
    run(source, stages.append)
    assert all(isinstance(stage, str) for stage in stages)


def test_invalid_media_keeps_accepted_file_for_failed_mission(source, monkeypatch):
    def invalid(*args, **kwargs): raise HTTPException(422, 'Invalid image')
    monkeypatch.setattr(module, 'extract_source_text', invalid)
    with pytest.raises(HTTPException): run(source)
    assert source[1].exists()


def test_readable_media_indexes_extracted_text_with_provenance(source, monkeypatch):
    import sys
    monkeypatch.setattr(module, 'extract_source_text', lambda *a, **kw: dict(text='Sentinel incident response notes', media_type='image/png', extraction_method='tesseract_english_ocr', warnings=[], metadata={'width':100}))
    stored = []
    def store_chunks(**kwargs):
        stored.append(kwargs)
        return len(kwargs['chunks'])
    monkeypatch.setitem(sys.modules, 'app.services.qdrant_service', SimpleNamespace(store_chunks=store_chunks))
    monkeypatch.setitem(sys.modules, 'app.services.embedding_service', SimpleNamespace(EmbeddingService=lambda: SimpleNamespace(get_model_name=lambda: 'test-model')))
    result = run(source)
    assert result['status'] == 'indexed'
    assert result['characters'] == len('Sentinel incident response notes')
    assert result['extraction_method'] == 'tesseract_english_ocr'
    assert result['metadata']['width'] == 100
    assert stored[0]['organization_id'] == 'default'
    assert source[2][0]['status'] == 'indexed'
