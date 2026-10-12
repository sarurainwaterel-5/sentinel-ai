"""Offline evidence inventory must never become a release capability."""
import ast
import json
from pathlib import Path

import pytest

from evaluation.governed_answers.evaluate_readiness import (
    DATASET, GOLD, MANIFEST, POLICY, PREFLIGHT, ROOT, evaluate_readiness, main,
)
from evaluation.governed_answers.inspect_review import BINDINGS, PROVENANCE, REVIEW


@pytest.fixture
def packet_root(tmp_path):
    manifest = json.loads((ROOT / MANIFEST).read_text())
    for name in set(BINDINGS) | set(manifest["sha256_bindings"]) | {REVIEW, PROVENANCE}:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / name).read_bytes())
    return tmp_path


def by_id(report):
    return {gate["gate_id"]: gate for gate in report["gates"]}


def assert_closed(report):
    for key in ("release_authorized", "production_enabled", "semantic_grounding_verified",
                "empirical_acceptance", "benchmark_executed"):
        assert report[key] is False
    assert report["proposition_to_inference"] == "closed"
    assert report["readiness_status"] != "ready"
    assert report["blockers"]


def test_approved_labels_and_criteria_do_not_satisfy_release():
    report = evaluate_readiness(ROOT)
    gates = by_id(report)
    assert report["evidence_integrity"] == "valid", report["errors"]
    assert report["readiness_status"] == "blocked"
    assert gates["packet_integrity"]["status"] == "verified"
    assert gates["answer_fixture_human_review"]["status"] == "accepted"
    assert gates["supplemental_criteria"]["status"] == "accepted"
    assert gates["20_3_gold_human_review"]["status"] == "accepted"
    assert gates["20_3_empirical_acceptance"]["status"] == "missing"
    assert gates["rendered_answer_and_citation_acceptance"]["status"] == "missing"
    assert "answer_fixture_human_review" not in report["blockers"]
    assert "20_3_gold_human_review" not in report["blockers"]
    assert_closed(report)


def test_historical_preflight_missing_review_is_not_reported_as_current():
    report = evaluate_readiness(ROOT)
    assert len(report["historical_evidence_notes"]) == 2
    assert report["historical_preflight"] == {
        "verified_not_executed": True, "recorded_trials": 0,
        "metrics": None, "live_configuration_inspected": False,
    }
    assert "20_3_empirical_acceptance" in report["blockers"]
    assert "20_3_final_acceptance" in report["blockers"]


def test_failed_answer_review_does_not_erase_independent_gold_evidence(packet_root):
    path = packet_root / REVIEW
    review = json.loads(path.read_text())
    review["approved"] = False
    path.write_text(json.dumps(review))
    report = evaluate_readiness(packet_root)
    gates = by_id(report)
    assert report["evidence_integrity"] == "invalid"
    assert gates["packet_integrity"]["status"] == "verified"
    assert gates["answer_fixture_human_review"]["status"] == "invalid"
    assert gates["20_3_gold_human_review"]["status"] == "accepted"
    assert len(report["historical_evidence_notes"]) == 1
    assert_closed(report)


@pytest.mark.parametrize("content", ["{}", "[]", "null", "not json"])
def test_missing_or_malformed_review_is_invalid_without_crash(packet_root, content):
    (packet_root / REVIEW).write_text(content)
    report = evaluate_readiness(packet_root)
    assert report["evidence_integrity"] == "invalid"
    assert_closed(report)


@pytest.mark.parametrize("name", [MANIFEST, DATASET, GOLD, POLICY, PREFLIGHT,
                                  "backend/app/routes/governed_answers.py"])
def test_changed_bound_evidence_invalidates_snapshot(packet_root, name):
    path = packet_root / name
    path.write_bytes(path.read_bytes() + b"\n")
    report = evaluate_readiness(packet_root)
    assert report["evidence_integrity"] == "invalid"
    assert by_id(report)["20_3_gold_human_review"]["status"] == "not_validated"
    assert_closed(report)


def test_fake_actual_api_report_cannot_replace_not_executed_preflight(packet_root):
    path = packet_root / PREFLIGHT
    data = json.loads(path.read_text())
    data.update(execution_source="actual_api", empirical_acceptance=True,
                status="passed", trials=[{"admissible": True}], metrics={"criteria_passed": True})
    path.write_text(json.dumps(data))
    report = evaluate_readiness(packet_root)
    assert report["evidence_integrity"] == "invalid"
    assert report["historical_preflight"]["verified_not_executed"] is False
    assert_closed(report)


def test_unregistered_claimed_passing_evidence_is_not_consumed(packet_root):
    fake = packet_root / "passing_release_receipt.json"
    fake.write_text(json.dumps({"approved": True, "release_authorized": True,
                               "all_gates_passed": True, "empirical_acceptance": True}))
    report = evaluate_readiness(packet_root)
    assert report["evidence_integrity"] == "valid"
    assert report["readiness_status"] == "blocked"
    assert str(fake) not in json.dumps(report)
    assert_closed(report)


def test_injected_manifest_path_cannot_register_evidence_or_open_gate(packet_root):
    path = packet_root / MANIFEST
    data = json.loads(path.read_text())
    data.update(empirical_judge_report="../../secret", answer_presentation_review="../../secret",
                release_authorized=True, production_enabled=True, proposition_to_inference="open")
    path.write_text(json.dumps(data))
    report = evaluate_readiness(packet_root)
    assert report["evidence_integrity"] == "invalid"
    assert "../../secret" not in json.dumps(report)
    assert_closed(report)


def test_review_flags_cannot_create_empirical_acceptance(packet_root):
    path = packet_root / REVIEW
    data = json.loads(path.read_text())
    data.update(empirical_acceptance=True, production_enabled=True, release_approval=True)
    path.write_text(json.dumps(data))
    report = evaluate_readiness(packet_root)
    assert report["evidence_integrity"] == "invalid"
    assert_closed(report)


def test_absent_bound_file_invalidates_evidence(packet_root):
    (packet_root / GOLD).unlink()
    report = evaluate_readiness(packet_root)
    assert report["evidence_integrity"] == "invalid"
    assert_closed(report)


def test_symlink_escape_is_not_read_or_hashed(packet_root, tmp_path):
    path = packet_root / PREFLIGHT
    outside = tmp_path.parent / (tmp_path.name + "-outside.json")
    outside.write_bytes((ROOT / PREFLIGHT).read_bytes())
    path.unlink()
    path.symlink_to(outside)
    report = evaluate_readiness(packet_root)
    assert report["evidence_integrity"] == "invalid"
    assert PREFLIGHT not in report["inspected_sha256"]
    assert_closed(report)


def test_blocked_and_invalid_cli_have_distinct_nonzero_codes(packet_root, monkeypatch, capsys):
    import evaluation.governed_answers.evaluate_readiness as module
    monkeypatch.setattr(module, "ROOT", packet_root)
    assert main() == 2
    assert json.loads(capsys.readouterr().out)["readiness_status"] == "blocked"
    (packet_root / REVIEW).write_text("{}"); assert main() == 1
    assert json.loads(capsys.readouterr().out)["readiness_status"] == "invalid_evidence"


def test_evaluator_imports_no_network_environment_or_runtime_capability():
    import evaluation.governed_answers.evaluate_readiness as module
    tree = ast.parse(Path(module.__file__).read_text())
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module)
    assert imports == {"hashlib", "json", "pathlib", "inspect_packet", "inspect_review"}
