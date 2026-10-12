"""Exact approved offline artifacts confer no production presentation authority."""
import copy
import json
from pathlib import Path

import pytest

from evaluation.governed_answers.inspect_presentation import (
    ARTIFACT_BINDINGS, SOURCE_BINDINGS, RECORD, FIXTURES, HTML, ROOT,
    inspect_presentation, main,
)
from evaluation.governed_answers.inspect_review import BINDINGS, REVIEW, PROVENANCE


def record():
    return json.loads((ROOT / RECORD).read_text())


@pytest.fixture
def packet_root(tmp_path):
    manifest = json.loads((ROOT / "backend/evaluation/governed_answers/release_manifest.json").read_text())
    names = set(BINDINGS) | set(manifest["sha256_bindings"]) | set(ARTIFACT_BINDINGS) | set(SOURCE_BINDINGS) | {RECORD, REVIEW, PROVENANCE}
    for name in names:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / name).read_bytes())
    return tmp_path


def assert_closed(report):
    for key in ("production_presentation_accepted", "release_authorized", "production_enabled",
                "semantic_grounding_verified", "empirical_acceptance"):
        assert report[key] is False
    assert report["proposition_to_inference"] == "closed"
    assert report["assistant_browser_visual_inspection_completed"] is False


def test_approved_static_packet_is_valid_not_production_accepted():
    report = inspect_presentation(ROOT)
    assert report["presentation_integrity"] == "valid", report["errors"]
    assert report["offline_fixture_presentation_approved"] is True
    assert report["observed_counts"] == {"accepted_previews": 6, "withheld_cases": 7}
    assert_closed(report)


@pytest.mark.parametrize("key,value", [
    ("approved", False), ("approved", 1), ("reviewer", None),
    ("reviewed_at", "2026-02-30T16:46:19Z"), ("reviewed_at", None),
    ("approval_evidence", None), ("approval_evidence", {}),
    ("confirmation_evidence", {}), ("packet_assessments", {}),
    ("source_bindings", {}), ("source_bindings", {"../../secret":"0"*64}),
    ("fixture_packet_sha256", "0"*64), ("html_sha256", "0"*64),
    ("reviewed_artifact_paths", {"fixtures":"../../secret", "html":"../../secret"}),
    ("guard_implementation_commit", "0"*40), ("case_reviews", None),
    ("case_reviews", [None]), ("case_reviews", [{"case_id":[]}]),
    ("assessment_scope", ""), ("approval_limitation", ""),
    ("browser_visual_inspection", {"assistant_completed":True}),
])
def test_incomplete_or_rebound_record_is_invalid(key, value):
    data = record()
    data[key] = value
    report = inspect_presentation(ROOT, data)
    assert report["presentation_integrity"] == "invalid"
    assert report["offline_fixture_presentation_approved"] is False
    assert_closed(report)


@pytest.mark.parametrize("key,value", [
    ("release_approval", True), ("production_presentation_accepted", True),
    ("production_enabled", True), ("empirical_acceptance", True),
    ("release_authorized", True), ("semantic_grounding_verified", True),
    ("proposition_to_inference", "open"),
])
def test_record_flags_cannot_expand_fixture_approval(key, value):
    data = record()
    data[key] = value
    report = inspect_presentation(ROOT, data)
    assert report["presentation_integrity"] == "invalid"
    assert_closed(report)


def test_confirmation_scope_cannot_be_rewritten():
    data = record()
    data["packet_assessments"]["offline_disabled_scope_clear"]["scope"] = "Production release is accepted."
    assert inspect_presentation(ROOT, data)["presentation_integrity"] == "invalid"
    data = record()
    data["packet_assessments"]["accepted_preview_text"]["confirmed"] = False
    assert inspect_presentation(ROOT, data)["presentation_integrity"] == "invalid"


def test_explicit_approval_must_match_human_and_time():
    for key,value in (("human_response","no"), ("reviewer","Another reviewer"),
                      ("recorded_at","2020-01-01T00:00:00Z"), ("context","")):
        data = record()
        data["approval_evidence"][key] = value
        assert inspect_presentation(ROOT, data)["presentation_integrity"] == "invalid"


def test_case_worksheet_cannot_invent_individual_ratings_or_rationales():
    for field,value in (("exact_text_preserved",True), ("human_rationale","Invented human words")):
        data = record()
        data["case_reviews"][0][field] = value
        report = inspect_presentation(ROOT, data)
        assert report["presentation_integrity"] == "invalid"
        assert any(error.startswith("unprovided_case_rating_or_rationale:") for error in report["errors"])


def test_case_coverage_requires_unique_complete_ids():
    for mode in ("missing","duplicate","unknown"):
        data = record()
        if mode == "missing":
            data["case_reviews"].pop()
        elif mode == "duplicate":
            data["case_reviews"].append(copy.deepcopy(data["case_reviews"][0]))
        else:
            data["case_reviews"][0]["case_id"] = "unknown"
        assert inspect_presentation(ROOT, data)["presentation_integrity"] == "invalid"


@pytest.mark.parametrize("name", list(SOURCE_BINDINGS) + list(ARTIFACT_BINDINGS))
def test_changed_bound_source_or_artifact_is_invalid(packet_root, name):
    path = packet_root / name
    path.write_bytes(path.read_bytes()+b"\n")
    report = inspect_presentation(packet_root)
    assert report["presentation_integrity"] == "invalid"
    assert_closed(report)


def test_caller_cannot_rehash_modified_html_to_renew_approval(packet_root):
    import hashlib
    path = packet_root / HTML
    path.write_bytes(path.read_bytes()+b"<script>newDisplay()</script>")
    data = record()
    data["html_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    report = inspect_presentation(packet_root, data)
    assert report["presentation_integrity"] == "invalid"
    assert "changed_binding:"+HTML in report["errors"]


def test_irrelevant_preview_cannot_be_reintroduced_in_approved_packet(packet_root):
    path = packet_root / FIXTURES
    data = json.loads(path.read_text())
    irrelevant = next(c for c in data["cases"] if c["case_id"]=="irrelevant")
    irrelevant["report"]["fixture_claim"] = data["cases"][0]["report"]["fixture_claim"]
    path.write_text(json.dumps(data))
    assert inspect_presentation(packet_root)["presentation_integrity"] == "invalid"


@pytest.mark.parametrize("content", ['null','[]','broken','{"approved":true,"approved":false}'])
def test_malformed_record_returns_invalid(packet_root, content):
    (packet_root / RECORD).write_text(content)
    report = inspect_presentation(packet_root)
    assert report["presentation_integrity"] == "invalid"
    assert_closed(report)


def test_missing_record_and_html_return_invalid(packet_root):
    (packet_root / RECORD).unlink()
    assert inspect_presentation(packet_root)["presentation_integrity"] == "invalid"
    (packet_root / RECORD).write_bytes((ROOT / RECORD).read_bytes())
    (packet_root / HTML).unlink()
    assert inspect_presentation(packet_root)["presentation_integrity"] == "invalid"


def test_artifact_symlink_escape_is_not_read(packet_root, tmp_path):
    outside = tmp_path.parent / (tmp_path.name+"-outside.html")
    outside.write_bytes((ROOT / HTML).read_bytes())
    path = packet_root / HTML
    path.unlink()
    path.symlink_to(outside)
    report = inspect_presentation(packet_root)
    assert "unsafe_path:"+HTML in report["errors"]
    assert report["presentation_integrity"] == "invalid"


def test_cli_validity_is_not_release_authority(packet_root, monkeypatch, capsys):
    import evaluation.governed_answers.inspect_presentation as module
    monkeypatch.setattr(module,"ROOT",packet_root)
    assert main()==0
    report=json.loads(capsys.readouterr().out)
    assert_closed(report)
    (packet_root / RECORD).write_text('{}')
    assert main()==1
    assert json.loads(capsys.readouterr().out)["presentation_integrity"]=="invalid"
