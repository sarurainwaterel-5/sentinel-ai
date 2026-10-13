"""Governed async composition of scripted offline providers only.

Replay adapters never dispatch work. Frozen synchronous grounding, provenance,
statement and rendering checks remain authoritative. No runtime/client wiring.
"""
import asyncio
import copy
import hashlib
import inspect
import time

from app.services.cognition.reasoning.answer_orchestrator import OfflineAnswerCoordinator
from app.services.cognition.reasoning.semantic_generation_provider import SemanticGenerationResponse
from app.services.cognition.reasoning.semantic_proposition_generator import ProviderSemanticPropositionGenerator
from app.services.cognition.reasoning.semantic_admissibility_provider import (
    SemanticAdmissibilityFailure, SemanticAdmissibilityResponse,
)
from app.services.cognition.reasoning.statement_admissibility_validator import FreeFormStatementAdmissibilityValidator
from .evidence_scope_guard import evaluate_scoped_fixture
from .presentation_guard import GuardedPresentation, RelevanceVerdict, _snapshot
from .provider_budget_guard import (
    BudgetedPresentation, OfflineProviderBudget, _canonical,
)


def _generation_request(premises, relationships):
    return _canonical({"premises": [p.model_dump(mode="json") for p in premises],
                       "relationships": [r.model_dump(mode="json") for r in relationships]})


class _GenerationCapture:
    request_json = None

    def generate(self, *, premises, relationships):
        self.request_json = _generation_request(premises, relationships)
        return None  # preflight stops before any candidate or assessment


class _GenerationReplay:
    def __init__(self, request_json, response_json):
        self.request_json, self.response_json = request_json, response_json

    def generate(self, *, premises, relationships):
        if _generation_request(premises, relationships) != self.request_json:
            raise ValueError("Generation replay request changed.")
        return SemanticGenerationResponse(content=self.response_json)


class _StatementReplay:
    def __init__(self, request_json=None, response_json=None):
        self.request_json, self.response_json = request_json, response_json
        self.captured_json = None

    def assess(self, *, request):
        current = _canonical(request.model_dump(mode="json"))
        self.captured_json = current
        if self.response_json is None:
            raise SemanticAdmissibilityFailure("unavailable")  # capture only
        if current != self.request_json:
            raise ValueError("Statement replay request changed.")
        return SemanticAdmissibilityResponse(content=self.response_json)


class _RelevanceReplay:
    execution_source = "unit_test"

    def __init__(self, request_json, response_json):
        self.request_json, self.response_json = request_json, response_json

    def assess(self, *, request):
        if request.context_json != self.request_json:
            raise ValueError("Relevance replay request changed.")
        return RelevanceVerdict.model_validate_json(self.response_json, strict=True)


def _engine(generator, statement):
    return OfflineAnswerCoordinator(generator=generator,
        statement_validator=FreeFormStatementAdmissibilityValidator(provider=statement))


def _identities(providers):
    """Explicit scripted objects and exposed clients, never inferred metadata."""
    identities = []
    for provider in providers:
        if (provider is None or getattr(provider, "execution_source", None) != "unit_test"
                or not inspect.iscoroutinefunction(getattr(provider, "call", None))):
            raise ValueError("All roles require explicitly scripted providers.")
        client = getattr(provider, "client", None)
        identities.append((provider,) if client is None else (provider, client))
    for index, role in enumerate(identities):
        for other in identities[index + 1:]:
            if any(left is right for left in role for right in other):
                raise ValueError("Independent provider roles are required.")
    return tuple(identities)


class OfflineAsyncAnswerCoordinator:
    """A fresh budget and immutable context per invocation, sequential dispatch.

    Caller cancellation propagates. Other failures withhold the entire fixture.
    Providers are trusted injected test capabilities, not untrusted sandboxed code.
    Independence checks cover exposed client identity, not concealed credentials.
    """
    def __init__(self, *, generation_provider, statement_provider, relevance_provider,
                 limits=None, clock=time.monotonic):
        self.providers = (generation_provider, statement_provider, relevance_provider)
        self.limits, self.clock = limits, clock

    async def evaluate_fixture(self, *, question, scope, collection, sources,
                               relationships, authority_reader, catalog_reader):
        budget = OfflineProviderBudget(self.limits, clock=self.clock)
        receipts = []

        def finish(presentation=None, reason=None):
            if reason:
                presentation = GuardedPresentation(_canonical({"execution_source": "unit_test",
                    "empirical_acceptance": False, "public_response": None,
                    "fixture_claim": None, "fixture_text": None}), False, (reason,))
            result = budget.guard_presentation(presentation)
            report = result.to_component_report()
            report["async_coordinator"] = {"schema_version": "21-F-offline-async-v1",
                "stage_receipts": receipts, "rejection_reasons": [reason] if reason else list(result.rejection_reasons),
                "execution_source": "unit_test", "empirical_acceptance": False,
                "production_enabled": False, "release_authorized": False,
                "semantic_grounding_verified": False, "proposition_to_inference": "closed"}
            return BudgetedPresentation(_canonical(report), result.preview_allowed,
                (reason,) if reason else result.rejection_reasons)

        try:
            providers = tuple(self.providers)
            identities = _identities(providers)
            original = dict(question=question, scope=scope, collection=collection,
                            sources=sources, relationships=relationships)
            captured = copy.deepcopy(original)

            def inputs_json(args):
                return _canonical({"question": args["question"], "scope": args["scope"].model_dump(mode="json"),
                    "collection": args["collection"],
                    "sources": [s.model_dump(mode="json") for s in args["sources"]],
                    "relationships": [r.model_dump(mode="json") for r in args["relationships"]]})

            input_binding = inputs_json(captured)

            def preflight():
                capture = _GenerationCapture()
                scoped = evaluate_scoped_fixture(**captured, authority_reader=authority_reader,
                    catalog_reader=catalog_reader, coordinator=_engine(capture, _StatementReplay()))
                return capture.request_json, scoped.to_component_report()

            generation_json, baseline = preflight()
            if generation_json is None or not baseline.get("evidence_scope_guard", {}).get("fixture_scope_checked"):
                return finish(reason="async_preflight_rejected")

            def unchanged():
                current_ids = _identities(providers)
                if (len(current_ids) != len(identities) or any(
                    len(a) != len(b) or any(x is not y for x, y in zip(a, b))
                    for a, b in zip(current_ids, identities)) or inputs_json(original) != input_binding):
                    raise ValueError("Inputs or provider identities changed.")
                current_request, current_report = preflight()
                if current_request != generation_json or current_report != baseline:
                    raise ValueError("Scope, catalog or evidence snapshot changed.")

            async def execute(stage, request_json, provider):
                result = await budget.execute(stage=stage, request_json=request_json, provider=provider)
                receipt = result.report()
                receipts.append(receipt)
                if result.status != "completed":
                    return result, result.reason
                expected = hashlib.sha256(request_json.encode()).hexdigest()
                if (receipt.get("stage") != stage or receipt.get("request_sha256") != expected
                        or receipt.get("status") != "completed" or result.response_json is None):
                    return result, "async_receipt_unbound"
                unchanged()
                return result, None

            generation, reason = await execute("generation", generation_json, providers[0])
            if reason:
                return finish(reason=reason)
            generator = ProviderSemanticPropositionGenerator(provider=_GenerationReplay(generation_json, generation.response_json))
            public = baseline["public_response"]
            catalog = {s.document_id: {key: getattr(s, key) for key in (
                "organization_id", "collection", "module", "topic", "status", "file_hash")} for s in captured["sources"]}
            evaluation_args = dict(captured, catalog=catalog, snapshot_id=public["snapshot_id"])
            statement_capture = _StatementReplay()
            _engine(generator, statement_capture).evaluate_fixture(**evaluation_args)
            if statement_capture.captured_json is None:
                return finish(reason="async_structural_rejected")
            statement_json = statement_capture.captured_json
            statement, reason = await execute("statement_assessment", statement_json, providers[1])
            if reason:
                return finish(reason=reason)
            judge = _StatementReplay(statement_json, statement.response_json)
            engine = _engine(generator, judge)
            evaluation = engine.evaluate_fixture(**evaluation_args)
            if evaluation.fixture_claim is None:
                return finish(reason="async_statement_rejected")
            _, _, _, relevance_request = _snapshot(evaluation)
            relevance, reason = await execute("relevance_assessment", relevance_request.context_json, providers[2])
            if reason:
                return finish(reason=reason)
            presentation = evaluate_scoped_fixture(**captured, authority_reader=authority_reader,
                catalog_reader=catalog_reader, coordinator=engine,
                relevance_assessor=_RelevanceReplay(relevance_request.context_json, relevance.response_json))
            unchanged()
            if not presentation.preview_allowed:
                return finish(reason=presentation.rejection_reasons[0]
                    if presentation.rejection_reasons else "async_presentation_withheld")
            return finish(presentation)
        except asyncio.CancelledError:
            raise  # budget owns cancellation/quarantine; never return partial output
        except Exception:
            return finish(reason="async_context_or_composition_failure")
