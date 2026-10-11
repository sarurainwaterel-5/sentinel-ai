"""Packet integrity checks do not evaluate semantic behavior or authorize release."""
import copy
import json
from evaluation.governed_answers.inspect_packet import ROOT, PACKET, inspect_packet


def manifest():
    return json.loads(PACKET.read_text())


def test_committed_packet_is_bound_and_disabled():
    report=inspect_packet(ROOT,manifest())
    assert report["packet_integrity"]=="valid"
    assert report["release_authorized"] is False
    assert report["production_enabled"] is False
    assert report["release_blockers"]


def test_changed_content_invalidates_packet():
    packet=manifest()
    name=next(iter(packet["sha256_bindings"]))
    packet["sha256_bindings"][name]="0"*64
    assert inspect_packet(ROOT,packet)["packet_integrity"]=="invalid"


def test_metadata_cannot_authorize_release_or_open_inference():
    for key,value in (("release_authorized",True),("production_enabled",True),
                      ("semantic_grounding_verified",True),("proposition_to_inference","open")):
        packet=copy.deepcopy(manifest());packet[key]=value
        report=inspect_packet(ROOT,packet)
        assert report["packet_integrity"]=="invalid"
        assert report["release_authorized"] is False


def test_inspection_does_not_read_arbitrary_files():
    packet=manifest();packet["sha256_bindings"]={"../../secret":"0"*64}
    assert inspect_packet(ROOT,packet)["errors"]==["invalid_binding_path"]


def test_proposed_cases_have_complete_review_slots_and_no_fabricated_approval():
    folder=PACKET.parent
    dataset=json.loads((folder/"answer_cases.proposed.json").read_text())
    review=json.loads((folder/"answer_review.template.json").read_text())
    cases=dataset["cases"]
    assert len(cases)==13 and len({c["case_id"] for c in cases})==13
    assert {c["case_id"] for c in cases}=={c["case_id"] for c in review["case_reviews"]}
    assert review["approved"] is False and review["release_approval"] is False
    assert all(c["statement_admissible"] is None and c["answers_question"] is None for c in review["case_reviews"])
    irrelevant=next(c for c in cases if c["category"]=="query_relevance")
    assert irrelevant["proposed_expectation"]=={"statement_admissible":True,"eligible_answer_after_all_release_gates":False}


def test_structurally_valid_review_cases_do_not_claim_semantic_grounding():
    from app.services.cognition.reasoning.models import CandidateProposition, Premise, PremiseRelationship
    from app.services.cognition.reasoning.proposition_grounding_validator import PropositionGroundingValidator
    cases=json.loads((PACKET.parent/"answer_cases.proposed.json").read_text())["cases"]
    for case in cases:
        result=PropositionGroundingValidator().validate(candidate=CandidateProposition.model_validate(case["candidate"]),
            premises=[Premise.model_validate(p) for p in case["premises"]],
            relationships=[PremiseRelationship.model_validate(r) for r in case["relationships"]])
        assert result.structurally_valid and result.semantic_grounding_verified is False
