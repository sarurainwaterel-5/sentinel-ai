"""Fake-SDK contract tests only; no model calls or semantic accuracy evidence."""
import asyncio
import json
import hashlib
from types import SimpleNamespace as NS

import pytest

from app.services.providers.openai_governed_transport import (
    GovernedTransportFailure, OpenAIGovernedTransport, RoleConfiguration,
)


def completion(text='{"statement":"Synthesis","premise_ids":["p1","p2"],"relationship_references":[],"qualifications":[]}'):
    return NS(status="completed", error=None, incomplete_details=None,
              output=[NS(type="message", status="completed", role="assistant", content=[NS(type="output_text", text=text)])])


class Client:
    max_retries = 0
    def __init__(self):
        self.responses = self
        self.calls = []
        self.response = completion()
        self.error = None
        self.delay = 0
    async def parse(self, **kwargs):
        self.calls.append(kwargs)
        await asyncio.sleep(self.delay)
        if self.error:
            raise self.error
        return self.response


def bundle(**kwargs):
    clients = [Client() for _ in range(3)]
    configs = [RoleConfiguration(client=c, model=f"explicit-role-{i}") for i, c in enumerate(clients)]
    return OpenAIGovernedTransport(generation=configs[0], statement=configs[1], relevance=configs[2], **kwargs), clients


def run(transport, role="generation", request_json='{"premises":[],"relationships":[]}'):
    return asyncio.run(transport.call(role=role, request_json=request_json))


def test_actual_sdk_request_configuration_without_network():
    transport, clients = bundle()
    result = json.loads(run(transport))
    assert result["statement"] == "Synthesis"
    call = clients[0].calls[0]
    assert call["model"] == "explicit-role-0" and call["store"] is False
    assert call["timeout"] == 30 and call["max_output_tokens"] == 4096
    assert call["truncation"] == "disabled"
    assert call["input"][1]["content"] == '{"premises":[],"relationships":[]}'
    assert clients[1].calls == clients[2].calls == []
    assert transport.execution_source != "unit_test"
    assert not transport.production_enabled and not transport.release_authorized


@pytest.mark.parametrize("role,payload", [
    ("statement", {"admissible": True, "unsupported_fact": False, "certainty_inflation": False,
     "causal_overreach": False, "negation_reversal": False, "fabricated_precision": False,
     "conflict_suppression": False, "unsupported_qualification": False,
     "insufficient_support": False, "rejection_reasons": []}),
    ("relevance", {"request_sha256": hashlib.sha256(b'{"premises":[],"relationships":[]}').hexdigest(), "answers_question": False, "uncertain": True, "reason": "Insufficient support"}),
])
def test_other_role_schema(role, payload):
    transport, clients = bundle()
    clients[["generation", "statement", "relevance"].index(role)].response = completion(json.dumps(payload))
    assert json.loads(run(transport, role=role)) == payload


@pytest.mark.parametrize("text", ["{}", "[]", "null", '{"admissible":true}', '{"x":1,"x":2}', '{"x":NaN}', "not json"])
def test_malformed_output_fails_closed(text):
    transport, clients = bundle()
    clients[0].response = completion(text)
    with pytest.raises(GovernedTransportFailure, match="malformed_response"):
        run(transport)
    assert len(clients[0].calls) == 1


@pytest.mark.parametrize("status", ["incomplete", "failed", "queued", "cancelled"])
def test_incomplete_status_denied(status):
    transport, clients = bundle()
    clients[0].response.status = status
    with pytest.raises(GovernedTransportFailure, match="incomplete"):
        run(transport)


def test_refusal_denied():
    transport, clients = bundle()
    clients[0].response.output[0].content = [NS(type="refusal", refusal="private provider text")]
    with pytest.raises(GovernedTransportFailure, match="refused"):
        run(transport)


@pytest.mark.parametrize("request_text", ['{"x":1,"x":2}', "[]", '{"x":NaN}', "bad"])
def test_bad_request_never_dispatches(request_text):
    transport, clients = bundle()
    with pytest.raises(GovernedTransportFailure):
        run(transport, request_json=request_text)
    assert clients[0].calls == []


def test_budget_limits_and_no_retry_or_exception_leak():
    transport, clients = bundle(max_input_bytes=4)
    with pytest.raises(GovernedTransportFailure, match="budget_exceeded"):
        run(transport)
    assert not clients[0].calls
    transport, clients = bundle(max_output_bytes=4)
    with pytest.raises(GovernedTransportFailure, match="budget_exceeded"):
        run(transport)
    transport, clients = bundle()
    clients[0].error = RuntimeError("synthetic secret that must not leak")
    with pytest.raises(GovernedTransportFailure) as error:
        run(transport)
    assert str(error.value) == "unavailable" and len(clients[0].calls) == 1


def test_timeout_and_cancel_propagate():
    transport, clients = bundle(timeout_seconds=.001)
    clients[0].delay = 1
    with pytest.raises(GovernedTransportFailure, match="timeout"):
        run(transport)
    async def cancel():
        transport, clients = bundle()
        clients[0].delay = 10
        task = asyncio.create_task(transport.call(role="generation", request_json="{}"))
        await asyncio.sleep(.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert len(clients[0].calls) == 1
    asyncio.run(cancel())


def test_separate_clients_models_and_zero_retries_required():
    client = Client()
    config = RoleConfiguration(client, "explicit")
    with pytest.raises(ValueError):
        OpenAIGovernedTransport(generation=config, statement=config, relevance=config)
    transport, clients = bundle()
    clients[0].max_retries = 2
    with pytest.raises(GovernedTransportFailure, match="unavailable"):
        run(transport)
    assert clients[0].calls == []


def test_installed_sdk_responses_parse_with_local_mock_transport():
    """Exercise actual installed SDK serialization/parser without any network."""
    import httpx
    from openai import AsyncOpenAI
    calls = []
    async def handle(request):
        calls.append(json.loads(request.content))
        return httpx.Response(200, json={"id": "resp_synthetic", "object": "response", "created_at": 0,
            "status": "completed", "error": None, "incomplete_details": None,
            "model": "explicit-generation", "output": [{"id": "msg_synthetic", "type": "message",
                "role": "assistant", "status": "completed", "content": [{"type": "output_text",
                    "annotations": [], "text": completion().output[0].content[0].text}]}]})
    async def exercise():
        clients = [AsyncOpenAI(api_key="synthetic-not-a-live-key", max_retries=0,
            http_client=httpx.AsyncClient(transport=httpx.MockTransport(handle))) for _ in range(3)]
        # Avoid SDK host platform discovery in restricted local sandbox; HTTP
        # serialization and Responses parsing still use the installed SDK.
        for client in clients:
            client._platform = "Linux"
        try:
            transport = OpenAIGovernedTransport(**dict(zip(("generation", "statement", "relevance"),
                (RoleConfiguration(c, f"explicit-{r}") for c, r in zip(clients, ("generation", "statement", "relevance"))))))
            result = await transport.call(role="generation", request_json="{}")
            assert json.loads(result)["statement"] == "Synthesis"
        finally:
            for client in clients:
                await client.close()
    asyncio.run(exercise())
    assert len(calls) == 1
    assert calls[0]["store"] is False
    assert calls[0]["text"]["format"]["strict"] is True
    assert calls[0]["text"]["format"]["schema"]["additionalProperties"] is False


@pytest.mark.parametrize("role,request_text", [([], "{}"), ("generation", "\ud800"),
    ("generation", '{"deep":' + '[' * 2000 + '0' + ']' * 2000 + '}'),
    ("relevance", '{"value":"\\ud800"}')], ids=["invalid-role", "surrogate", "deep-json", "escaped-surrogate"])
def test_exceptional_input_bounded_before_dispatch(role, request_text):
    transport, clients = bundle()
    with pytest.raises(GovernedTransportFailure, match="malformed_response"):
        run(transport, role=role, request_json=request_text)
    assert all(not client.calls for client in clients)


def test_unbound_relevance_denied():
    transport, clients = bundle()
    clients[2].response = completion(json.dumps({"request_sha256": "a" * 64,
        "answers_question": True, "uncertain": False, "reason": "Unbound response"}))
    with pytest.raises(GovernedTransportFailure, match="malformed_response"):
        run(transport, role="relevance")


def test_reasoning_item_ignored_but_tool_calls_and_multiple_messages_denied():
    transport, clients = bundle()
    clients[0].response.output.insert(0, NS(type="reasoning", summary=["synthetic private reasoning"]))
    result = run(transport)
    assert "reasoning" not in result
    clients[0].response.output.insert(0, NS(type="function_call"))
    with pytest.raises(GovernedTransportFailure, match="malformed_response"):
        run(transport)
    clients[0].response = completion()
    clients[0].response.output.append(completion().output[0])
    with pytest.raises(GovernedTransportFailure, match="malformed_response"):
        run(transport)
