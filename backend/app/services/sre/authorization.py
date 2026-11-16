"""Explicit server policy maps existing authenticated scopes to SRE boundaries."""
from dataclasses import dataclass
from app.services.governed_authentication import GovernedAuthenticationSession, AuthenticatedGovernedPrincipal
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from .contracts import identifier, SREError

ACTIONS=frozenset({'read','configure','ingest','validate','incident'})

@dataclass(frozen=True)
class Grant:
    principal_id: str
    evidence_scope: EvidenceScope
    tenant_id: str
    application_id: str
    actions: frozenset

@dataclass(frozen=True)
class Access:
    session: GovernedAuthenticationSession
    principal: AuthenticatedGovernedPrincipal

class SREAuthorizer:
    """Construct from trusted local composition only, never posted configuration.

    No credential lookup, defaults, global scope or supervisor bypass is added.
    Existing session's exact issued handle and current epochs are rechecked.
    """
    def __init__(self,catalog,grants=()):
        self._catalog=catalog; checked=[]
        if type(grants) is not tuple or len(grants)>256: raise SREError('INVALID_GRANTS')
        for g in grants:
            if type(g) is not Grant or type(g.evidence_scope) is not EvidenceScope or type(g.actions) is not frozenset or not g.actions or not g.actions<=ACTIONS: raise SREError('INVALID_GRANTS')
            for x in (g.principal_id,g.tenant_id,g.application_id):identifier(x)
            scope=EvidenceScope.model_validate_json(g.evidence_scope.model_dump_json(),strict=True)
            checked.append((g.principal_id,scope.model_dump_json(),g.tenant_id,g.application_id,g.actions))
        self._grants=tuple(checked)

    def check(self,access,tenant,application,action):
        try:
            identifier(tenant);identifier(application)
            if type(access) is not Access or type(access.session) is not GovernedAuthenticationSession or type(access.principal) is not AuthenticatedGovernedPrincipal: raise ValueError()
            if not access.session.bound_to(self._catalog) or not access.session.recheck(access.principal): raise ValueError()
            p=access.principal
            if not any((p.principal_id,p.scope.model_dump_json(),tenant,application)==g[:4] and action in g[4] for g in self._grants): raise ValueError()
            return identifier(p.principal_id)
        except Exception: raise SREError('ACCESS_DENIED') from None
