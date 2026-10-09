from pathlib import Path
import pytest
from app.services.workspaces.canon_library import library_documents, read_library_document


def test_library_preserves_relative_provenance_and_duplicate_names(tmp_path):
    (tmp_path / "IDENTITY.md").write_text("# Identity\nHuman judgment", encoding="utf-8")
    (tmp_path / "architecture").mkdir()
    (tmp_path / "architecture" / "IDENTITY.md").write_text("# Architecture identity", encoding="utf-8")
    docs = library_documents(tmp_path)
    assert {doc["path"] for doc in docs} == {"IDENTITY.md", "architecture/IDENTITY.md"}
    result = read_library_document("IDENTITY.md", tmp_path)
    assert result["title"] == "Identity"
    assert result["content"] == "# Identity\nHuman judgment"
    assert result["read_only"] is True
    assert str(tmp_path) not in str(docs)


@pytest.mark.parametrize("path", ["../private.md", "/etc/passwd", "IDENTITY.txt", "nested/../../private.md"])
def test_reader_refuses_arbitrary_paths(tmp_path, path):
    with pytest.raises(ValueError): read_library_document(path, tmp_path)


def test_reader_excludes_symlinks_outside_library_and_handles_missing_files(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    private = tmp_path / "private.md"
    private.write_text("private")
    (root / "outside.md").symlink_to(private)
    assert library_documents(root) == []
    with pytest.raises(ValueError): read_library_document("outside.md", root)
    with pytest.raises(FileNotFoundError): read_library_document("missing.md", root)


def test_reader_bounded_size_and_empty_source(tmp_path, monkeypatch):
    from app.services.workspaces import canon_library
    (tmp_path / "large.md").write_text("# Long content")
    (tmp_path / "empty.md").write_text("")
    monkeypatch.setattr(canon_library, "MAX_DOCUMENT_BYTES", 5)
    with pytest.raises(ValueError): read_library_document("large.md", tmp_path)
    assert read_library_document("empty.md", tmp_path)["content"] == ""


def test_document_route_bounds_read_errors(monkeypatch):
    from app.main import app
    from app.routes import canon
    from fastapi.testclient import TestClient
    def fail(path): raise OSError("private-server-path")
    monkeypatch.setattr(canon, "read_library_document", fail)
    response = TestClient(app).get("/canon/document?path=IDENTITY.md")
    assert response.status_code == 503
    assert "private" not in response.text
