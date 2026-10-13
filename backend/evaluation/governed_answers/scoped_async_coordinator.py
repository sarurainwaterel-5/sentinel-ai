"""Offline scope/catalog contracts composed with the existing async pipeline.

No real identity, storage, retrieval, publication, clients or production wiring.
"""
import asyncio
import copy
import json
import time

from app.services.cognition.reasoning.answer_models import AnswerScope
from app.services.cognition.reasoning.models import EvidenceSource
from .async_coordinator import OfflineAsyncAnswerCoordinator, _identities
from .evidence_scope_guard import (
    OperatorScopeFixture, CatalogDocumentFixture, CatalogSnapshotFixture,
)
from .provider_budget_guard import (
    BudgetedPresentation, OfflineBudgetLimits, ScriptedProviderFailure, _canonical,
)
from .scope_catalog_contracts import OfflineEligibilityGuard


class _CheckedReader:
    execution_source = "unit_test"
    def __init__(self, snapshot, checkpoint):
        self.snapshot, self.checkpoint = snapshot, checkpoint

    def read(self):
        self.checkpoint()
        return self.snapshot


class _CheckedProvider:
    execution_source = "unit_test"
    def __init__(self, provider, checkpoint):
        self.provider, self.checkpoint = provider, checkpoint

    @property
    def client(self):
        client = getattr(self.provider, "client", None)
        return self.provider if client is None else client

    async def call(self, *, request):
        self.checkpoint()
        result = await self.provider.call(request=request)
        self.checkpoint()
        return result


class OfflineScopedAsyncCoordinator:
    """Capture once, check around each await and before returning exact fixtures.

    Bridge readers expose only captured scripted fixtures and recheck the actual
    injected contract readers on every read. They never wrap real authenticated
    stores or upgrade the output's authority. One outer deadline starts at entry.
    """
    def __init__(self, *, generation_provider, statement_provider, relevance_provider,
                 authority_reader, catalog_reader, limits=None, clock=time.monotonic):
        self.providers = (generation_provider, statement_provider, relevance_provider)
        self.authority_reader, self.catalog_reader = authority_reader, catalog_reader
        self.limits, self.clock = limits, clock

    async def evaluate_fixture(self, *, identity, scope, request_id, question, evidence, relationships):
        context = None
        reason = None
        guard = None
        pipeline_result = None

        def outcome(result=None, failure=None):
            if failure or result is None or not result.preview_allowed:
                report = {"execution_source": "unit_test", "empirical_acceptance": False,
                    "public_response": None, "fixture_claim": None, "fixture_text": None}
                if result is not None:
                    prior = result.to_component_report()
                    for key in ("async_coordinator", "provider_budget_guard"):
                        if key in prior:
                            report[key] = prior[key]
                reasons = (failure,) if failure else result.rejection_reasons
                allowed = False
            else:
                report, reasons, allowed = result.to_component_report(), (), True
            report["scope_catalog_integration"] = {
                "schema_version": "21-H-offline-scoped-async-v1",
                "context_sha256": context.context_sha256 if context else None,
                "eligible_fixture": allowed, "rejection_reasons": list(reasons),
                "authenticated_scope_verified": False, "semantic_grounding_verified": False,
                "production_enabled": False, "release_authorized": False,
                "proposition_to_inference": "closed"}
            return BudgetedPresentation(_canonical(report), allowed, tuple(reasons))

        try:
            limits = OfflineBudgetLimits() if self.limits is None else OfflineBudgetLimits.model_validate_json(self.limits.model_dump_json(), strict=True)
            guard = OfflineEligibilityGuard(authority_reader=self.authority_reader,
                catalog_reader=self.catalog_reader, timeout_seconds=limits.request_timeout_seconds, clock=self.clock)
            providers = tuple(self.providers)
            identities = _identities(providers)
            captured_relationships = copy.deepcopy(relationships)
            def relationship_json():
                return _canonical([r.model_dump(mode="json") for r in relationships])
            relationship_binding = relationship_json()
            captured = guard.capture(identity=identity, scope=scope, request_id=request_id,
                                     question=question, evidence=evidence)
            if not captured.eligible_fixture:
                return outcome(failure=captured.reason)
            context = captured.context
            data = json.loads(context.context_json)

            def checkpoint():
                nonlocal reason
                checked = guard.recheck(context)
                if not checked.eligible_fixture:
                    reason = reason or checked.reason
                    raise ScriptedProviderFailure("unavailable")
                current = _identities(providers)
                if any(len(a) != len(b) or any(x is not y for x, y in zip(a, b)) for a, b in zip(identities, current)) or relationship_json() != relationship_binding:
                    reason = reason or "integration_inputs_or_provider_changed"
                    guard._deny(reason)
                    raise ScriptedProviderFailure("unavailable")

            bound_scope = data["scope"]
            sources = [EvidenceSource(document_id=c["document_id"], file_hash=c["file_sha256"],
                chunk_index=c["chunk_index"], text=c["text"], status="indexed", **bound_scope)
                for c in data["evidence"]]
            selected = {source.document_id for source in sources}
            documents = tuple(CatalogDocumentFixture(document_id=d["document_id"],
                status="indexed", file_hash=d["file_sha256"], version_epoch=d["lifecycle_epoch"],
                chunk_hashes=tuple(d["chunk_hashes"]), **bound_scope)
                for d in data["catalog"]["documents"] if d["document_id"] in selected)
            authority = OperatorScopeFixture(operator_id=data["identity"]["principal_id"],
                organization_id=bound_scope["organization_id"], collection=bound_scope["collection"],
                allowed_modules=(bound_scope["module"],), allowed_topics=(bound_scope["topic"],),
                scope_epoch=data["authority"]["permission_epoch"])
            catalog = CatalogSnapshotFixture(revision=data["catalog"]["revision"], documents=documents)
            checkpoint()
            remaining = limits.request_timeout_seconds - (guard._now() - guard.started)
            if remaining <= 0:
                return outcome(failure="request_expired")
            inner_limits = limits.model_copy(update={"request_timeout_seconds": remaining})
            wrapped = [_CheckedProvider(provider, checkpoint) for provider in providers]
            engine = OfflineAsyncAnswerCoordinator(generation_provider=wrapped[0], statement_provider=wrapped[1],
                relevance_provider=wrapped[2], limits=inner_limits, clock=self.clock)
            result = await engine.evaluate_fixture(question=data["question"],
                scope=AnswerScope(organization_id=bound_scope["organization_id"], module=bound_scope["module"],
                                  topic=bound_scope["topic"]), collection=bound_scope["collection"],
                sources=sources, relationships=captured_relationships,
                authority_reader=_CheckedReader(authority, checkpoint), catalog_reader=_CheckedReader(catalog, checkpoint))
            pipeline_result = result
            checkpoint()
            return outcome(result, failure=reason)
        except asyncio.CancelledError:
            if guard is not None:
                guard._deny("request_cancelled")
            raise
        except Exception:
            return outcome(pipeline_result, failure=reason or "offline_scope_integration_failure")
