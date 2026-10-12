"""Request-local budgets for asynchronous scripted provider calls only.

No provider factories, SDKs, credentials, generation fallback, live evaluation or
runtime wiring. Completion is transport/schema validation, never claim approval.
"""
import asyncio
import hashlib
import inspect
import json
import math
import time
from dataclasses import dataclass, field
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.services.cognition.reasoning.models import CandidateProposition
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticJudgeVerdict
from app.services.cognition.reasoning.answer_models import AnswerClaim, GovernedAnswer
from app.services.cognition.reasoning.answer_orchestrator import OfflineAnswerEvaluation
from .presentation_guard import GuardedPresentation, RelevanceVerdict, _snapshot
from .evidence_scope_guard import ScopedFixturePresentation

STAGES = ("generation", "statement_assessment", "relevance_assessment")


class OfflineBudgetLimits(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    generation_calls: int = Field(default=1, ge=0, le=100)
    statement_assessment_calls: int = Field(default=1, ge=0, le=100)
    relevance_assessment_calls: int = Field(default=1, ge=0, le=100)
    total_calls: int = Field(default=3, ge=0, le=100)
    per_call_timeout_seconds: float = Field(default=1.0, gt=0, le=60, allow_inf_nan=False)
    request_timeout_seconds: float = Field(default=3.0, gt=0, le=120, allow_inf_nan=False)
    max_request_bytes: int = Field(default=100000, ge=1, le=1000000)
    max_response_bytes: int = Field(default=20000, ge=1, le=1000000)
    total_request_bytes: int = Field(default=300000, ge=1, le=3000000)
    total_response_bytes: int = Field(default=60000, ge=1, le=3000000)


@dataclass(frozen=True)
class BudgetedRequest:
    stage: str
    content_json: str
    request_sha256: str


@dataclass(frozen=True)
class BudgetedStageResult:
    status: Literal["completed", "blocked"]
    response_json: str | None
    reason: str | None
    report_json: str
    execution_source: str = field(default="unit_test", init=False)
    empirical_acceptance: bool = field(default=False, init=False)
    release_authorized: bool = field(default=False, init=False)
    production_enabled: bool = field(default=False, init=False)

    def report(self):
        return json.loads(self.report_json)


class ScriptedProviderFailure(Exception):
    def __init__(self, reason):
        if reason not in {"unavailable", "refused"}:
            raise ValueError("Unknown scripted provider failure.")
        self.reason = reason
        super().__init__(reason)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key.")
        result[key] = value
    return result


def _no_constant(value):
    raise ValueError("Non-finite JSON constant.")


def _object_json(text):
    value = json.loads(text, object_pairs_hook=_unique_object, parse_constant=_no_constant)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object.")
    json.dumps(value, allow_nan=False)  # reject overflowed numeric values too
    return value


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


class OfflineProviderBudget:
    """Single-flight session with terminal failure, no retries or partial output.

    Async providers must cooperate with the event loop. Timed-out tasks receive
    cancellation, are quarantined until done, and can never reopen this session.
    No forceful process kill or paid-token/cost enforcement is claimed.
    """
    def __init__(self, limits: OfflineBudgetLimits | None = None, *, clock=time.monotonic):
        limits = limits if limits is not None else OfflineBudgetLimits()
        self._limits = OfflineBudgetLimits.model_validate(limits.model_dump(warnings="error"), strict=True)
        self._clock = clock
        self._started = self._now()
        self._last_time = self._started
        self._calls = {stage: 0 for stage in STAGES}
        self._request_bytes = 0
        self._response_bytes = 0
        self._terminal_reason = None
        self._active = False
        self._pending = set()
        self._loop = None
        self._completed = {}
        self._sealed = False
        self._generation_providers = []
        self._assessment_providers = []

    def _now(self):
        value = self._clock()
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
            raise ValueError("A finite monotonic clock is required.")
        if hasattr(self, "_last_time") and value < self._last_time:
            raise ValueError("Clock moved backwards.")
        self._last_time = value
        return value

    def _finish(self, stage, *, reason=None, content=None, request=None):
        if reason and self._terminal_reason is None:
            self._terminal_reason = reason
            for task in self._pending:
                if not task.done() and not task.cancelling():
                    task.cancel()
        reason = self._terminal_reason
        report = {"schema_version": "21-E-scripted-provider-budget-v1", "stage": stage,
                  "status": "blocked" if reason else "completed", "reason": reason,
                  "calls": dict(self._calls), "total_calls": sum(self._calls.values()),
                  "request_bytes": self._request_bytes, "observed_response_bytes": self._response_bytes,
                  "request_sha256": request.request_sha256 if request else None,
                  "limits": self._limits.model_dump(), "pending_cancelled_tasks": len(self._pending),
                  "execution_source": "unit_test", "empirical_acceptance": False,
                  "production_enabled": False, "release_authorized": False,
                  "semantic_grounding_verified": False, "proposition_to_inference": "closed",
                  "scope": "Scripted transport/resource/schema enforcement only; not statement or question-relevance acceptance."}
        return BudgetedStageResult(report["status"], content if not reason else None, reason, _canonical(report))

    def _forget(self, task):
        self._pending.discard(task)
        # Retrieve errors to avoid unhandled-task warnings; never use late output.
        if not task.cancelled():
            task.exception()

    @staticmethod
    def _validate_response(stage, content, request):
        _object_json(content)  # reject duplicate keys/NaN before schema parsing
        if stage == "generation":
            candidate = CandidateProposition.model_validate_json(content, strict=True)
            if not candidate.statement.strip():
                raise ValueError("Blank candidate.")
        elif stage == "statement_assessment":
            verdict = SemanticJudgeVerdict.model_validate_json(content, strict=True)
            checks = {key for key in SemanticJudgeVerdict.model_fields
                      if key not in {"admissible", "rejection_reasons"} and getattr(verdict, key)}
            if verdict.admissible != (not checks) or set(verdict.rejection_reasons) != checks or len(verdict.rejection_reasons) != len(checks):
                raise ValueError("Contradictory statement verdict.")
        else:
            verdict = RelevanceVerdict.model_validate_json(content, strict=True)
            if verdict.request_sha256 != request.request_sha256:
                raise ValueError("Unbound relevance verdict.")

    async def execute(self, *, stage, request_json, provider):
        stage = stage if isinstance(stage, str) and stage in STAGES else "unknown"
        if self._sealed:
            return self._finish(stage, reason="budget_finalized")
        if self._terminal_reason:
            return self._finish(stage)
        loop = asyncio.get_running_loop()
        if self._loop is not None and self._loop is not loop:
            return self._finish(stage, reason="budget_loop_changed")
        self._loop = loop
        if self._active:
            return self._finish(stage, reason="concurrent_call_not_allowed")
        if stage == "unknown":
            return self._finish(stage, reason="unknown_stage")
        try:
            now = self._now()
            remaining = self._limits.request_timeout_seconds - (now - self._started)
        except Exception:
            return self._finish(stage, reason="invalid_clock")
        if remaining <= 0:
            return self._finish(stage, reason="request_deadline_exceeded")
        if self._calls[stage] >= getattr(self._limits, stage + "_calls") or sum(self._calls.values()) >= self._limits.total_calls:
            return self._finish(stage, reason="call_limit_exceeded")
        if provider is None or getattr(provider, "execution_source", None) != "unit_test" or not inspect.iscoroutinefunction(getattr(provider, "call", None)):
            return self._finish(stage, reason="provider_not_async_scripted")
        prior_providers = self._assessment_providers if stage == "generation" else self._generation_providers
        if any(provider is prior for prior in prior_providers):
            return self._finish(stage, reason="generation_assessment_provider_shared")
        try:
            if not isinstance(request_json, str):
                raise ValueError("Expected serialized request.")
            if len(request_json.encode()) > self._limits.max_request_bytes:
                return self._finish(stage, reason="request_size_exceeded")
            canonical = _canonical(_object_json(request_json))
            request_size = len(canonical.encode())
            if request_size > self._limits.max_request_bytes or self._request_bytes + request_size > self._limits.total_request_bytes:
                return self._finish(stage, reason="request_size_exceeded")
            request = BudgetedRequest(stage, canonical, hashlib.sha256(canonical.encode()).hexdigest())
        except Exception:
            return self._finish(stage, reason="request_malformed")
        timeout = min(self._limits.per_call_timeout_seconds, remaining)
        timeout_reason = "request_deadline_exceeded" if remaining <= self._limits.per_call_timeout_seconds else "provider_timeout"
        self._calls[stage] += 1
        self._request_bytes += request_size
        self._active = True
        (self._generation_providers if stage == "generation" else self._assessment_providers).append(provider)
        task = None
        try:
            task = asyncio.create_task(provider.call(request=BudgetedRequest(
                request.stage, request.content_json, request.request_sha256)))
            self._pending.add(task)
            task.add_done_callback(self._forget)
            try:
                done, _ = await asyncio.wait((task,), timeout=timeout)
            except asyncio.CancelledError:
                task.cancel()
                self._finish(stage, reason="request_cancelled", request=request)
                raise
            if not done:
                task.cancel()
                return self._finish(stage, reason=timeout_reason, request=request)
            if self._terminal_reason:
                return self._finish(stage, request=request)
            try:
                ended = self._now()
            except Exception:
                return self._finish(stage, reason="invalid_clock", request=request)
            if ended - self._started >= self._limits.request_timeout_seconds:
                return self._finish(stage, reason="request_deadline_exceeded", request=request)
            if ended - now >= self._limits.per_call_timeout_seconds:
                return self._finish(stage, reason="provider_timeout", request=request)
            try:
                content = task.result()
            except asyncio.CancelledError:
                return self._finish(stage, reason="provider_cancelled", request=request)
            except ScriptedProviderFailure as error:
                reason = "provider_" + error.reason if error.reason in {"unavailable", "refused"} else "provider_failure"
                return self._finish(stage, reason=reason, request=request)
            except Exception:
                return self._finish(stage, reason="provider_failure", request=request)
            if not isinstance(content, str):
                return self._finish(stage, reason="response_malformed", request=request)
            try:
                size = len(content.encode())
            except Exception:
                return self._finish(stage, reason="response_malformed", request=request)
            self._response_bytes += size
            if size > self._limits.max_response_bytes or self._response_bytes > self._limits.total_response_bytes:
                return self._finish(stage, reason="response_size_exceeded", request=request)
            try:
                self._validate_response(stage, content, request)
            except Exception:
                return self._finish(stage, reason="response_malformed_or_unbound", request=request)
            self._completed[stage] = (request, content)
            return self._finish(stage, content=content, request=request)
        except asyncio.CancelledError:
            raise
        except Exception:
            if task is not None and not task.done():
                task.cancel()
            return self._finish(stage, reason="provider_failure", request=request)
        finally:
            self._active = False


    def guard_presentation(self, presentation):
        """Require complete, current, snapshot-matching receipts before preview.

        Finalization is single-use. No async stage runs here, and no earlier
        partial response can be promoted after a budget failure or deadline.
        """
        def result(report=None, reason=None):
            if reason:
                self._finish("presentation", reason=reason)
            if self._terminal_reason:
                reason = self._terminal_reason
            if reason:
                report = {"execution_source":"unit_test", "empirical_acceptance":False,
                          "public_response":None, "fixture_claim":None, "fixture_text":None}
            receipt = self._finish("presentation").report()
            receipt["status"] = "blocked" if reason else "passed_offline_budget"
            report["provider_budget_guard"] = receipt
            return BudgetedPresentation(_canonical(report), not reason,
                                        (reason,) if reason else ())
        if self._sealed:
            return result(reason="budget_finalized")
        if self._terminal_reason:
            return result(reason=self._terminal_reason)
        if self._active:
            return result(reason="concurrent_call_not_allowed")
        try:
            if self._now() - self._started >= self._limits.request_timeout_seconds:
                return result(reason="request_deadline_exceeded")
        except Exception:
            return result(reason="invalid_clock")
        if type(presentation) not in {GuardedPresentation, ScopedFixturePresentation}:
            return result(reason="unrecognized_presentation")
        if (presentation.execution_source != "unit_test" or presentation.empirical_acceptance is not False
                or presentation.production_enabled is not False or presentation.release_authorized is not False):
            return result(reason="unrecognized_presentation")
        if not presentation.preview_allowed:
            return result(reason="presentation_already_withheld")
        if set(self._completed) != set(STAGES):
            return result(reason="presentation_budget_incomplete")
        try:
            report = presentation.to_component_report()
            if report.get("execution_source") != "unit_test" or report.get("empirical_acceptance") is not False:
                raise ValueError("Non-scripted report.")
            if any(key in report and report[key] is not False for key in (
                    "release_authorized", "production_enabled", "semantic_grounding_verified", "production_presentation_accepted")):
                raise ValueError("Presentation claims authority.")
            if "proposition_to_inference" in report and report["proposition_to_inference"] != "closed":
                raise ValueError("Presentation opens inference.")
            for name in ("presentation_guard", "evidence_scope_guard"):
                metadata = report.get(name)
                if metadata is not None and (not isinstance(metadata,dict)
                        or any(metadata.get(key) is not False for key in (
                            "release_authorized", "production_enabled", "semantic_grounding_verified"))
                        or metadata.get("proposition_to_inference") != "closed"):
                    raise ValueError("Prior guard claims authority.")
            if type(presentation) is ScopedFixturePresentation and (
                    report.get("evidence_scope_guard",{}).get("fixture_scope_checked") is not True
                    or report["evidence_scope_guard"].get("production_authenticated_scope_verified") is not False):
                raise ValueError("Invalid fixture-scope proof.")
            public = GovernedAnswer.model_validate_json(json.dumps(report["public_response"]), strict=True)
            claim = AnswerClaim.model_validate_json(json.dumps(report["fixture_claim"]), strict=True)
            evaluation = OfflineAnswerEvaluation(public_response=public, fixture_claim=claim,
                                                 fixture_text=report["fixture_text"])
            _, _, _, request = _snapshot(evaluation)
            generated_request, generated_content = self._completed["generation"]
            candidate = CandidateProposition.model_validate_json(generated_content, strict=True)
            expected_generation = {"premises":report["public_response"]["premises"],
                                   "relationships":report["public_response"]["relationships"]}
            if generated_request.content_json != _canonical(expected_generation):
                raise ValueError("Generation request not bound to preview inputs.")
            if (candidate.statement != claim.statement or tuple(candidate.qualifications) != claim.qualifications
                    or tuple(candidate.premise_ids) != claim.premise_ids
                    or [r.model_dump(mode="json") for r in candidate.relationship_references]
                    != [r.model_dump(mode="json") for r in claim.relationship_references]):
                raise ValueError("Generation response not bound to preview candidate.")
            statement_request, statement_content = self._completed["statement_assessment"]
            expected_statement = {"statement":claim.statement, "qualifications":list(claim.qualifications),
                "premises":[{"premise_id":p.premise_id,"statement":p.statement} for p in public.premises],
                "relationships":[{"source_premise_id":r.source_premise_id,
                    "target_premise_id":r.target_premise_id,"kind":r.kind.value,"basis":r.basis}
                    for r in public.relationships]}
            if statement_request.content_json != _canonical(expected_statement):
                raise ValueError("Statement request not bound to preview.")
            if SemanticJudgeVerdict.model_validate_json(statement_content,strict=True).admissible is not True:
                raise ValueError("Budgeted statement verdict rejected.")
            relevance_request, relevance_content = self._completed["relevance_assessment"]
            relevance = RelevanceVerdict.model_validate_json(relevance_content,strict=True)
            guard = report["presentation_guard"]
            if (relevance_request.content_json != request.context_json
                    or relevance.request_sha256 != request.request_sha256
                    or not relevance.answers_question or relevance.uncertain
                    or guard.get("status") != "allowed_offline_fixture"
                    or guard.get("request_sha256") != request.request_sha256):
                raise ValueError("Relevance receipt not bound to allowed preview.")
        except Exception:
            return result(reason="presentation_budget_unbound_or_rejected")
        # Validation/rendering must not promote receipts that expire meanwhile.
        try:
            if self._now() - self._started >= self._limits.request_timeout_seconds:
                return result(reason="request_deadline_exceeded")
        except Exception:
            return result(reason="invalid_clock")
        self._sealed = True
        return result(report=report)


@dataclass(frozen=True)
class BudgetedPresentation:
    report_json: str
    preview_allowed: bool
    rejection_reasons: tuple[str, ...]
    execution_source: str = field(default="unit_test", init=False)
    empirical_acceptance: bool = field(default=False, init=False)
    production_enabled: bool = field(default=False, init=False)
    release_authorized: bool = field(default=False, init=False)

    def to_component_report(self):
        return json.loads(self.report_json)
