"""Inspect the approved 21-E review offline; never authorize release.

Content/attestation checks are not identity authentication or semantic evaluation.
Only fixed packet paths are read; no providers, credentials, or runtime imports.
"""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from .inspect_packet import inspect_packet

ROOT = Path(__file__).resolve().parents[3]
FOLDER = "backend/evaluation/governed_answers/"
REVIEW = FOLDER + "answer_review.human.approved.json"
PROVENANCE = FOLDER + "answer_review.rationales.proposed.json"
COMMIT = "81e2a712ce2788054a8c5e218af1d52f098e6811"
# Frozen packet input bytes; caller-supplied hashes cannot redefine this checkpoint.
BINDINGS = {
    FOLDER + "answer_cases.proposed.json": "d5a4391d5108e14894fec3158261d9a91600e5b7b28695138388e29218891ba9",
    FOLDER + "answer_review.template.json": "bd990107f4eb653c4115b2e3eab1011a2f97fee395f967de4b40c33dee01979e",
    FOLDER + "answer_acceptance.proposed.json": "46b7bd1822f29176ee2a907b6e1d733c0efda929757e89428c51c136c3517dd6",
    FOLDER + "release_manifest.json": "14cd952d66c928a3a68e49558bed7c9825b086a9dae2a2c244ee5a1236d1b643",
}
BOOLEANS = ("statement_admissible", "answers_question",
            "preserves_conflicts_and_uncertainty", "citations_complete")
ADOPTED = "assistant_drafted_in_frozen_dataset_personally_verified_and_adopted_by_human"
ORIGINS = {ADOPTED, "verbatim_human_statement_in_referenced_conversation",
           "human_reason_supplied_in_current_request_normalized_not_verbatim_quote"}


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _utc(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", value):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return True
    except ValueError:
        return False


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _load(root, name, errors, expected=None):
    path = root / name
    # Reject symlink escape before reading, including fixed-path symlink attacks.
    if not path.resolve().is_relative_to(root.resolve()):
        errors.append("unsafe_path:" + name)
        return None
    try:
        data = path.read_bytes()
        if expected and hashlib.sha256(data).hexdigest() != expected:
            errors.append("changed_binding:" + name)
            return None
        value = json.loads(data, object_pairs_hook=_unique_object)
        if not isinstance(value, dict):
            raise ValueError("expected object")
        return value
    except (OSError, ValueError, UnicodeError):
        errors.append("unreadable_json:" + name)
        return None


def inspect_review(root: Path, review=None):
    """Validate this frozen checkpoint. Optional dict input supports offline tests."""
    errors = []
    inputs = {name: _load(root, name, errors, digest) for name, digest in BINDINGS.items()}
    provenance = _load(root, PROVENANCE, errors)
    if review is None:
        review = _load(root, REVIEW, errors)
    counts = {key: 0 for key in ("accept", "reject", "withhold")}
    packet = inputs[FOLDER + "release_manifest.json"]
    if packet:
        try:
            result = inspect_packet(root, packet)
            errors.extend("packet:" + error for error in result["errors"])
        except (TypeError, ValueError, OSError):
            errors.append("invalid_packet")
    if not isinstance(review, dict):
        errors.append("invalid_review_object")
    else:
        if review.get("version") != "21-E-review-v1" or review.get("repository") != "sarurainwaterel-5/sentinel-ai" or review.get("acceptance_packet_commit") != COMMIT:
            errors.append("invalid_checkpoint")
        if review.get("source_bindings") != BINDINGS or review.get("dataset_sha256") != BINDINGS[FOLDER + "answer_cases.proposed.json"]:
            errors.append("invalid_review_bindings")
        if review.get("approved") is not True:
            errors.append("review_unapproved")
        if review.get("release_approval") is not False:
            errors.append("invalid_release_approval")
        for key in ("release_authorized", "production_enabled", "semantic_grounding_verified", "empirical_acceptance"):
            if key in review and review[key] is not False:
                errors.append("invalid_authority:" + key)
        if "proposition_to_inference" in review and review["proposition_to_inference"] != "closed":
            errors.append("invalid_authority:proposition_to_inference")
        reviewer = review.get("reviewer")
        if not _text(reviewer) or not _utc(review.get("reviewed_at")):
            errors.append("missing_reviewer_or_utc_time")
        approval = review.get("approval_evidence")
        if not isinstance(approval, dict) or approval.get("reviewer") != reviewer or approval.get("human_response") != "yes I approve" or not all(_text(approval.get(k)) for k in ("human_response", "context", "timestamp_basis")) or approval.get("recorded_at") != review.get("reviewed_at"):
            errors.append("missing_or_inconsistent_approval_evidence")
        independence = review.get("independence_attestation")
        if not isinstance(independence, dict) or independence.get("confirmed") is not True or not _text(independence.get("scope")):
            errors.append("missing_independence_attestation")
        assessments = review.get("packet_assessments")
        if not isinstance(assessments, dict) or any(assessments.get(k) != "confirmed" for k in ("evidence_citation_traceability", "conflict_and_uncertainty_preservation", "question_relevance")):
            errors.append("missing_packet_assessments")
        criteria = review.get("supplemental_criteria_approval")
        if not isinstance(criteria, dict) or criteria.get("accepted") is not True or criteria.get("criteria_path") != FOLDER + "answer_acceptance.proposed.json" or criteria.get("criteria_sha256") != BINDINGS[FOLDER + "answer_acceptance.proposed.json"] or criteria.get("reviewer") != reviewer or not _text(criteria.get("evidence")) or criteria.get("original_20_3_G_policy_unchanged") is not True:
            errors.append("invalid_criteria_acceptance")
        interpretations = review.get("field_interpretations")
        if not isinstance(interpretations, dict) or any(not isinstance(interpretations.get(k), dict) or interpretations[k].get("human_confirmed") is not True or not _text(interpretations[k].get("meaning")) or not _text(interpretations[k].get("evidence")) for k in ("answers_question", "citations_complete")):
            errors.append("missing_confirmed_field_definitions")
        cases = review.get("case_reviews")
        dataset = inputs[FOLDER + "answer_cases.proposed.json"]
        expected_ids = {c["case_id"] for c in dataset["cases"]} if dataset else set()
        seen = set()
        adopted_ids = set()
        if not isinstance(cases, list):
            errors.append("invalid_case_reviews")
            cases = []
        for case in cases:
            if not isinstance(case, dict) or not _text(case.get("case_id")):
                errors.append("invalid_case_object")
                continue
            cid = case["case_id"]
            if cid in seen:
                errors.append("duplicate_case:" + cid)
            seen.add(cid)
            decision = case.get("human_classification")
            if not isinstance(decision, str) or decision not in counts:
                errors.append("invalid_decision:" + cid)
            else:
                counts[decision] += 1
            if any(type(case.get(k)) is not bool for k in BOOLEANS):
                errors.append("incomplete_case_booleans:" + cid)
            elif ((decision == "accept" and not all(case[k] for k in BOOLEANS))
                  or (decision == "reject" and case["statement_admissible"])
                  or (decision == "withhold" and (not case["statement_admissible"] or case["answers_question"]))):
                errors.append("inconsistent_decision:" + cid)
            if cid == "irrelevant" and (decision != "withhold" or case.get("statement_admissible") is not True or case.get("answers_question") is not False):
                errors.append("irrelevant_must_be_admissible_and_withheld")
            if not _text(case.get("human_rationale")) or not _text(case.get("requested_revision")):
                errors.append("incomplete_case_text:" + cid)
            origin = case.get("rationale_origin")
            if not isinstance(origin, str) or origin not in ORIGINS:
                errors.append("unknown_rationale_origin:" + cid)
            if origin == ADOPTED:
                adopted_ids.add(cid)
        if len(cases) != 13 or seen != expected_ids:
            errors.append("incomplete_case_coverage")
        if counts != {"accept": 6, "reject": 6, "withhold": 1}:
            errors.append("invalid_checkpoint_counts")
        adoption = review.get("rationale_adoption")
        ids = adoption.get("case_ids") if isinstance(adoption, dict) else None
        if not isinstance(ids, list) or any(not isinstance(cid, str) for cid in ids) or len(ids) != len(set(ids)) or set(ids) != adopted_ids or not _text(adoption.get("evidence")) or adoption.get("independently_human_authored") is not False:
            errors.append("invalid_rationale_adoption")
        if not isinstance(provenance, dict) or provenance.get("acceptance_packet_commit") != COMMIT or provenance.get("dataset_sha256") != review.get("dataset_sha256") or not _text(provenance.get("verification_evidence")):
            errors.append("invalid_rationale_provenance")
        else:
            proposals = provenance.get("case_rationales")
            proposal_ids = []
            if not isinstance(proposals, list):
                errors.append("invalid_rationale_proposals")
                proposals = []
            by_id = {c["case_id"]: c for c in cases if isinstance(c, dict) and isinstance(c.get("case_id"), str)}
            frozen_rationales = {c["case_id"]: c["rationale"] for c in dataset["cases"]} if dataset else {}
            for proposal in proposals:
                if not isinstance(proposal, dict) or not isinstance(proposal.get("case_id"), str):
                    errors.append("invalid_rationale_proposal")
                    continue
                cid = proposal["case_id"]
                proposal_ids.append(cid)
                case = by_id.get(cid, {})
                if proposal.get("human_verified") is not True or proposal.get("origin") != "assistant_authored_in_frozen_answer_cases.proposed.json" or case.get("rationale_origin") != ADOPTED or case.get("human_rationale") != proposal.get("proposed_rationale") or proposal.get("proposed_rationale") != frozen_rationales.get(cid):
                    errors.append("unverified_or_misattributed_rationale:" + cid)
            if len(proposal_ids) != len(set(proposal_ids)) or set(proposal_ids) != adopted_ids or len(adopted_ids) != 11:
                errors.append("incomplete_rationale_provenance")
    return {"review_integrity": "invalid" if errors else "valid",
            "human_review_approved": not errors, "errors": errors,
            "classification_counts": counts, "release_authorized": False,
            "production_enabled": False, "semantic_grounding_verified": False,
            "proposition_to_inference": "closed",
            "remaining_release_gates": ["20.3-G empirical evaluation and final acceptance",
                "Authenticated retrieval, catalog and race integration",
                "Production provider composition and operational budgets",
                "Runtime release-gate consumption and rendered-citation acceptance"],
            "limitation": "Offline content and attestation checks only; no authenticated identity, source truth, semantic accuracy or production authorization."}


def main():
    report = inspect_review(ROOT)
    print(json.dumps(report, indent=2))
    return 0 if report["review_integrity"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
