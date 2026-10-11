"""Deterministic fixture renderer. Never paraphrases assessed statements."""
import hashlib
import json
from app.services.cognition.reasoning.answer_models import AnswerClaim, EvidenceReference


def claim_digest(statement: str, qualifications: tuple[str, ...]) -> str:
    return hashlib.sha256(json.dumps({"statement": statement, "qualifications": qualifications},
        ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def render_fixture(claim: AnswerClaim, evidence: tuple[EvidenceReference, ...], *, inputs: dict) -> str:
    # Revalidate because nested reused models can be mutable despite frozen wrappers.
    claim = AnswerClaim.model_validate(claim.model_dump(), strict=True)
    references = tuple(EvidenceReference.model_validate(e.model_dump(), strict=True) for e in evidence)
    digest = hashlib.sha256(json.dumps(inputs, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if digest != claim.validation.inputs_sha256 or inputs.get("evidence") != [e.model_dump() for e in references]:
        raise ValueError("Assessed input snapshot changed before rendering.")
    if claim.kind != "attributed_synthesis" or claim.validation.statement_status != "admissible":
        raise ValueError("Unassessed content cannot be rendered as an answer fixture.")
    ids = [e.evidence_id for e in references]
    if len(set(ids)) != len(ids) or set(claim.evidence_ids) != set(ids):
        raise ValueError("Fixture citations must cover the complete evidence snapshot.")
    labels = " ".join(f"[{index}]" for index, _ in enumerate(references, start=1))
    # Fixed labeling is explicit attribution, not an additional factual conclusion.
    text = f"Attributed synthesis (offline fixture; not released):\n{claim.statement} {labels}"
    if claim.qualifications:
        text += "\nRecorded qualifications:\n" + "\n".join(claim.qualifications)
    return text
