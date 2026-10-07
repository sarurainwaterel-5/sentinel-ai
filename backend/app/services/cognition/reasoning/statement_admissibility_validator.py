"""Bounded statement validation, not general natural-language entailment.

Only an exact Sentinel-rendered report of all supplied premises and assessed
relationships is admissible. Unknown paraphrases and additional claims fail
closed. This does not establish that the underlying source statements are true.
"""

import json

from pydantic import BaseModel, ConfigDict

from app.services.cognition.reasoning.models import CandidateProposition, Premise, PremiseRelationship


class StatementAdmissibilityResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    admissible: bool
    rejection_reasons: tuple[str, ...] = ()
    validation_scope: str = "verbatim_premise_report"


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
