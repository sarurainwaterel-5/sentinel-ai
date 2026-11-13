"""Read-only disposable PostgreSQL authority observations, never authentication.

The caller must independently authenticate principal_id. HTTP headers, vector
payloads and organization parameters are not identity proofs. This adapter is
not registered with the application and cannot authorize publication.
"""
from dataclasses import dataclass, field
import re

from psycopg2 import sql
from psycopg2.extensions import TRANSACTION_STATUS_IDLE

from .postgres_rehearsal import DATABASE
from .scope_catalog_contracts import EvidenceScope


@dataclass(frozen=True)
class PostgresAuthorityObservation:
    principal_id: str
    scope: EvidenceScope
    scope_id: str
    permission_epoch: int
    scope_revision: int
    execution_source: str = field(default='actual_disposable_postgres', init=False)
    authenticated_application_principal: bool = field(default=False, init=False)
    production_enabled: bool = field(default=False, init=False)
    release_authorized: bool = field(default=False, init=False)


class PostgresAuthorityReader:
    """Caller-owned idle connection; scoped repeatable-read observations only.

    No DSN/environment lookup, schema creation, grant inference, writes or retries.
    Rechecks detect observed changes, not a transaction across provider awaits or
    an atomic publication barrier. All grant/disable writers must increment the
    permission epoch: remove/regrant or disable/enable ABA between observations
    is otherwise invisible. The standalone schema does not enforce this protocol.
    Only handles issued by this reader may recheck.
    """
    def __init__(self, connection, *, schema):
        if type(schema) is not str or re.fullmatch(r'sentinel_rehearsal_[0-9a-f]{32}', schema) is None:
            raise ValueError('dedicated_authority_schema_required')
        self._connection = connection
        self._schema = schema
        self._issued = None
        self._terminal = False

    def _observe(self, principal_id, scope):
        if self._terminal:
            raise ValueError('authority_reader_terminal')
        if type(principal_id) is not str or not principal_id.strip() or len(principal_id) > 200:
            raise ValueError('invalid_principal')
        if type(scope) is not EvidenceScope:
            raise ValueError('invalid_scope')
        scope = EvidenceScope.model_validate_json(scope.model_dump_json(), strict=True)
        connection = self._connection
        # Never commit/rollback a caller's existing transaction.
        if connection.get_transaction_status() != TRANSACTION_STATUS_IDLE:
            raise ValueError('idle_dedicated_connection_required')
        with connection:
            with connection.cursor() as cursor:
                cursor.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                cursor.execute("SET LOCAL statement_timeout = '3000ms'")
                cursor.execute("SET LOCAL lock_timeout = '1000ms'")
                cursor.execute("SELECT current_database(),current_setting('server_version_num')::int")
                database, version = cursor.fetchone()
                if database != DATABASE or not 160000 <= version < 170000:
                    raise ValueError('dedicated_postgres16_required')
                cursor.execute(sql.SQL('''
                    SELECT p.permission_epoch,p.disabled,s.scope_id,s.revision
                    FROM {}.principals p
                    JOIN {}.grants g ON g.principal_id=p.principal_id
                    JOIN {}.scopes s ON s.scope_id=g.scope_id
                    WHERE p.principal_id=%s AND s.organization_id=%s
                      AND s.collection=%s AND s.module=%s AND s.topic=%s
                    LIMIT 2
                ''').format(*(sql.Identifier(self._schema) for _ in range(3))),
                    (principal_id, scope.organization_id, scope.collection, scope.module, scope.topic))
                rows = cursor.fetchall()
                if len(rows) != 1:
                    raise ValueError('principal_scope_denied')
                epoch, disabled, scope_id, revision = rows[0]
                if (type(disabled) is not bool or disabled or type(epoch) is not int or epoch < 1
                        or type(revision) is not int or revision < 0
                        or type(scope_id) is not str or not 1 <= len(scope_id) <= 200):
                    raise ValueError('invalid_or_disabled_authority')
                return PostgresAuthorityObservation(principal_id, scope, scope_id, epoch, revision)

    def capture(self, *, principal_id, scope):
        try:
            if self._issued is not None:
                raise ValueError('authority_capture_already_used')
            self._issued = self._observe(principal_id, scope)
            return self._issued
        except Exception:
            self._terminal = True
            raise

    def recheck(self, observation):
        try:
            if observation is not self._issued or observation is None:
                raise ValueError('unbound_authority_observation')
            if self._observe(observation.principal_id, observation.scope) != observation:
                raise ValueError('authority_changed')
            return observation
        except Exception:
            self._terminal = True
            raise
