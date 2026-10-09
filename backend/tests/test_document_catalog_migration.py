from alembic import command
from alembic.config import Config
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError


def migrated_config(tmp_path):
    url = f"sqlite:///{tmp_path / 'catalog.sqlite3'}"
    config = Config('alembic.ini')
    config.set_main_option('sqlalchemy.url', url)
    return config, create_engine(url)


def test_fresh_migration_supports_document_storage_and_deduplication(tmp_path):
    config, engine = migrated_config(tmp_path)
    command.upgrade(config, 'head')
    assert {'documents', 'reflection_history'} <= set(inspect(engine).get_table_names())
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO documents (id, filename, file_hash, embedding_model) VALUES ('one', 'report.pdf', 'digest', 'test-model')"))
        row = connection.execute(text("SELECT status, organization_id FROM documents WHERE id='one'")).one()
        assert tuple(row) == ('indexed', 'default')
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO documents (id, filename, file_hash, embedding_model) VALUES ('two', 'report.pdf', 'digest', 'test-model')"))


def test_migration_preserves_catalog_created_before_alembic(tmp_path):
    config, engine = migrated_config(tmp_path)
    command.upgrade(config, 'head')
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO documents (id, filename, file_hash, embedding_model) VALUES ('existing', 'existing.pdf', 'existing-hash', 'test-model')"))
    command.stamp(config, '01620884d63e')
    command.upgrade(config, 'head')
    with engine.connect() as connection:
        assert connection.execute(text("SELECT filename FROM documents WHERE id='existing'")).scalar_one() == 'existing.pdf'
