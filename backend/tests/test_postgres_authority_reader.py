"""Optional real database test is not counted as executed when skipped."""
import os
import uuid
from dataclasses import replace

import psycopg2
from psycopg2 import sql
import pytest

from evaluation.governed_answers.postgres_authority_reader import PostgresAuthorityReader
from evaluation.governed_answers.postgres_rehearsal import DDL_PATH, _schema
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope


@pytest.mark.parametrize('schema', ['public', 'sentinel_rehearsal_', 'sentinel_rehearsal_'+'a'*32+';DROP', None])
def test_schema_allowlist_before_io(schema):
    with pytest.raises(ValueError):
        PostgresAuthorityReader(None, schema=schema)


def test_actual_authority_observations():
    dsn = os.environ.get('SENTINEL_ISOLATED_POSTGRES_DSN')
    if not dsn:
        pytest.skip('explicit disposable PostgreSQL16 required')
    conn = psycopg2.connect(dsn, connect_timeout=5)
    other = psycopg2.connect(dsn, connect_timeout=5)
    schema = 'sentinel_rehearsal_' + uuid.uuid4().hex
    scope = EvidenceScope(organization_id='org', collection='manuals', module='ir', topic='sre')
    # Refuse wrong databases before creating any schema.
    with conn:
        with conn.cursor() as c:
            c.execute('SELECT current_database()')
            assert c.fetchone()[0] == 'sentinel_sprint21_rehearsal'
    _schema(conn, schema, DDL_PATH.read_text())
    def mutate(statement):
        with other:
            with other.cursor() as c:
                c.execute(sql.SQL('SET LOCAL search_path TO {},pg_catalog').format(sql.Identifier(schema)))
                c.execute(statement)
    def reader():
        return PostgresAuthorityReader(conn, schema=schema)
    try:
        mutate("INSERT INTO principals VALUES('alice',1,false),('bob',1,false)")
        mutate("INSERT INTO scopes VALUES('scope','org','manuals','ir','sre',0)")
        mutate("INSERT INTO grants VALUES('alice','scope')")
        r = reader(); observed = r.capture(principal_id='alice', scope=scope)
        assert r.recheck(observed) is observed
        assert not observed.production_enabled and not observed.authenticated_application_principal
        with pytest.raises(ValueError, match='authority_capture_already_used'):
            r.capture(principal_id='alice', scope=scope)
        with pytest.raises(ValueError, match='authority_reader_terminal'):
            r.recheck(observed)
        r = reader(); observed = r.capture(principal_id='alice', scope=scope)
        # ABA by writers violating the epoch protocol is invisible to observations.
        mutate("DELETE FROM grants WHERE principal_id='alice'")
        mutate("INSERT INTO grants VALUES('alice','scope')")
        assert r.recheck(observed) is observed
        with pytest.raises(ValueError):
            reader().capture(principal_id='bob', scope=scope)
        with pytest.raises(ValueError):
            reader().capture(principal_id='alice', scope=scope.model_copy(update={'topic':'other'}))
        with pytest.raises(ValueError):
            r.recheck(replace(observed))
        r = reader(); observed = r.capture(principal_id='alice', scope=scope)
        mutate("UPDATE principals SET permission_epoch=permission_epoch+1 WHERE principal_id='alice'")
        with pytest.raises(ValueError, match='authority_changed'):
            r.recheck(observed)
        r = reader(); observed = r.capture(principal_id='alice', scope=scope)
        mutate("DELETE FROM grants WHERE principal_id='alice'")
        with pytest.raises(ValueError):
            r.recheck(observed)
        mutate("INSERT INTO grants VALUES('alice','scope')")
        r = reader(); observed = r.capture(principal_id='alice', scope=scope)
        mutate("UPDATE scopes SET revision=revision+1 WHERE scope_id='scope'")
        with pytest.raises(ValueError, match='authority_changed'):
            r.recheck(observed)
        r = reader(); observed = r.capture(principal_id='alice', scope=scope)
        mutate("UPDATE principals SET disabled=true WHERE principal_id='alice'")
        with pytest.raises(ValueError):
            r.recheck(observed)
        with conn.cursor() as c:
            c.execute('SELECT 1')
        with pytest.raises(ValueError, match='idle_dedicated_connection_required'):
            reader().capture(principal_id='alice', scope=scope)
        conn.rollback()
    finally:
        conn.rollback()
        with conn:
            with conn.cursor() as c:
                c.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))
        conn.close(); other.close()
