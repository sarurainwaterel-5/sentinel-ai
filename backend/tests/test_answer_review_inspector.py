"""Offline review integrity is distinct from semantic and production acceptance."""
import copy
import json
from pathlib import Path

import pytest

from evaluation.governed_answers.inspect_review import (
    BINDINGS, FOLDER, PROVENANCE, REVIEW, ROOT, inspect_review, main,
)


def review():
    return json.loads((ROOT / REVIEW).read_text())


@pytest.fixture
def packet_root(tmp_path):
    manifest = json.loads((ROOT / (FOLDER + "release_manifest.json")).read_text())
    names = set(BINDINGS) | set(manifest["sha256_bindings"]) | {REVIEW, PROVENANCE}
    for name in names:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    return tmp_path


def assert_disabled(result):
    assert result["release_authorized"] is False
    assert result["production_enabled"] is False
    assert result["semantic_grounding_verified"] is False
    assert result["proposition_to_inference"] == "closed"
    assert result["remaining_release_gates"]


def test_approved_review_is_valid_without_unlocking_release():
    result = inspect_review(ROOT)
    assert result["review_integrity"] == "valid", result["errors"]
    assert result["human_review_approved"] is True
    assert result["classification_counts"] == {"accept": 6, "reject": 6, "withhold": 1}
    assert_disabled(result)


@pytest.mark.parametrize("key,value", [
    ("approved", False), ("approved", 1), ("reviewer", None), ("reviewer", " "),
    ("reviewed_at", None), ("reviewed_at", "2026-02-30T15:04:34Z"),
    ("reviewed_at", "2026-10-12T15:04:34"), ("approval_evidence", None),
    ("approval_evidence", {}), ("independence_attestation", {}),
    ("packet_assessments", {}), ("supplemental_criteria_approval", {}),
    ("field_interpretations", {}), ("rationale_adoption", {}),
    ("rationale_adoption", {"case_ids": [[]]}),
    ("dataset_sha256", "0" * 64), ("source_bindings", {}),
    ("source_bindings", {"../../secret": "0" * 64}),
    ("acceptance_packet_commit", "0" * 40), ("version", "other"),
    ("repository", "other/repository"), ("case_reviews", None),
    ("case_reviews", [None]), ("case_reviews", [{"case_id": []}]),
])
def test_incomplete_and_stale_review_is_invalid(key, value):
    record = review()
    record[key] = value
    result = inspect_review(ROOT, record)
    assert result["review_integrity"] == "invalid"
    assert result["human_review_approved"] is False
    assert_disabled(result)


@pytest.mark.parametrize("key,value", [
    ("release_approval", True), ("release_approval", None),
    ("release_authorized", True), ("production_enabled", True),
    ("semantic_grounding_verified", True), ("empirical_acceptance", True),
    ("proposition_to_inference", "open"),
])
def test_metadata_cannot_open_release(key, value):
    record = review()
    record[key] = value
    result = inspect_review(ROOT, record)
    assert result["review_integrity"] == "invalid"
    assert_disabled(result)


@pytest.mark.parametrize("field,value", [
    ("statement_admissible", None), ("answers_question", 1),
    ("preserves_conflicts_and_uncertainty", "true"), ("citations_complete", None),
    ("human_rationale", " "), ("requested_revision", None),
    ("rationale_origin", "independently_human_authored"),
    ("rationale_origin", []), ("human_classification", "release"),
    ("human_classification", []),
])
def test_incomplete_case_fields(field, value):
    record = review()
    record["case_reviews"][0][field] = value
    assert inspect_review(ROOT, record)["review_integrity"] == "invalid"


def test_duplicate_missing_and_unknown_ids_are_invalid():
    for cases in (review()["case_reviews"][:-1],
                  review()["case_reviews"] + [copy.deepcopy(review()["case_reviews"][0])]):
        record = review()
        record["case_reviews"] = cases
        assert inspect_review(ROOT, record)["review_integrity"] == "invalid"
    record = review()
    record["case_reviews"][0]["case_id"] = "unknown"
    assert inspect_review(ROOT, record)["review_integrity"] == "invalid"


@pytest.mark.parametrize("cid,key,value", [
    ("faithful-paraphrase", "statement_admissible", False),
    ("faithful-paraphrase", "answers_question", False),
    ("unsupported", "statement_admissible", True),
    ("irrelevant", "statement_admissible", False),
    ("irrelevant", "answers_question", True),
    ("irrelevant", "human_classification", "accept"),
])
def test_decision_consistency_and_withheld_irrelevant(cid, key, value):
    record = review()
    case = next(c for c in record["case_reviews"] if c["case_id"] == cid)
    case[key] = value
    assert inspect_review(ROOT, record)["review_integrity"] == "invalid"


def test_approval_evidence_must_match_reviewer_and_time():
    for key, value in (("reviewer", "Someone else"), ("recorded_at", "2020-01-01T00:00:00Z"),
                       ("human_response", ""), ("human_response", "no I reject"), ("context", "")):
        record = review()
        record["approval_evidence"][key] = value
        assert inspect_review(ROOT, record)["review_integrity"] == "invalid"


@pytest.mark.parametrize("name", list(BINDINGS))
def test_changed_frozen_input_is_invalid_even_if_review_hash_is_rewritten(packet_root, name):
    path = packet_root / name
    path.write_bytes(path.read_bytes() + b"\n")
    record = review()
    import hashlib
    record["source_bindings"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    assert inspect_review(packet_root, record)["review_integrity"] == "invalid"


def test_changed_implementation_invalidates_original_packet(packet_root):
    path = packet_root / "backend/app/routes/governed_answers.py"
    path.write_bytes(path.read_bytes() + b"\n")
    result = inspect_review(packet_root)
    assert any(error.startswith("packet:changed_binding:") for error in result["errors"])
    assert result["review_integrity"] == "invalid"


@pytest.mark.parametrize("content", ["{broken", "[]", '{"approved":true,"approved":false}', 'null'])
def test_malformed_review_file_returns_invalid(packet_root, content):
    (packet_root / REVIEW).write_text(content)
    assert inspect_review(packet_root)["review_integrity"] == "invalid"


def test_missing_review_or_provenance_returns_invalid(packet_root):
    (packet_root / REVIEW).unlink()
    assert inspect_review(packet_root)["review_integrity"] == "invalid"
    (packet_root / REVIEW).write_bytes((ROOT / REVIEW).read_bytes())
    (packet_root / PROVENANCE).unlink()
    assert inspect_review(packet_root)["review_integrity"] == "invalid"


def test_fixed_input_symlink_cannot_escape_root(packet_root, tmp_path):
    name = FOLDER + "answer_cases.proposed.json"
    outside = tmp_path.parent / (tmp_path.name + "-outside.json")
    outside.write_bytes((ROOT / name).read_bytes())
    (packet_root / name).unlink()
    (packet_root / name).symlink_to(outside)
    result = inspect_review(packet_root)
    assert "unsafe_path:" + name in result["errors"]


@pytest.mark.parametrize("mutation", ["unverified", "rationale", "origin", "duplicate", "missing", "malformed"])
def test_adoption_provenance_cannot_be_silently_changed(packet_root, mutation):
    path = packet_root / PROVENANCE
    data = json.loads(path.read_text())
    if mutation == "unverified":
        data["case_rationales"][0]["human_verified"] = False
    elif mutation == "rationale":
        data["case_rationales"][0]["proposed_rationale"] = "new wording"
    elif mutation == "origin":
        data["case_rationales"][0]["origin"] = "human"
    elif mutation == "duplicate":
        data["case_rationales"].append(copy.deepcopy(data["case_rationales"][0]))
    elif mutation == "missing":
        data["case_rationales"].pop()
    else:
        data["case_rationales"] = [None]
    path.write_text(json.dumps(data))
    assert inspect_review(packet_root)["review_integrity"] == "invalid"


def test_unapproved_template_is_not_complete_review():
    record = json.loads((ROOT / (FOLDER + "answer_review.template.json")).read_text())
    result = inspect_review(ROOT, record)
    assert result["review_integrity"] == "invalid"
    assert_disabled(result)


def test_cli_exits_nonzero_for_invalid_review(packet_root, monkeypatch, capsys):
    import evaluation.governed_answers.inspect_review as module
    monkeypatch.setattr(module, "ROOT", packet_root)
    assert main() == 0
    assert json.loads(capsys.readouterr().out)["release_authorized"] is False
    (packet_root / REVIEW).write_text("{}")
    assert main() == 1
    assert json.loads(capsys.readouterr().out)["review_integrity"] == "invalid"


def test_review_and_provenance_cannot_jointly_rewrite_adopted_frozen_rationale(packet_root):
    path = packet_root / PROVENANCE
    data = json.loads(path.read_text())
    data["case_rationales"][0]["proposed_rationale"] = "new rationale not adopted from frozen packet"
    path.write_text(json.dumps(data))
    record = review()
    record["case_reviews"][0]["human_rationale"] = data["case_rationales"][0]["proposed_rationale"]
    assert inspect_review(packet_root, record)["review_integrity"] == "invalid"
