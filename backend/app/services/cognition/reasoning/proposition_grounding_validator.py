"""Deterministic reference and provenance gate for untrusted propositions.

Passing this gate does not establish semantic entailment of the statement.
Only a separate statement-level grounding check may authorize promotion.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.services.cognition.reasoning.models import (
    CandidateProposition,
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
)


class PropositionGroundingValidationResult(BaseModel):
    """Inspectable structural decision with provenance derived from trusted inputs."""

    model_config = ConfigDict(frozen=True)

    structurally_valid: bool
    rejection_reasons: tuple[str, ...] = ()
    premise_ids: tuple[str, ...] = ()
    evidence_ids: tuple[str, ...] = ()
    domain_ids: tuple[str, ...] = ()
    relationships: tuple[PremiseRelationship, ...] = ()
    semantic_grounding_verified: Literal[False] = False


class PropositionGroundingValidator:
    """Reconcile candidate claims with Sentinel's assessed reasoning artifacts."""

    def validate(
        self,
        *,
        candidate: CandidateProposition,
        premises: list[Premise],
        relationships: list[PremiseRelationship],
    ) -> PropositionGroundingValidationResult:
        reasons: list[str] = []

        def reject(reason: str) -> None:
            if reason not in reasons:
                reasons.append(reason)

        if not candidate.statement.strip():
            reject("blank_candidate_statement")

        premise_by_id: dict[str, Premise] = {}
        for premise in premises:
            previous = premise_by_id.setdefault(premise.premise_id, premise)
            if previous != premise:
                reject("ambiguous_trusted_premise")

        candidate_ids = list(dict.fromkeys(candidate.premise_ids))
        if len(candidate_ids) < 2:
            reject("insufficient_distinct_premises")
        for premise_id in candidate_ids:
            premise = premise_by_id.get(premise_id)
            if premise is None:
                reject("unknown_premise_reference")
            elif not premise.evidence_ids or any(
                not evidence_id.strip() for evidence_id in premise.evidence_ids
            ):
                reject("missing_evidence_lineage")

        trusted_by_pair: dict[tuple[str, str], PremiseRelationship] = {}
        for relationship in relationships:
            pair = (relationship.source_premise_id, relationship.target_premise_id)
            previous = trusted_by_pair.setdefault(pair, relationship)
            if previous != relationship:
                reject("ambiguous_trusted_relationship")

        if not candidate.relationship_references:
            reject("missing_relationship_reference")

        selected: list[PremiseRelationship] = []
        selected_pairs: set[tuple[str, str]] = set()
        covered_ids: set[str] = set()
        for reference in candidate.relationship_references:
            pair = (reference.source_premise_id, reference.target_premise_id)
            if not set(pair).issubset(candidate_ids):
                reject("relationship_outside_candidate_premises")
            relationship = trusted_by_pair.get(pair)
            if relationship is None:
                reject("unknown_or_reversed_relationship")
                continue
            if relationship.kind != reference.kind:
                reject("relationship_kind_mismatch")
                continue
            if relationship.kind in {
                PremiseRelationshipKind.INDEPENDENT,
                PremiseRelationshipKind.UNRESOLVED,
            }:
                reject("inadmissible_relationship_kind")
                continue
            if pair not in selected_pairs:
                selected_pairs.add(pair)
                selected.append(relationship)
            covered_ids.update(pair)

        if set(candidate_ids) != covered_ids:
            reject("unconnected_premise_reference")

        # Every assessed conflict among the participating premises must be
        # acknowledged, including a conflict in the opposite direction.
        for pair, relationship in trusted_by_pair.items():
            if (
                relationship.kind == PremiseRelationshipKind.CONFLICTS
                and set(pair).issubset(candidate_ids)
                and pair not in selected_pairs
            ):
                reject("suppressed_conflict")

        if reasons:
            return PropositionGroundingValidationResult(
                structurally_valid=False,
                rejection_reasons=tuple(reasons),
            )

        participating = [premise_by_id[premise_id] for premise_id in candidate_ids]
        return PropositionGroundingValidationResult(
            structurally_valid=True,
            premise_ids=tuple(candidate_ids),
            evidence_ids=tuple(dict.fromkeys(
                evidence_id
                for premise in participating
                for evidence_id in premise.evidence_ids
            )),
            domain_ids=tuple(dict.fromkeys(
                domain_id
                for premise in participating
                for domain_id in premise.domain_ids
            )),
            relationships=tuple(selected),
        )
