"""Bounded isolated composition; inspection only, never a publication barrier.

Bindings and retrieved cases are supplied by an explicit trusted rehearsal adapter.
This does not authenticate users or turn legacy retrieval into governed evidence.
"""
import asyncio
import hashlib
import math
from dataclasses import dataclass

from app.services.providers.openai_governed_transport import (
    OpenAIGovernedTransport, GenerationPayload, GovernedTransportFailure, _bounded_json,
)
from app.services.cognition.reasoning.semantic_admissibility_provider import (
    SemanticAdmissibilityRequest, SemanticPremiseText, SemanticRelationshipText,
    SemanticJudgeVerdict,
)
from .live_provider_rehearsal import canonical, consistent, structurally_complete
from .presentation_guard import RelevanceVerdict
from .scope_catalog_contracts import EvidenceScope


@dataclass(frozen=True)
class InspectionResult:
    """Immutable serialized result; denied results contain no candidate or sources."""
    report_json: str

    def to_dict(self):
        return _bounded_json(self.report_json)


class InspectionDenied(Exception):
    pass


async def inspect_runtime(*, transport, retrieve, current_binding, timeout_seconds=90):
    """At most three role calls with one deadline, no retries or partial output.

    current_binding() must synchronously return the current question/context,
    principal/permission/catalog versions and gate evidence digests. Caller owns
    authoritative reads. The callback must be bounded and nonblocking: asyncio
    deadlines cannot preempt synchronous blocking code. Serial checks cannot replace a publication transaction.
    retrieve() supplies one complete synthetic case with the reviewed case shape.
    """
    if type(transport) is not OpenAIGovernedTransport:
        raise ValueError('Explicit real SDK transport required.')
    if (type(timeout_seconds) not in (int, float) or not math.isfinite(timeout_seconds)
            or not 0 < timeout_seconds <= 120):
        raise ValueError('Bounded finite outer deadline required.')
    calls = 0
    base = {'version': 'sprint21-runtime-inspection-v1',
            'execution_source': 'isolated_runtime_composition',
            'transport_execution_source': transport.execution_source,
            'production_enabled': False, 'release_authorized': False,
            'empirical_acceptance': False, 'proposition_to_inference': 'closed',
            'publication_barrier_implemented': False}

    def snapshot():
        value = current_binding()
        if type(value) is not dict or set(value) != {
                'question', 'context_sha256', 'principal_id', 'permission_epoch',
                'catalog_epoch', 'gate_sha256', 'eligible', 'scope', 'credential_epoch'}:
            raise InspectionDenied('invalid_binding')
        if (value['eligible'] is not True or type(value['permission_epoch']) is not int
                or value['permission_epoch'] < 0 or type(value['credential_epoch']) is not int
                or value['credential_epoch'] < 1 or type(value['catalog_epoch']) is not int
                or value['catalog_epoch'] < 0):
            raise InspectionDenied('ineligible_binding')
        for key in ('question', 'principal_id'):
            if type(value[key]) is not str or not value[key].strip():
                raise InspectionDenied('invalid_binding')
        for key in ('context_sha256', 'gate_sha256'):
            if (type(value[key]) is not str or len(value[key]) != 64
                    or any(c not in '0123456789abcdef' for c in value[key])):
                raise InspectionDenied('invalid_binding')
        EvidenceScope.model_validate(value['scope'], strict=True)
        encoded = canonical(value)
        if len(encoded.encode()) > 16384:
            raise InspectionDenied('binding_budget')
        return encoded

    def configuration_snapshot():
        # Nonsecret settings only: never serialize clients or credentials.
        return canonical({'roles': {role: {'model': config.model,
            'reasoning_effort': config.reasoning_effort,
            'sdk_retries': config.client.max_retries}
            for role, config in transport._roles.items()},
            'timeout_seconds': transport.timeout, 'max_input_bytes': transport.max_input_bytes,
            'max_output_bytes': transport.max_output_bytes,
            'max_output_tokens': transport.max_output_tokens})

    async def body():
        nonlocal calls
        initial = snapshot()
        configuration = configuration_snapshot()
        requests = {}

        def guard():
            if configuration_snapshot() != configuration:
                raise InspectionDenied('configuration_changed')
            if snapshot() != initial:
                raise InspectionDenied('binding_changed')

        guard()
        case = await retrieve()
        guard()
        # Snapshot prevents downstream mutation by the retrieval adapter.
        encoded = canonical(case)
        if len(encoded.encode()) > 60000:
            raise InspectionDenied('context_budget')
        case = _bounded_json(encoded)
        binding = _bounded_json(initial)
        context = {key: case[key] for key in ('question', 'sources', 'premises', 'relationships')}
        if (case['question'] != binding['question']
                or hashlib.sha256(canonical(context).encode()).hexdigest() != binding['context_sha256']):
            raise InspectionDenied('context_mismatch')

        if (type(context['sources']) is not list or not context['sources']
                or type(context['premises']) is not list or len(context['premises']) < 2
                or any(type(p.get('evidence_ids')) is not list or not p['evidence_ids']
                       for p in context['premises'])):
            raise InspectionDenied('missing_source_support')

        async def dispatch(role, payload):
            nonlocal calls
            guard()
            if calls >= 3:
                raise InspectionDenied('call_budget')
            calls += 1
            request_json = canonical(payload)
            requests[role] = hashlib.sha256(request_json.encode()).hexdigest()
            raw = await transport.call(role=role, request_json=request_json)
            guard()
            return raw

        candidate = GenerationPayload.model_validate_json(await dispatch('generation', context), strict=True)
        if not structurally_complete(candidate, case):
            raise InspectionDenied('structure_rejected')
        request = SemanticAdmissibilityRequest(statement=candidate.statement,
            qualifications=tuple(candidate.qualifications),
            premises=tuple(SemanticPremiseText(premise_id=p['premise_id'], statement=p['statement']) for p in case['premises']),
            relationships=tuple(SemanticRelationshipText(**{k:r[k] for k in SemanticRelationshipText.model_fields}) for r in case['relationships']))
        verdict = SemanticJudgeVerdict.model_validate_json(await dispatch('statement', request.model_dump(mode='json')), strict=True)
        if not consistent(verdict) or not verdict.admissible:
            raise InspectionDenied('statement_rejected')
        relevance_context = dict(context, candidate=candidate.model_dump(mode='json'))
        relevance = RelevanceVerdict.model_validate_json(await dispatch('relevance', relevance_context), strict=True)
        expected = hashlib.sha256(canonical(relevance_context).encode()).hexdigest()
        if relevance.request_sha256 != expected or not relevance.answers_question or relevance.uncertain:
            raise InspectionDenied('relevance_rejected')
        guard()
        # No await between final guard and immutable inspection snapshot.
        return dict(base, status='inspection_only', preview_allowed=True,
                    binding=_bounded_json(initial), context=context,
                    candidate=candidate.model_dump(mode='json'),
                    context_sha256=binding['context_sha256'], attempted_calls=calls,
                    configuration=_bounded_json(configuration), request_sha256=requests,
                    statement_assessment=verdict.model_dump(mode='json'),
                    relevance_assessment=relevance.model_dump(mode='json'))

    try:
        async with asyncio.timeout(timeout_seconds):
            result = await body()
    except asyncio.CancelledError:
        raise
    except TimeoutError:
        result = dict(base, status='withheld', preview_allowed=False, reason='timeout', attempted_calls=calls)
    except InspectionDenied as exc:
        result = dict(base, status='withheld', preview_allowed=False, reason=str(exc), attempted_calls=calls)
    except GovernedTransportFailure as exc:
        result = dict(base, status='withheld', preview_allowed=False, reason=exc.reason, attempted_calls=calls)
    except Exception:
        result = dict(base, status='withheld', preview_allowed=False, reason='invalid_adapter_or_response', attempted_calls=calls)
    return InspectionResult(canonical(result))
