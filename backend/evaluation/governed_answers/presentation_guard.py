"""Additive offline presentation eligibility; never a production release gate.

A scripted relevance assessment is independent of statement admissibility. Missing,
negative, uncertain, malformed, unbound or stale assessments withhold the preview.
The original coordinator, renderer, contracts and production routes are unchanged.
"""
import hashlib
import json
from dataclasses import dataclass, field
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.cognition.reasoning.answer_models import AnswerClaim, GovernedAnswer
from app.services.cognition.reasoning.answer_orchestrator import OfflineAnswerEvaluation
from app.services.cognition.reasoning.answer_renderer import render_fixture


def _canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


class RelevanceRequest(BaseModel):
    """Immutable serialized context: no labels, approval or generator metadata."""
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    context_json: str

    @property
    def request_sha256(self):
        return hashlib.sha256(self.context_json.encode()).hexdigest()


class RelevanceVerdict(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)
    request_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    answers_question: bool
    uncertain: bool
    reason: str = Field(min_length=1, max_length=1000)

    @field_validator("reason")
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError("A bounded assessment reason is required.")
        return value


class ScriptedRelevanceAssessor(Protocol):
    execution_source: Literal["unit_test"]

    def assess(self, *, request: RelevanceRequest) -> RelevanceVerdict:
        ...


class RelevanceAssessmentFailure(Exception):
    def __init__(self, reason):
        if reason not in {"unavailable", "refused", "timeout"}:
            raise ValueError("Unknown relevance failure.")
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class GuardedPresentation:
    """Serialized snapshot avoids mutable nested model state after approval.

    This only represents an offline display sample. It cannot publish an answer.
    Each call returns fresh dicts; callers cannot mutate the stored snapshot.
    """
    report_json: str
    preview_allowed: bool
    rejection_reasons: tuple[str, ...]
    execution_source: str = field(default="unit_test", init=False)
    empirical_acceptance: bool = field(default=False, init=False)
    release_authorized: bool = field(default=False, init=False)
    production_enabled: bool = field(default=False, init=False)

    def to_component_report(self):
        return json.loads(self.report_json)


def _snapshot(evaluation):
    if type(evaluation) is not OfflineAnswerEvaluation:
        raise ValueError("Only existing offline evaluations are accepted.")
    if evaluation.execution_source != "unit_test" or evaluation.empirical_acceptance is not False:
        raise ValueError("Non-scripted fixture metadata is invalid.")
    public = GovernedAnswer.model_validate(evaluation.public_response.model_dump(warnings="error"), strict=True)
    if public.answer_text is not None or public.claims or public.validation.release_status != "disabled":
        raise ValueError("Public answer must remain disabled.")
    if evaluation.fixture_claim is None:
        if evaluation.fixture_text is not None:
            raise ValueError("Text without a validated fixture claim is invalid.")
        return public, None, None, None
    if public.outcome != "disabled" or public.validation.coverage_status != "passed" or public.validation.citation_status != "passed":
        raise ValueError("Claim preview requires complete original fixture gates.")
    claim = AnswerClaim.model_validate(evaluation.fixture_claim.model_dump(warnings="error"), strict=True)
    premise_ids = [p.premise_id for p in public.premises]
    if public.scope is None or len(premise_ids) != len(set(premise_ids)) or set(claim.premise_ids) != set(premise_ids):
        raise ValueError("Complete explicit scope and premise coverage are required.")
    references = sorted((r.source_premise_id, r.target_premise_id, r.kind.value)
                        for r in claim.relationship_references)
    relationships = sorted((r.source_premise_id, r.target_premise_id, r.kind.value)
                           for r in public.relationships)
    if references != relationships:
        raise ValueError("Claim relationship references changed.")
    inputs = {"question": public.question, "scope": public.scope.model_dump() if public.scope else None,
              "evidence": [e.model_dump() for e in public.evidence],
              "premises": [p.model_dump() for p in public.premises],
              "relationships": [r.model_dump(mode="json") for r in public.relationships]}
    text = render_fixture(claim, public.evidence, inputs=inputs)
    if evaluation.fixture_text != text:
        raise ValueError("Fixture text changed after validation.")
    context = {"question": public.question, "snapshot_id": public.snapshot_id,
               "scope": inputs["scope"], "candidate": {
                   "statement": claim.statement, "qualifications": claim.qualifications,
                   "premise_ids": claim.premise_ids, "evidence_ids": claim.evidence_ids,
                   "relationship_references": [r.model_dump(mode="json") for r in claim.relationship_references]},
               "evidence": inputs["evidence"], "premises": inputs["premises"],
               "relationships": inputs["relationships"]}
    return public, claim, text, RelevanceRequest(context_json=_canonical(context))


def guard_fixture(evaluation, *, assessor: ScriptedRelevanceAssessor | None = None):
    """Validate exact fixture and require separately injected scripted relevance.

    No provider/client construction, network, credentials, generation, inference,
    routes or runtime enablement. Scripted verdicts do not prove real relevance.
    """
    def result(public=None, claim=None, text=None, reasons=(), request=None, verdict=None):
        allowed = claim is not None and not reasons
        if public is not None and reasons and evaluation.fixture_claim is not None:
            data = public.model_dump()
            data["outcome"] = "blocked_validation"
            data["validation"]["rejection_reasons"] = tuple(
                dict.fromkeys((*public.validation.rejection_reasons, *reasons)))
            public = GovernedAnswer.model_validate(data, strict=True)
        payload = {"execution_source": "unit_test", "empirical_acceptance": False,
                   "public_response": public.model_dump(mode="json") if public else None,
                   "fixture_claim": claim.model_dump(mode="json") if allowed else None,
                   "fixture_text": text if allowed else None,
                   "presentation_guard": {
                       "schema_version": "21-E-offline-presentation-v1",
                       "status": "allowed_offline_fixture" if allowed else "withheld",
                       "rejection_reasons": list(reasons),
                       "request_sha256": request.request_sha256 if request else None,
                       "relevance_verdict": verdict.model_dump() if verdict else None,
                       "release_authorized": False, "production_enabled": False,
                       "semantic_grounding_verified": False,
                       "proposition_to_inference": "closed"}}
        return GuardedPresentation(report_json=_canonical(payload), preview_allowed=allowed,
                                   rejection_reasons=tuple(reasons))
    try:
        public, claim, text, request = _snapshot(evaluation)
    except Exception:
        return result(reasons=("invalid_fixture_snapshot",))
    if claim is None:
        return result(public=public, reasons=("no_admissible_fixture_claim",))
    if assessor is None:
        return result(public, reasons=("relevance_assessment_missing",), request=request)
    try:
        if getattr(assessor, "execution_source", None) != "unit_test":
            return result(public, reasons=("relevance_assessor_not_scripted",), request=request)
        untrusted = assessor.assess(request=request.model_copy(deep=True))
        if type(untrusted) is not RelevanceVerdict:
            return result(public, reasons=("relevance_assessment_malformed",), request=request)
        verdict = RelevanceVerdict.model_validate(untrusted.model_dump(warnings="error"), strict=True)
    except RelevanceAssessmentFailure as exc:
        reason = "relevance_assessment_" + exc.reason if exc.reason in {"unavailable", "refused", "timeout"} else "relevance_assessment_failure"
        return result(public, reasons=(reason,), request=request)
    except Exception:
        return result(public, reasons=("relevance_assessment_failure",), request=request)
    if verdict.request_sha256 != request.request_sha256:
        return result(public, reasons=("relevance_assessment_unbound",), request=request)
    try:
        _, _, _, current = _snapshot(evaluation)
        if current != request:
            raise ValueError("Snapshot changed while relevance was assessed.")
    except Exception:
        return result(public, reasons=("fixture_changed_during_relevance_assessment",), request=request)
    if verdict.uncertain:
        return result(public, reasons=("relevance_assessment_uncertain",), request=request, verdict=verdict)
    if not verdict.answers_question:
        return result(public, reasons=("fixture_question_not_answered",), request=request, verdict=verdict)
    return result(public, claim, text, request=request, verdict=verdict)
