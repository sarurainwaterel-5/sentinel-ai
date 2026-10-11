"""Sprint 21 contracts only. These records confer no inference authority."""
import hashlib
import json
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator
from app.services.cognition.reasoning.models import CandidateRelationshipReference, Premise, PremiseRelationship, ConfidenceAssessment
from app.services.cognition.reasoning.statement_admissibility_validator import StatementAdmissibilityResult


class AnswerRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    @field_validator("semantic_grounding_verified", check_fields=False, mode="before")
    @classmethod
    def false_only(cls, value):
        if value is not False:
            raise ValueError("Grounding verification must remain literally false.")
        return value


class EvidenceReference(AnswerRecord):
    evidence_id: str = Field(min_length=1, max_length=200)
    snapshot_id: str = Field(min_length=1, max_length=200)
    document_id: str = Field(min_length=1, max_length=200)
    organization_id: str = Field(min_length=1, max_length=200)
    collection: str = Field(min_length=1, max_length=200)
    chunk_index: int = Field(ge=0)
    text: str = Field(min_length=1, max_length=100000)
    text_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    filename: str | None = None
    file_hash: str | None = None
    module: str | None = None
    topic: str | None = None
    status: Literal["indexed"] = "indexed"

    @model_validator(mode="after")
    def exact_text(self):
        if any(not v.strip() for v in (self.evidence_id, self.snapshot_id, self.document_id, self.organization_id, self.collection, self.text)):
            raise ValueError("Evidence identity and text must not be blank.")
        if self.text_sha256 != hashlib.sha256(self.text.encode()).hexdigest():
            raise ValueError("Text hash must match the exact evidence snapshot.")
        return self


class ClaimValidation(AnswerRecord):
    structural_status: Literal["not_run", "passed", "rejected"] = "not_run"
    statement_status: Literal["not_run", "admissible", "rejected", "unavailable", "refused", "malformed", "error"] = "not_run"
    statement_result: StatementAdmissibilityResult | None = None
    semantic_grounding_verified: Literal[False] = False
    candidate_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    inputs_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")
    policy_version: str | None = None

    @model_validator(mode="after")
    def consistent(self):
        if self.statement_status == "admissible" and (
            self.structural_status != "passed" or self.statement_result is None
            or not self.statement_result.admissible or self.statement_result.rejection_reasons
            or not self.candidate_sha256 or not self.inputs_sha256 or not self.policy_version
        ):
            raise ValueError("Admissibility requires both explicit gates.")
        if self.statement_status != "admissible" and self.statement_result and self.statement_result.admissible:
            raise ValueError("Statement status contradicts its result.")
        return self


class AnswerClaim(AnswerRecord):
    claim_id: str = Field(min_length=1, max_length=200)
    statement: str = Field(min_length=1, max_length=10000)
    kind: Literal["attributed_synthesis", "source_report"]
    premise_ids: tuple[str, ...] = Field(min_length=1, max_length=25)
    relationship_references: tuple[CandidateRelationshipReference, ...] = Field(default=(), max_length=300)
    evidence_ids: tuple[str, ...] = Field(min_length=1, max_length=25)
    qualifications: tuple[str, ...] = Field(default=(), max_length=25)
    validation: ClaimValidation = Field(default_factory=ClaimValidation)

    @model_validator(mode="after")
    def distinct_lineage(self):
        if not self.statement.strip() or any(not v.strip() for v in (*self.premise_ids, *self.evidence_ids)):
            raise ValueError("Blank claims or lineage are invalid.")
        if len(set(self.premise_ids)) != len(self.premise_ids) or len(set(self.evidence_ids)) != len(self.evidence_ids):
            raise ValueError("Duplicate lineage is invalid.")
        if self.kind == "attributed_synthesis" and len(self.premise_ids) < 2:
            raise ValueError("Synthesis requires two distinct premises.")
        if self.validation.statement_status == "admissible":
            expected = hashlib.sha256(json.dumps(
                {"statement": self.statement, "qualifications": self.qualifications},
                ensure_ascii=False, separators=(",", ":"),
            ).encode()).hexdigest()
            if self.validation.candidate_sha256 != expected:
                raise ValueError("Validation is bound to different claim text.")
            scope = self.validation.statement_result.validation_scope
            if self.kind == "attributed_synthesis" and scope != "independent_model_semantic_admissibility":
                raise ValueError("Source report fidelity cannot certify synthesis.")
        return self


class AnswerValidation(AnswerRecord):
    coverage_status: Literal["not_run", "passed", "rejected"] = "not_run"
    citation_status: Literal["not_run", "passed", "rejected"] = "not_run"
    release_status: Literal["disabled"] = "disabled"
    semantic_grounding_verified: Literal[False] = False
    rejection_reasons: tuple[str, ...] = ()


class AnswerScope(AnswerRecord):
    organization_id: str = Field(min_length=1, max_length=200)
    module: str | None = None
    topic: str | None = None
    limit: int = Field(default=5, ge=1, le=25)
    score_threshold: float = Field(default=0.45, ge=0, le=1)


class GovernedAnswer(AnswerRecord):
    schema_version: Literal["21.v1"] = "21.v1"
    answer_id: str | None = None
    request_id: str | None = None
    scope: AnswerScope | None = None
    question: str = Field(min_length=1, max_length=10000)
    snapshot_id: str = Field(min_length=1, max_length=200)
    outcome: Literal["disabled", "insufficient_evidence", "blocked_provenance", "blocked_relationships", "blocked_validation", "rejected", "provider_failure"] = "disabled"
    answer_text: None = None
    claims: tuple[AnswerClaim, ...] = ()
    evidence: tuple[EvidenceReference, ...] = Field(default=(), max_length=25)
    premises: tuple[Premise, ...] = ()
    relationships: tuple[PremiseRelationship, ...] = ()
    conflicts: tuple[str, ...] = ()
    unresolved_relationships: tuple[PremiseRelationship, ...] = ()
    limitations: tuple[str, ...] = ()
    confidence: ConfidenceAssessment | None = None
    constitutional_status: Literal["not_evaluated"] = "not_evaluated"
    operational_trace: tuple[str, ...] = ()
    recommended_next_step: str | None = None
    uncertainty: tuple[str, ...] = ()
    missing_information: tuple[str, ...] = ()
    validation: AnswerValidation = Field(default_factory=AnswerValidation)

    @model_validator(mode="after")
    def snapshot_integrity(self):
        if not self.question.strip():
            raise ValueError("Question must not be blank.")
        if self.claims:
            raise ValueError("21-B cannot publish claims while release is disabled.")
        if self.scope and any(e.organization_id != self.scope.organization_id or
            (self.scope.module and e.module != self.scope.module) or
            (self.scope.topic and e.topic != self.scope.topic) for e in self.evidence):
            raise ValueError("Evidence violates the captured scope.")
        ids = [e.evidence_id for e in self.evidence]
        if len(set(ids)) != len(ids) or any(e.snapshot_id != self.snapshot_id for e in self.evidence):
            raise ValueError("Evidence must be unique and belong to this snapshot.")
        return self
