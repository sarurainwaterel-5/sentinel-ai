"""Separate exact-report fidelity and independent free-form admissibility gates.

Neither establishes source truth or a formal natural-language entailment proof.
"""

import json
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, ValidationError

from app.services.cognition.reasoning.models import CandidateProposition, Premise, PremiseRelationship
from app.services.cognition.reasoning.semantic_admissibility_provider import (
    SemanticAdmissibilityFailure, SemanticAdmissibilityProvider,
    SemanticAdmissibilityRequest, SemanticAdmissibilityResponse,
    SemanticJudgeVerdict, SemanticPremiseText, SemanticRelationshipText,
)


class StatementAdmissibilityResult(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    admissible: bool
    rejection_reasons: tuple[Literal[
        "unrepresented_trusted_premise", "unvalidated_qualifications",
        "unsupported_statement_form", "inadmissible_relationship_kind",
        "unsupported_fact", "certainty_inflation", "causal_overreach",
        "negation_reversal", "fabricated_precision", "conflict_suppression",
        "unsupported_qualification", "insufficient_support",
        "semantic_judge_unavailable", "semantic_judge_refused",
        "semantic_judge_malformed_response", "semantic_judge_failure",
        "semantic_judge_inconsistent_verdict",
    ], ...] = ()
    validation_scope: Literal["verbatim_premise_report", "independent_model_semantic_admissibility"] = "verbatim_premise_report"


class VerbatimPremiseStatementValidator:
    """Accept source-preserving reports; never infer semantic equivalence."""

    @staticmethod
    def render(*, premises: list[Premise], relationships: list[PremiseRelationship]) -> str:
        # JSON quoting preserves boundaries even when premise text includes
        # punctuation, instructions, or text resembling another report entry.
        payload = {
            "premises": [{"premise_id": p.premise_id, "statement": p.statement} for p in premises],
            "assessed_relationships": [{
                "source_premise_id": r.source_premise_id,
                "target_premise_id": r.target_premise_id,
                "kind": r.kind.value,
            } for r in relationships],
        }
        return "Supplied premise report: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

    def validate(
        self, *, candidate: CandidateProposition,
        premises: list[Premise], relationships: list[PremiseRelationship],
    ) -> StatementAdmissibilityResult:
        reasons = []
        if set(candidate.premise_ids) != {p.premise_id for p in premises}:
            reasons.append("unrepresented_trusted_premise")
        if candidate.qualifications:
            reasons.append("unvalidated_qualifications")
        if candidate.statement != self.render(premises=premises, relationships=relationships):
            reasons.append("unsupported_statement_form")
        return StatementAdmissibilityResult(admissible=not reasons, rejection_reasons=tuple(reasons))


class StatementAdmissibilityValidator(Protocol):
    def validate(self, *, candidate: CandidateProposition, premises: list[Premise],
                 relationships: list[PremiseRelationship]) -> StatementAdmissibilityResult:
        ...


class FreeFormStatementAdmissibilityValidator:
    """Govern independent model assessment; this is not an entailment proof.

    The provider must be configured independently from generation by the caller.
    We exclude every piece of generator metadata and require a complete,
    internally consistent bounded verdict. Uncertain judgments must reject.
    """
    scope = "independent_model_semantic_admissibility"

    def __init__(self, *, provider: SemanticAdmissibilityProvider):
        self.provider = provider

    def validate(self, *, candidate: CandidateProposition, premises: list[Premise],
                 relationships: list[PremiseRelationship]) -> StatementAdmissibilityResult:
        def result(*reasons):
            return StatementAdmissibilityResult(
                admissible=not reasons, rejection_reasons=tuple(reasons),
                validation_scope=self.scope,
            )

        # Do not let a subset hide an assessed conflicting premise. Structural
        # membership/provenance remains the structural validator's responsibility.
        if set(candidate.premise_ids) != {p.premise_id for p in premises}:
            return result("unrepresented_trusted_premise")
        if any(r.kind.value in {"independent", "unresolved"} for r in relationships):
            return result("inadmissible_relationship_kind")
        request = SemanticAdmissibilityRequest(
            statement=candidate.statement, qualifications=tuple(candidate.qualifications),
            premises=tuple(SemanticPremiseText(premise_id=p.premise_id, statement=p.statement)
                           for p in premises),
            relationships=tuple(SemanticRelationshipText(
                source_premise_id=r.source_premise_id, target_premise_id=r.target_premise_id,
                kind=r.kind.value, basis=r.basis) for r in relationships),
        )
        try:
            response = self.provider.assess(request=request.model_copy(deep=True))
            if not isinstance(response, SemanticAdmissibilityResponse):
                return result("semantic_judge_malformed_response")
            verdict = SemanticJudgeVerdict.model_validate_json(response.content, strict=True)
        except SemanticAdmissibilityFailure as error:
            return result(f"semantic_judge_{error.reason}")
        except ValidationError:
            return result("semantic_judge_malformed_response")
        except Exception:
            return result("semantic_judge_failure")
        checks = tuple(name for name in SemanticJudgeVerdict.model_fields
                       if name not in {"admissible", "rejection_reasons"} and getattr(verdict, name))
        # Reject contradictory approvals, missing reasons, or unsupported reasons.
        if (verdict.admissible != (not checks)
                or set(verdict.rejection_reasons) != set(checks)
                or len(verdict.rejection_reasons) != len(set(verdict.rejection_reasons))):
            return result("semantic_judge_inconsistent_verdict")
        return result(*checks)
