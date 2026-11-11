"""Explicit model selection and credential isolation; no live SDK requests."""
import asyncio
import json
from types import SimpleNamespace as NS

import pytest

from app.services.providers.selected_model_configuration import (
    create_selected_model_clients, selected_configuration, KEY_NAMES, ROLES, EFFORTS, SELECTION,
)


class Client:
    max_retries = 0
    def __init__(self, **kwargs):
        self.responses = self
        self.calls = []
        self.closed = False
        assert kwargs["timeout"] == 30 and kwargs["max_retries"] == 0
    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        text = '{"statement":"Conservative synthesis","premise_ids":["p1","p2"],"relationship_references":[],"qualifications":[]}'
        if kwargs["model"] == "gpt-6-astra":
            from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticJudgeVerdict
            fields = SemanticJudgeVerdict.model_fields
            text = json.dumps({key: [] if key == "rejection_reasons" else key == "admissible" for key in fields})
        if kwargs["model"] == "gpt-6.1-terra":
            digest = json.loads(kwargs["input"][1]["content"])["request_sha256"]
            text = json.dumps({"request_sha256": digest, "answers_question": False,
                               "uncertain": True, "reason": "Synthetic test assessment"})
        return NS(status="completed", error=None, incomplete_details=None,
            output=[NS(type="message", role="assistant", status="completed",
                       content=[NS(type="output_text", text=text)])])
    async def close(self):
        self.closed = True


def keys():
    return {name: "synthetic-role-key-" + role for role, name in KEY_NAMES.items()}


def test_selected_models_and_explicit_reasoning_are_sent_without_sampling():
    async def check():
        created = []
        def factory(**kwargs):
            client = Client(**kwargs)
            created.append(client)
            return client
        configured = await create_selected_model_clients(credentials=keys(), client_factory=factory)
        assert configured.configuration["roles"] == ROLES
        assert configured.configuration["reasoning_efforts"] == EFFORTS
        await configured.transport.call(role="generation", request_json="{}")
        call = created[0].calls[0]
        assert call["model"] == "gpt-6.1-sol" and call["reasoning"] == {"effort": "low"}
        assert "temperature" not in call and "top_p" not in call
        assert created[1].calls == created[2].calls == []
        await configured.transport.call(role="statement", request_json="{}")
        await configured.transport.call(role="relevance", request_json="{}")
        for client, role in zip(created, ROLES):
            assert client.calls[0]["model"] == ROLES[role]
            assert client.calls[0]["reasoning"] == {"effort": EFFORTS[role]}
        assert "synthetic-role-key" not in json.dumps(configured.configuration)
        await configured.close()
        assert all(c.closed for c in created)
    asyncio.run(check())


@pytest.mark.parametrize("missing", list(KEY_NAMES.values()))
def test_missing_dedicated_key_does_not_fall_back_or_construct_clients(missing):
    credentials = keys()
    del credentials[missing]
    credentials["OPENAI_API_KEY"] = "synthetic-general-key"
    def forbidden(**kwargs):
        raise AssertionError("Client construction before key validation")
    with pytest.raises(ValueError, match="Dedicated credential missing"):
        asyncio.run(create_selected_model_clients(credentials=credentials, client_factory=forbidden))


def test_same_client_factory_is_rejected_and_closed():
    client = Client(timeout=30, max_retries=0)
    with pytest.raises(ValueError, match="initialization failed"):
        asyncio.run(create_selected_model_clients(credentials=keys(), client_factory=lambda **kwargs: client))
    assert client.closed and not client.calls


def test_manifest_tampering_cannot_substitute_selected_models(tmp_path):
    data = json.loads(SELECTION.read_text())
    data["roles"]["semantic_judge"] = "gpt-6.1-sol"
    path = tmp_path / "selection.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="selection invalid"):
        selected_configuration(path)


def test_cleanup_attempts_all_clients_and_sanitizes_errors():
    async def check():
        configured = await create_selected_model_clients(credentials=keys(), client_factory=Client)
        async def fail():
            raise RuntimeError("synthetic-secret-error")
        configured._clients[0].close = fail
        with pytest.raises(ValueError, match="cleanup failed") as error:
            await configured.close()
        assert "synthetic-secret" not in str(error.value)
        assert all(client.closed for client in configured._clients[1:])
    asyncio.run(check())
