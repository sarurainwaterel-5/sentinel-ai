"""Versioned reasoning-compatible transport; legacy judge semantics stay frozen."""

from app.services.cognition.reasoning.semantic_admissibility_provider import (
    SemanticAdmissibilityFailure,
    SemanticAdmissibilityRequest,
    SemanticAdmissibilityResponse,
    SemanticJudgeVerdict,
)
from app.services.providers.openai_semantic_admissibility import (
    OpenAISemanticAdmissibilityProvider,
)


class OpenAIReasoningAdmissibilityProvider:
    """Explicit assessment client, bounded output and no fallback or sampling knobs.

    This changes transport compatibility only. Prompt, verdict schema, and the
    caller's strict semantic validation contract remain those of the legacy
    adapter. Model independence must still be established by the deployment.
    """

    ADAPTER_VERSION = "openai-reasoning-admissibility-v1"
    system_message = staticmethod(OpenAISemanticAdmissibilityProvider.system_message)

    def __init__(self, *, client, model: str = "gpt-6-astra",
                 reasoning_effort: str = "low", max_completion_tokens: int = 4096,
                 timeout: float = 30.0, max_retries: int = 0):
        if not isinstance(model, str) or not model.strip():
            raise ValueError("An explicit judge model is required.")
        if reasoning_effort not in {"low", "medium", "high", "xhigh"}:
            raise ValueError("A supported reasoning effort is required.")
        if type(max_completion_tokens) is not int or not 0 < max_completion_tokens <= 16384:
            raise ValueError("max_completion_tokens must be an integer in 1..16384.")
        if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout < float("inf"):
            raise ValueError("timeout must be finite and positive.")
        if type(max_retries) is not int or max_retries != 0:
            raise ValueError("Judge retries must be disabled.")
        self.client = client.with_options(timeout=timeout, max_retries=max_retries)
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_completion_tokens = max_completion_tokens

    def assess(self, *, request: SemanticAdmissibilityRequest) -> SemanticAdmissibilityResponse:
        try:
            if type(self.client.max_retries) is not int or self.client.max_retries != 0:
                raise SemanticAdmissibilityFailure("unavailable")
            completion = self.client.chat.completions.parse(
                model=self.model,
                reasoning_effort=self.reasoning_effort,
                max_completion_tokens=self.max_completion_tokens,
                messages=[{"role": "system", "content": self.system_message()},
                          {"role": "user", "content": request.model_dump_json()}],
                response_format=SemanticJudgeVerdict,
            )
            message = completion.choices[0].message
            if message.refusal:
                raise SemanticAdmissibilityFailure("refused")
            if not isinstance(message.parsed, SemanticJudgeVerdict):
                raise SemanticAdmissibilityFailure("malformed_response")
            content = message.parsed.model_dump_json(warnings="error")
            SemanticJudgeVerdict.model_validate_json(content, strict=True)
            return SemanticAdmissibilityResponse(content=content)
        except SemanticAdmissibilityFailure:
            raise
        except Exception:
            raise SemanticAdmissibilityFailure("unavailable") from None
