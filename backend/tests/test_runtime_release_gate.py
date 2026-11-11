"""Report consistency can never substitute for release authorization."""
import copy
import hashlib
import json
from pathlib import Path
import random

import pytest

from app.services.cognition.reasoning.release_gate import REVIEW, SEMANTIC, inspect_release_gate
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticJudgeVerdict
from app.services.providers.openai_semantic_admissibility import OpenAISemanticAdmissibilityProvider
from evaluation.semantic_judge.runner import digest, load_inputs, summarize

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def evidence(tmp_path):
    for name in [REVIEW, SEMANTIC + "dataset.json", SEMANTIC + "acceptance.json", SEMANTIC + "runner.py"]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    cases, policy, labels, blockers = load_inputs(tmp_path / (SEMANTIC + "dataset.json"), tmp_path / (SEMANTIC + "acceptance.json"), tmp_path / REVIEW)
    assert blockers == []
    rows = []
    for repetition in range(policy["repetitions"]):
        ordered = list(cases)
        random.Random(policy["order_seed"] + repetition).shuffle(ordered)
        rows.extend(dict(case_id=case["case_id"], repetition=repetition,
                         admissible=labels[case["case_id"]], operational_error=False,
                         rejection_reasons=[] if labels[case["case_id"]] else ["unsupported_fact"],
                         scope="independent_model_semantic_admissibility", elapsed_seconds=0)
                    for case in ordered)
    report = dict(execution_source="actual_api", provider="OpenAI", model="synthetic-test-only",
                  criteria=policy, dataset_size=36, planned_calls=108, blockers=[],
                  openai_sdk_version="test", python="test", commit="test",
                  started_at="2026-11-10T00:00:00+00:00", finished_at="2026-11-10T00:01:00+00:00",
                  trials=rows, metrics=summarize(cases, labels, rows, policy), status="passed", empirical_acceptance=True,
                  dataset_sha256=digest(tmp_path / (SEMANTIC + "dataset.json")),
                  policy_sha256=digest(tmp_path / (SEMANTIC + "acceptance.json")),
                  review_sha256=digest(tmp_path / REVIEW), runner_sha256=digest(tmp_path / (SEMANTIC + "runner.py")),
                  prompt_sha256=hashlib.sha256(OpenAISemanticAdmissibilityProvider.system_message().encode()).hexdigest(),
                  verdict_schema_sha256=hashlib.sha256(json.dumps(SemanticJudgeVerdict.model_json_schema(), sort_keys=True).encode()).hexdigest())
    return tmp_path, report


def inspect(evidence, change=None):
    root, report = evidence
    report = copy.deepcopy(report)
    if change:
        change(report)
    path = root / "report.json"
    path.write_text(json.dumps(report))
    result = inspect_release_gate(root, path)
    assert result["enabled"] is False
    assert result["production_enabled"] is False
    assert result["release_authorized"] is False
    assert result["semantic_grounding_verified"] is False
    assert result["proposition_to_inference"] == "closed"
    assert result["blockers"]
    return result


def test_no_evidence_denies_before_loading_providers():
    result = inspect_release_gate(ROOT)
    assert result["empirical_report_eligible_for_human_review"] is False
    assert "empirical_report_missing" in result["errors"]


def test_internally_consistent_synthetic_report_is_only_review_eligible(evidence):
    result = inspect(evidence)
    assert result["errors"] == []
    assert result["empirical_report_eligible_for_human_review"] is True
    assert "empirical_execution_provenance_and_final_human_review_required" in result["blockers"]


@pytest.mark.parametrize("change", [
    lambda report: report.update(execution_source="unit_test"),
    lambda report: report.update(model=""),
    lambda report: report.update(dataset_sha256="wrong"),
    lambda report: report.update(metrics={"criteria_passed": True}),
    lambda report: report.update(status="blocked"),
    lambda report: report.update(finished_at="2026-11-09T00:00:00+00:00"),
    lambda report: report["trials"].pop(),
    lambda report: report["trials"].reverse(),
    lambda report: report["trials"][0].update(operational_error=True),
    lambda report: report["trials"][0].update(admissible="true"),
    lambda report: report["trials"][0].update(repetition=True),
    lambda report: report["trials"][0].update(scope="verbatim_premise_report"),
    lambda report: report["trials"][0].update(rejection_reasons=["unbounded-invented-reason"]),
    lambda report: report["trials"][0].update(elapsed_seconds=float("nan")),
    lambda report: report["trials"][0].update(elapsed_seconds=-1),
    lambda report: report["trials"][0].update(elapsed_seconds=True),
    lambda report: report["trials"][1].update(case_id=report["trials"][0]["case_id"]),
])
def test_inconsistent_reports_are_not_review_eligible(evidence, change):
    result = inspect(evidence, change)
    assert result["empirical_report_eligible_for_human_review"] is False
    assert result["errors"]


def test_report_symlink_escape_is_denied(evidence, tmp_path):
    root, report = evidence
    outside = tmp_path.parent / (tmp_path.name + "-outside.json")
    outside.write_text(json.dumps(report))
    (root / "escaped.json").symlink_to(outside)
    result = inspect_release_gate(root, root / "escaped.json")
    assert result["empirical_report_eligible_for_human_review"] is False
    assert "invalid_empirical_evidence" in result["errors"]


@pytest.mark.parametrize("payload", ['{"status":"passed","status":"failed"}', " " * (2 * 1024 * 1024 + 1)])
def test_duplicate_keys_and_oversized_reports_are_denied(evidence, payload):
    root, _ = evidence
    path = root / "invalid.json"
    path.write_text(payload)
    result = inspect_release_gate(root, path)
    assert result["empirical_report_eligible_for_human_review"] is False
    assert result["errors"]


def test_relaxed_policy_cannot_be_registered_by_matching_report_hash(evidence):
    root, report = evidence
    policy_path = root / (SEMANTIC + "acceptance.json")
    policy = json.loads(policy_path.read_text())
    policy["min_accuracy"] = 0
    policy_path.write_text(json.dumps(policy))
    report["policy_sha256"] = digest(policy_path)
    report["criteria"] = policy
    result = inspect(evidence)
    assert "unregistered_benchmark_revision" in result["errors"]
    assert result["empirical_report_eligible_for_human_review"] is False
