"""Storage corruption fails closed without exposing parser internals over HTTP."""
import asyncio
import base64

import httpx
import pytest

from app.services.companion.api import create_companion_app
from app.services.companion.store import CompanionGrant, ConversationAuthority, ConversationStore
from app.services.governed_authentication import GovernedAuthenticationSession
from app.services.sre.contracts import SREError, digest


@pytest.fixture
def private_chat(sre_setup, tmp_path):
    f = sre_setup
    authority = ConversationAuthority(f['authorizer'], (
        CompanionGrant('operator-sre', 'tenant-a', 'sentinel-ai', frozenset({'read', 'converse'})),
    ))
    store = ConversationStore(tmp_path / 'phase5a-chat.sqlite', authority, create=True)
    store.create(f['access'], 'tenant-a', 'sentinel-ai', now=f['at'])
    yield f, store
    store.close()


def stored_rows(store):
    return {table: [tuple(row) for row in store.db.execute('SELECT * FROM '+table)]
            for table in ('conversations', 'audit')}


@pytest.mark.parametrize('table,document', [
    ('conversations', '{malformed-private-document'),
    ('audit', '{malformed-private-audit'),
    ('audit', '{}'),
])
def test_corrupt_storage_is_bounded_and_unchanged(private_chat, table, document):
    f, store = private_chat
    store.db.execute('UPDATE '+table+' SET document=?', (document,))
    if document == '{}':
        store.db.execute('UPDATE audit SET digest=?', (digest({}),))
    before = stored_rows(store)
    with pytest.raises(SREError, match='^CONVERSATION_OPERATION_FAILED$'):
        store.list(f['access'], 'tenant-a', 'sentinel-ai', now=f['at'])
    assert not store.db.in_transaction
    assert stored_rows(store) == before


def test_failed_write_rolls_back_and_domain_errors_survive(private_chat):
    f, store = private_chat
    before = stored_rows(store)
    with pytest.raises(SREError, match='^CONVERSATION_OPERATION_FAILED$'):
        with store.transaction(f['access'], 'tenant-a', 'sentinel-ai', 'converse'):
            store.db.execute('DELETE FROM conversations')
            raise KeyError('private implementation detail')
    assert stored_rows(store) == before
    assert not store.db.in_transaction
    with pytest.raises(SREError, match='^EXPLICIT_DOMAIN_FAILURE$'):
        with store.transaction(f['access'], 'tenant-a', 'sentinel-ai', 'read'):
            raise SREError('EXPLICIT_DOMAIN_FAILURE')


def test_api_corrupt_storage_returns_generic_error(private_chat):
    f, store = private_chat
    store.db.execute("UPDATE audit SET document='{private malformed audit'")
    before = stored_rows(store)
    app = create_companion_app(
        store=store, manager=None, knowledge=None,
        session_factory=lambda: GovernedAuthenticationSession(f['catalog']),
        evidence_scope=f['grant'].evidence_scope,
        tenant_id='tenant-a', application_id='sentinel-ai', now=lambda: f['at'],
    )

    async def request():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://offline.test') as client:
            authorization = 'Basic '+base64.b64encode(b'synthetic-sre:synthetic-sre-password').decode()
            response = await client.get('/companion/v1/conversations', headers={'Authorization': authorization})
            assert response.status_code == 403
            assert response.json() == {'detail': 'Companion request unavailable'}

    asyncio.run(request())
    assert stored_rows(store) == before
    assert not store.db.in_transaction
