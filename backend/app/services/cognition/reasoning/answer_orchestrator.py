"""Offline Sprint 21 coordinator; intentionally has no production composition.

Caller supplies synthetic evidence and assessed fixture relationships. It never
retrieves, creates clients, registers routes, invokes inference or releases answers.
"""
import hashlib
import json
from dataclasses import dataclass, field
from itertools import combinations
from app.services.cognition.reasoning.answer_models import (
    AnswerClaim, AnswerScope, AnswerValidation, ClaimValidation, GovernedAnswer,
)
from app.services.cognition.reasoning.answer_provenance import build_registry
from app.services.cognition.reasoning.answer_renderer import claim_digest, render_fixture
from app.services.cognition.reasoning.models import (
    CandidateProposition, CandidateRelationshipReference, EvidenceBundle, EvidenceDisposition, EvidenceItem,
    EvidenceSource, PremiseRelationship, PremiseRelationshipKind,
)
from app.services.cognition.reasoning.premise_extractor import PremiseExtractor
from app.services.cognition.reasoning.proposition_synthesizer import PropositionSynthesizer
from app.services.cognition.reasoning.statement_admissibility_validator import FreeFormStatementAdmissibilityValidator


@dataclass(frozen=True)
class OfflineAnswerEvaluation:
    public_response: GovernedAnswer
    fixture_claim: AnswerClaim | None = None
    fixture_text: str | None = None
    execution_source: str = field(default="unit_test", init=False)
    empirical_acceptance: bool = field(default=False, init=False)


class OfflineAnswerCoordinator:
    def __init__(self, *, generator, statement_validator):
        # No exact-report/structural compatibility substitute for this pipeline.
        if type(statement_validator) is not FreeFormStatementAdmissibilityValidator:
            raise ValueError("The existing independent free-form gate is required.")
        self.synthesizer = PropositionSynthesizer(
            semantic_generator=generator, statement_validator=statement_validator)
        self.generator = generator

    def evaluate_fixture(self, *, question: str, sources: list[EvidenceSource],
                         catalog: dict[str, dict], scope: AnswerScope,
                         collection: str, snapshot_id: str,
                         relationships: list[PremiseRelationship]) -> OfflineAnswerEvaluation:
        # Validate the public question/scope contract before any injected work.
        GovernedAnswer(question=question, snapshot_id=snapshot_id, scope=scope)
        trace = []
        evidence = ()
        premises = []
        relations = []

        def response(outcome, reasons=(), coverage="not_run", citations="not_run", claim=None, text=None):
            conflicts = tuple(r.basis for r in relations if r.kind == PremiseRelationshipKind.CONFLICTS)
            unresolved = tuple(r for r in relations if r.kind in {
                PremiseRelationshipKind.UNRESOLVED, PremiseRelationshipKind.INDEPENDENT})
            return OfflineAnswerEvaluation(public_response=GovernedAnswer(
                question=question, snapshot_id=snapshot_id, scope=scope, outcome=outcome,
                evidence=evidence, premises=tuple(p.model_copy(deep=True) for p in premises),
                relationships=tuple(r.model_copy(deep=True) for r in relations),
                conflicts=conflicts, unresolved_relationships=unresolved,
                uncertainty=("Offline fixture verdicts do not establish semantic accuracy or source truth.",),
                operational_trace=tuple(trace), validation=AnswerValidation(
                    coverage_status=coverage, citation_status=citations,
                    rejection_reasons=tuple(reasons))), fixture_claim=claim, fixture_text=text)

        if len(sources) > scope.limit:
            return response("blocked_provenance", ("retrieval_budget_exceeded",), "rejected")
        try:
            registry = build_registry(sources=sources, catalog=catalog, snapshot_id=snapshot_id,
                organization_id=scope.organization_id, collection=collection,
                module=scope.module, topic=scope.topic)
        except Exception:
            return response("blocked_provenance", ("provenance_validation_failure",), "rejected")
        evidence = registry.evidence
        trace.append("Validated fixture source snapshot.")
        if registry.rejection_reasons:
            return response("blocked_provenance", registry.rejection_reasons, "rejected")
        if not evidence:
            return response("insufficient_evidence", ("no_usable_evidence",), "rejected")
        items = [EvidenceItem(statement=e.text, disposition=EvidenceDisposition.CONTEXTUAL,
            source=EvidenceSource(**{**e.model_dump(exclude={"evidence_id", "snapshot_id", "text_sha256"}),
                "metadata": {"evidence_id": e.evidence_id}})) for e in evidence]
        premises = PremiseExtractor().extract(EvidenceBundle(question=question, contextual=items))
        trace.append("Extracted complete fixture premises without classifying source truth.")
        ids = {p.premise_id for p in premises}
        if len(ids) < 2:
            return response("blocked_relationships", ("insufficient_distinct_premises",), "rejected")
        if {i for p in premises for i in p.evidence_ids} != {e.evidence_id for e in evidence}:
            return response("blocked_provenance", ("incomplete_evidence_coverage",), "rejected")
        if len(relationships) > 300:
            return response("blocked_relationships", ("relationship_budget_exceeded",), "rejected")
        try:
            relations = [PremiseRelationship.model_validate(r.model_dump(), strict=True) for r in relationships]
        except Exception:
            return response("blocked_relationships", ("invalid_relationship_fixture",), "rejected")
        pairs = [frozenset((r.source_premise_id, r.target_premise_id)) for r in relations]
        expected = {frozenset(pair) for pair in combinations(ids, 2)}
        if len(pairs) != len(set(pairs)) or set(pairs) != expected:
            return response("blocked_relationships", ("incomplete_or_ambiguous_relationship_coverage",), "rejected")
        if any(r.confidence < 0.75 or r.kind in {PremiseRelationshipKind.UNRESOLVED, PremiseRelationshipKind.INDEPENDENT} for r in relations):
            return response("blocked_relationships", ("unresolved_relationships",), "rejected")
        trace.append("Checked all fixture premise pairs and preserved assessed conflicts.")
        # Capture the exact untrusted candidate without relying on generator metadata.
        class Capture:
            provider = getattr(self.generator, "provider", self.generator)
            candidate = None
            def generate(inner, **kwargs):
                generated = self.generator.generate(**kwargs)
                if not isinstance(generated, CandidateProposition):
                    return generated
                inner.candidate = generated.model_copy(deep=True)
                return generated.model_copy(deep=True)
        capture = Capture()
        try:
            synthesis = PropositionSynthesizer(semantic_generator=capture,
                statement_validator=self.synthesizer.statement_validator).synthesize_with_validation(
                    premises=premises, relationships=relations)
        except Exception:
            return response("blocked_validation", ("synthesis_failure",), "passed")
        trace.append("Applied existing structural and independent statement gates to fixture candidate.")
        if not synthesis.propositions:
            reasons = synthesis.rejection_reasons
            outcome = "rejected"
            if any(r.startswith("provider_") or r in {"generator_failure", "malformed_generation", "invalid_candidate"} for r in reasons):
                outcome = "provider_failure"
            elif any(r.startswith("semantic_judge_") or "validator_failure" in r for r in reasons):
                outcome = "blocked_validation"
            return response(outcome, reasons, "passed")
        try:
            candidate = capture.candidate
            proposition = synthesis.propositions[0]
            if candidate.statement.strip() != proposition.statement:
                raise ValueError("Assessed content changed.")
            if synthesis.acceptance_mode != "statement_validated" or len(synthesis.propositions) != 1:
                raise ValueError("Unexpected synthesis outcome.")
            if set(proposition.premise_ids) != ids or set(proposition.evidence_ids) != {e.evidence_id for e in evidence}:
                raise ValueError("Incomplete claim coverage.")
            inputs = {"question": question, "scope": scope.model_dump(),
                "evidence": [e.model_dump() for e in evidence],
                "premises": [p.model_dump() for p in premises],
                "relationships": [r.model_dump(mode="json") for r in relations]}
            digest = hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            claim = AnswerClaim(claim_id="fixture-claim-1", statement=candidate.statement,
                kind="attributed_synthesis", premise_ids=tuple(proposition.premise_ids),
                evidence_ids=tuple(proposition.evidence_ids), qualifications=tuple(candidate.qualifications),
                relationship_references=tuple(CandidateRelationshipReference(
                    source_premise_id=r.source_premise_id, target_premise_id=r.target_premise_id, kind=r.kind) for r in relations),
                validation=ClaimValidation(structural_status="passed", statement_status="admissible",
                    statement_result=synthesis.statement_validation,
                    candidate_sha256=claim_digest(candidate.statement, tuple(candidate.qualifications)),
                    inputs_sha256=digest, policy_version="21-C-offline-existing-gates"))
            text = render_fixture(claim, evidence, inputs=inputs)
        except Exception:
            return response("blocked_validation", ("final_fixture_validation_failure",), "passed", "rejected")
        trace.append("Rendered exact assessed fixture content and citations; production release remains disabled.")
        return response("disabled", (), "passed", "passed", claim, text)
