"""Fake SDK compatibility checks, never empirical semantic evidence."""
from types import SimpleNamespace as NS

import pytest

from app.services.cognition.reasoning.semantic_admissibility_provider import (
    SemanticAdmissibilityFailure, SemanticAdmissibilityRequest, SemanticJudgeVerdict,
)
from app.services.providers.openai_reasoning_admissibility import OpenAIReasoningAdmissibilityProvider
from app.services.providers.openai_semantic_admissibility import OpenAISemanticAdmissibilityProvider


def verdict():
    return SemanticJudgeVerdict(admissible=True, unsupported_fact=False,
        certainty_inflation=False, causal_overreach=False, negation_reversal=False,
        fabricated_precision=False, conflict_suppression=False,
        unsupported_qualification=False, insufficient_support=False, rejection_reasons=())


class Client:
    def __init__(self):
        self.chat = NS(completions=self)
        self.calls = []
        self.options = None
        self.result = NS(choices=[NS(message=NS(refusal=None, parsed=verdict()))])
        self.error = None

    def with_options(self, **kwargs):
        self.options = kwargs
        self.max_retries = kwargs["max_retries"]
        return self

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.result


def request():
    return SemanticAdmissibilityRequest(statement="Untrusted data", qualifications=(), premises=(), relationships=())


def test_reasoning_transport_preserves_exact_prompt_and_schema():
    client = Client()
    provider = OpenAIReasoningAdmissibilityProvider(client=client, timeout=30.0)
    result = provider.assess(request=request())
    assert result.content == verdict().model_dump_json()
    assert client.options == {"timeout": 30.0, "max_retries": 0}
    assert client.calls == [{"model": "gpt-6-astra", "reasoning_effort": "low",
        "max_completion_tokens": 4096, "response_format": SemanticJudgeVerdict,
        "messages": [{"role": "system", "content": OpenAISemanticAdmissibilityProvider.system_message()},
                     {"role": "user", "content": request().model_dump_json()}]}]
    assert provider.ADAPTER_VERSION == "openai-reasoning-admissibility-v1"


@pytest.mark.parametrize("failure,reason", [("refusal", "refused"), ("parsed", "malformed_response"), ("exception", "unavailable"), ("empty", "unavailable")])
def test_failures_fail_closed_without_fallback(failure, reason):
    client = Client()
    if failure == "exception":
        client.error = RuntimeError("private provider failure")
    elif failure == "empty":
        client.result.choices = []
    else:
        setattr(client.result.choices[0].message, failure, "refused" if failure == "refusal" else {})
    provider = OpenAIReasoningAdmissibilityProvider(client=client)
    with pytest.raises(SemanticAdmissibilityFailure) as caught:
        provider.assess(request=request())
    assert caught.value.reason == reason
    assert str(caught.value) == reason
    assert len(client.calls) == 1


@pytest.mark.parametrize("kwargs", [{"model": ""}, {"reasoning_effort": "none"},
    {"max_completion_tokens": 0}, {"max_completion_tokens": 16385}, {"max_completion_tokens": True}, {"timeout": 0},
    {"timeout": float("nan")}, {"timeout": float("inf")}, {"max_retries": -1}, {"max_retries": 1}, {"max_retries": True}])
def test_invalid_configuration_rejected_before_sdk_configuration(kwargs):
    client = Client()
    with pytest.raises(ValueError):
        OpenAIReasoningAdmissibilityProvider(client=client, **kwargs)
    assert client.options is None and client.calls == []


def test_mutated_retry_configuration_blocks_dispatch():
    client = Client()
    provider = OpenAIReasoningAdmissibilityProvider(client=client)
    client.max_retries = 2
    with pytest.raises(SemanticAdmissibilityFailure) as caught:
        provider.assess(request=request())
    assert caught.value.reason == "unavailable" and client.calls == []


def test_bypassed_schema_object_fails_closed():
    client = Client()
    client.result.choices[0].message.parsed = verdict().model_copy(update={"admissible": "yes"})
    provider = OpenAIReasoningAdmissibilityProvider(client=client)
    with pytest.raises(SemanticAdmissibilityFailure):
        provider.assess(request=request())
