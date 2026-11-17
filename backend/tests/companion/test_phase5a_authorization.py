"""Phase 5A real ASGI action isolation and final-publication checks (offline)."""
import asyncio
import base64

import httpx
import pytest

from app.services.companion.api import create_companion_app
from app.services.companion.manager import ConversationManager
from app.services.companion.store import CompanionGrant, ConversationAuthority, ConversationStore
from app.services.governed_authentication import GovernedAuthenticationSession


class Knowledge:
    def authorized(self, checkpoint):
        checkpoint()
        return self

    def snapshot(self):
        return {'capabilities': []}

    def retrieve(self, question, max_items=6):
        return []


@pytest.fixture
def application(sre_setup, tmp_path):
    f = sre_setup
    actions = frozenset({'read', 'converse', 'delete', 'inspect', 'investigate'})
    authority = ConversationAuthority(f['authorizer'], (
        CompanionGrant('operator-sre', 'tenant-a', 'sentinel-ai', actions),
    ))
    store = ConversationStore(tmp_path / 'phase5a-chat.sqlite', authority, create=True)
    conversation = store.create(f['access'], 'tenant-a', 'sentinel-ai', now=f['at'])
    knowledge = Knowledge()
    app = create_companion_app(
        store=store, manager=ConversationManager(store, knowledge), knowledge=knowledge,
        session_factory=lambda: GovernedAuthenticationSession(f['catalog']),
        evidence_scope=f['grant'].evidence_scope, tenant_id='tenant-a',
        application_id='sentinel-ai', sre_store=f['store'], now=lambda: f['at'],
    )
    yield f, store, knowledge, app, conversation['conversation_id']
    store.close()


def request(app, method, path, json=None):
    async def run():
        header = 'Basic ' + base64.b64encode(b'synthetic-sre:synthetic-sre-password').decode()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url='http://offline.test',
                                     headers={'Authorization': header}) as client:
            return await client.request(method, path, json=json)
    return asyncio.run(run())


@pytest.mark.parametrize('action,method,path,body', [
    ('read', 'GET', '/conversations', None),
    ('read', 'GET', '/conversations/{id}', None),
    ('converse', 'POST', '/conversations', {}),
    ('converse', 'POST', '/conversations/{id}/turns',
     {'turn_id': 'denied-turn', 'text': 'architecture', 'expected_revision': 0}),
    ('delete', 'DELETE', '/conversations/{id}', None),
    ('inspect', 'GET', '/capabilities', None),
    ('investigate', 'POST', '/investigations',
     {'service_id': 'sentinel-api', 'observation_ids': ['observation-1'],
      'evaluated_at': '2026-11-16T12:00:00Z'}),
])
def test_each_endpoint_requires_its_explicit_action(application, action, method, path, body):
    f, store, knowledge, app, id = application
    allowed = frozenset({'read', 'converse', 'delete', 'inspect', 'investigate'} - {action})
    store.authority.grants = (CompanionGrant('operator-sre', 'tenant-a', 'sentinel-ai', allowed),)
    response = request(app, method, '/companion/v1' + path.format(id=id), body)
    assert response.status_code == 403
    assert response.json() == {'detail': 'Companion request unavailable'}
    assert store.db.execute('SELECT COUNT(*) FROM conversations').fetchone()[0] == 1
    assert store.db.execute('SELECT COUNT(*) FROM audit').fetchone()[0] == 1


@pytest.mark.parametrize('change', ['disabled', 'credential_epoch', 'permission_epoch', 'scopes'])
def test_catalog_revocation_during_capability_snapshot_is_not_published(application, change):
    f, store, knowledge, app, id = application
    def snapshot():
        f['catalog'].row[change] = True if change == 'disabled' else [] if change == 'scopes' else 2
        return {'capabilities': [{'private_marker': 'must-not-publish'}]}
    knowledge.snapshot = snapshot
    response = request(app, 'GET', '/companion/v1/capabilities')
    assert response.status_code == 403
    assert 'must-not-publish' not in response.text


def test_revocation_during_turn_retrieval_rolls_back_publication(application):
    f, store, knowledge, app, id = application
    def retrieve(*args, **kwargs):
        f['catalog'].row['permission_epoch'] += 1
        return []
    knowledge.retrieve = retrieve
    response = request(app, 'POST', f'/companion/v1/conversations/{id}/turns',
                       {'turn_id': 'revoked-turn', 'text': 'architecture', 'expected_revision': 0})
    assert response.status_code == 403
    assert store.db.execute('SELECT COUNT(*) FROM audit').fetchone()[0] == 1
    assert 'revoked-turn' not in store.db.execute('SELECT document FROM conversations').fetchone()[0]
