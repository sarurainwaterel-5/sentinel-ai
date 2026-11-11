"""Synthetic principal-to-scope composition; no authentication or runtime wiring.

The sole authority source is an explicitly scripted principal resolution. Reads
recheck its bound policy; observed denial is terminal for this request. These
serial observations are not a transactional publication barrier.
"""
import asyncio
import hashlib
import json
import math
import time

from .identity_resolution import OfflinePrincipalResolver, PrincipalRecord
from .provider_budget_guard import BudgetedPresentation, OfflineBudgetLimits, _canonical
from .scope_catalog_contracts import AuthoritySnapshot, EvidenceScope, ScriptedIdentity, _json
from .scoped_async_coordinator import OfflineScopedAsyncCoordinator


class _PrincipalAuthorityReader:
    execution_source = "unit_test"

    def __init__(self, *, snapshot, identity, checkpoint):
        self._snapshot, self._identity, self._checkpoint = snapshot, identity, checkpoint

    def read(self, *, identity):
        self._checkpoint()
        if type(identity) is not ScriptedIdentity or identity != self._identity:
            raise ValueError("principal_identity_unbound")
        snapshot = AuthoritySnapshot.model_validate_json(self._snapshot, strict=True)
        self._checkpoint()
        return snapshot


class OfflinePrincipalScopedCoordinator:
    """Resolve once, derive exact grants, and compose the offline scoped pipeline.

    One outer observational deadline covers identity and pipeline work. Providers,
    readers and verifier are trusted injected unit-test capabilities. No caller
    supplied identity or document metadata can supply authority. Every invocation
    creates an independent single-attempt resolver, with no retry or fallback.
    """
    def __init__(self, *, generation_provider, statement_provider, relevance_provider,
                 principal_reader, verifier, catalog_reader, limits=None, clock=time.monotonic):
        self.providers = (generation_provider, statement_provider, relevance_provider)
        self.principal_reader, self.verifier = principal_reader, verifier
        self.catalog_reader, self.limits, self.clock = catalog_reader, limits, clock

    async def evaluate_fixture(self, *, authorization_values, scope, request_id,
                               question, evidence, relationships):
        reason = None
        resolver = None
        principal = None
        principal_digest = authority_digest = None
        pipeline_result = None

        def deny(failure):
            nonlocal reason
            reason = reason or failure
            raise ValueError("principal_scope_denied")

        def outcome(result=None):
            allowed = reason is None and result is not None and result.preview_allowed
            reasons = (reason,) if reason else (() if allowed else result.rejection_reasons)
            if allowed:
                report = result.to_component_report()
            else:
                # Never retain partial claims, credential input, principal JSON,
                # provider payloads or callback exception details after denial.
                report = {"execution_source": "unit_test", "empirical_acceptance": False,
                    "public_response": None, "fixture_claim": None, "fixture_text": None}
            report["principal_scope_integration"] = {
                "schema_version": "21-N-offline-principal-scoped-v1",
                "principal_context_sha256": principal_digest,
                "authority_sha256": authority_digest,
                "eligible_fixture": allowed, "rejection_reasons": list(reasons),
                "execution_source": "unit_test", "authenticated_scope_verified": False,
                "semantic_grounding_verified": False, "production_enabled": False,
                "release_authorized": False, "proposition_to_inference": "closed"}
            return BudgetedPresentation(_canonical(report), allowed, tuple(reasons))

        try:
            clock = self.clock
            last = None

            def now():
                nonlocal last
                value = clock()
                if (isinstance(value, bool) or not isinstance(value, (int, float))
                        or not math.isfinite(value) or value < 0
                        or (last is not None and value < last)):
                    deny("principal_scope_clock_invalid")
                last = value
                return value

            started = now()
            limits = OfflineBudgetLimits() if self.limits is None else OfflineBudgetLimits.model_validate_json(self.limits.model_dump_json(), strict=True)
            providers = tuple(self.providers)
            capabilities = (self.principal_reader, self.verifier, self.catalog_reader,
                            self.clock, self.limits)
            if type(scope) is not EvidenceScope:
                deny("identity_scope_invalid")
            bound_scope = EvidenceScope.model_validate_json(scope.model_dump_json(), strict=True)
            scope_binding = bound_scope.model_dump_json()

            def remaining():
                value = limits.request_timeout_seconds - (now() - started)
                if value <= 0:
                    deny("request_expired")
                return value

            def inputs_bound():
                current = (self.principal_reader, self.verifier, self.catalog_reader,
                           self.clock, self.limits)
                if (any(a is not b for a, b in zip(capabilities, current))
                        or len(self.providers) != len(providers)
                        or any(a is not b for a, b in zip(providers, self.providers))
                        or scope.model_dump_json() != scope_binding):
                    deny("principal_scope_inputs_or_capabilities_changed")

            resolver = OfflinePrincipalResolver(principal_reader=capabilities[0],
                verifier=capabilities[1], timeout_seconds=remaining(), clock=now)
            resolved = resolver.resolve(authorization_values=authorization_values,
                requested_scope=bound_scope, request_id=request_id)
            if not resolved.verified_fixture:
                deny(resolved.reason)
            principal = resolved.principal
            inputs_bound()
            remaining()
            context = json.loads(principal.context_json)
            if (context["schema_version"] != "21-I-offline-principal-v1"
                    or context["request_id"] != request_id
                    or context["requested_scope"] != bound_scope.model_dump(mode="json")
                    or hashlib.sha256(principal.context_json.encode()).hexdigest() != principal.context_sha256):
                deny("principal_context_unbound")
            record = PrincipalRecord.model_validate_json(_json(context["principal"]), strict=True)
            if not record.enabled or bound_scope not in record.grants:
                deny("principal_scope_denied")
            identity = ScriptedIdentity(principal_id=record.principal_id)
            authority = AuthoritySnapshot(principal_id=record.principal_id,
                permission_epoch=record.permission_epoch, grants=record.grants)
            principal_digest = principal.context_sha256
            authority_json = authority.model_dump_json()
            authority_digest = hashlib.sha256(_json(authority.model_dump(mode="json")).encode()).hexdigest()

            def checkpoint():
                if reason:
                    deny(reason)
                inputs_bound()
                remaining()
                checked = resolver.recheck(principal)
                if not checked.verified_fixture:
                    deny(checked.reason)
                inputs_bound()
                remaining()

            authority_reader = _PrincipalAuthorityReader(snapshot=authority_json,
                identity=identity, checkpoint=checkpoint)
            checkpoint()
            engine = OfflineScopedAsyncCoordinator(generation_provider=providers[0],
                statement_provider=providers[1], relevance_provider=providers[2],
                authority_reader=authority_reader, catalog_reader=capabilities[2],
                limits=limits.model_copy(update={"request_timeout_seconds": remaining()}), clock=now)
            pipeline_result = await engine.evaluate_fixture(identity=identity, scope=bound_scope,
                request_id=request_id, question=question, evidence=evidence, relationships=relationships)
            checkpoint()
            return outcome(pipeline_result)
        except asyncio.CancelledError:
            if resolver is not None:
                resolver._deny("request_cancelled")
            raise
        except Exception:
            reason = reason or "offline_principal_scope_integration_failure"
            return outcome(pipeline_result)
