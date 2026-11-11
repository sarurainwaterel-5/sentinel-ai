"""Current runtime denial gate and empirical evidence diagnostic.

Evidence can qualify for human review; it never authorizes production. A JSON
report is not authenticated proof that API calls happened. No client is created.
The frozen Sprint 21-E inventory remains an independent historical artifact.
"""
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import random


SEMANTIC = "backend/evaluation/semantic_judge/"
REVIEW = SEMANTIC + "SentinelAI_Sprint_20_3_G_Human_Approval_Record.json"
FROZEN_INPUTS = {
    "dataset_sha256": "d57de823b86797a6b25ff36a808c678cc8843ef5a1b4d7188576f27fe0cc7adb",
    "policy_sha256": "4847ef02ffe88b3747944eb736fbd79c7e46518297f9c819877fd910ce497288",
    "review_sha256": "e4fe2bcf4f202e18fc12fd41801b36872629b43462e7dc266841900f48cf1917",
}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _bound_path(root, name):
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("evidence_path_outside_repository")
    return path


def _time(value):
    if not isinstance(value, str):
        raise ValueError("invalid_report_timestamp")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("invalid_report_timestamp")
    return result


def inspect_release_gate(root: Path, empirical_report: Path | None = None):
    """Deny release and optionally recompute a contained empirical report.

The path is explicit and confined to the repository. Failures expose bounded
codes, never provider payloads, filesystem contents, credentials or exceptions.
"""
    root = Path(root)
    errors = []
    metrics = None
    eligible = False
    if empirical_report is None:
        errors.append("empirical_report_missing")
    else:
        try:
            from evaluation.semantic_judge.runner import load_inputs, summarize
            from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticJudgeVerdict
            from app.services.providers.openai_semantic_admissibility import OpenAISemanticAdmissibilityProvider
            from app.services.cognition.reasoning.statement_admissibility_validator import StatementAdmissibilityResult

            report_path = _bound_path(root, empirical_report)
            with report_path.open("rb") as stream:
                raw = stream.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise ValueError("oversized_empirical_report")
            report = json.loads(raw, object_pairs_hook=_unique_object)
            dataset = _bound_path(root, SEMANTIC + "dataset.json")
            policy_path = _bound_path(root, SEMANTIC + "acceptance.json")
            review = _bound_path(root, REVIEW)
            cases, policy, labels, blockers = load_inputs(dataset, policy_path, review)
            errors.extend(blockers)
            if not isinstance(report, dict):
                raise ValueError("invalid_report")
            bindings = {
                "dataset_sha256": _digest(dataset),
                "policy_sha256": _digest(policy_path),
                "review_sha256": _digest(review),
                "runner_sha256": _digest(_bound_path(root, SEMANTIC + "runner.py")),
                "prompt_sha256": hashlib.sha256(OpenAISemanticAdmissibilityProvider.system_message().encode()).hexdigest(),
                "verdict_schema_sha256": hashlib.sha256(json.dumps(SemanticJudgeVerdict.model_json_schema(), sort_keys=True).encode()).hexdigest(),
            }
            if any(report.get(key) != value for key, value in bindings.items()):
                errors.append("empirical_binding_mismatch")
            if any(bindings[key] != value for key, value in FROZEN_INPUTS.items()):
                errors.append("unregistered_benchmark_revision")
            if (report.get("execution_source") != "actual_api"
                    or report.get("provider") != "OpenAI"
                    or report.get("criteria") != policy
                    or report.get("dataset_size") != len(cases)
                    or report.get("planned_calls") != len(cases) * policy["repetitions"]
                    or report.get("blockers") != []):
                errors.append("invalid_empirical_execution_metadata")
            for key in ("model", "openai_sdk_version", "python", "commit"):
                if not isinstance(report.get(key), str) or not report[key].strip():
                    errors.append("missing_empirical_identity:" + key)
            if _time(report.get("finished_at")) < _time(report.get("started_at")):
                errors.append("invalid_report_timestamp")
            rows = report.get("trials")
            expected = {(c["case_id"], repetition) for c in cases for repetition in range(policy["repetitions"])}
            observed = set()
            expected_order = []
            for repetition in range(policy["repetitions"]):
                ordered = list(cases)
                random.Random(policy["order_seed"] + repetition).shuffle(ordered)
                expected_order.extend((case["case_id"], repetition) for case in ordered)
            if not isinstance(rows, list) or len(rows) != len(expected):
                raise ValueError("incomplete_empirical_trials")
            for index, row in enumerate(rows):
                if (not isinstance(row, dict) or type(row.get("repetition")) is not int
                        or type(row.get("admissible")) is not bool
                        or type(row.get("operational_error")) is not bool
                        or not isinstance(row.get("rejection_reasons"), list)
                        or not all(isinstance(reason, str) for reason in row["rejection_reasons"])
                        or not isinstance(row.get("case_id"), str)
                        or not isinstance(row.get("scope"), str)):
                    raise ValueError("malformed_empirical_trial")
                if (row["scope"] != "independent_model_semantic_admissibility"
                        or len(row["rejection_reasons"]) > 17
                        or len(set(row["rejection_reasons"])) != len(row["rejection_reasons"])
                        or type(row.get("elapsed_seconds")) not in (int, float)
                        or not math.isfinite(row["elapsed_seconds"]) or row["elapsed_seconds"] < 0):
                    raise ValueError("invalid_empirical_trial_record")
                StatementAdmissibilityResult(admissible=row["admissible"],
                    rejection_reasons=tuple(row["rejection_reasons"]), validation_scope=row["scope"])
                identity = (row["case_id"], row["repetition"])
                if identity not in expected or identity in observed or identity != expected_order[index]:
                    raise ValueError("invalid_empirical_trial_coverage")
                observed.add(identity)
                if row["operational_error"] != any(r.startswith("semantic_judge_") for r in row["rejection_reasons"]):
                    raise ValueError("inconsistent_operational_error")
                if row["admissible"] != (not row["rejection_reasons"]):
                    raise ValueError("inconsistent_trial_decision")
            if labels is not None:
                metrics = summarize(cases, labels, rows, policy)
                if report.get("metrics") != metrics:
                    errors.append("empirical_metrics_mismatch")
                if metrics["criteria_passed"] is not True:
                    errors.append("empirical_criteria_failed")
            if report.get("status") != "passed" or report.get("empirical_acceptance") is not True:
                errors.append("empirical_report_not_passing")
            eligible = not errors and metrics is not None
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
            errors.append("invalid_empirical_evidence")
    blockers = list(errors) + [
        "independent_provider_deployment_review_required",
        "empirical_execution_provenance_and_final_human_review_required",
        "authenticated_retrieval_integration_acceptance_required",
        "production_question_and_full_context_acceptance_required",
        "production_answer_and_citation_presentation_acceptance_required",
        "explicit_production_release_authorization_required",
    ]
    return {"schema_version": "21-runtime-denial-v1", "status": "disabled",
            "enabled": False, "production_enabled": False, "release_authorized": False,
            "semantic_grounding_verified": False, "proposition_to_inference": "closed",
            "empirical_report_eligible_for_human_review": eligible,
            "recomputed_empirical_metrics": metrics, "errors": sorted(set(errors)),
            "blockers": sorted(set(blockers)),
            "limitation": "Report consistency is not authenticated API execution or human acceptance."}
