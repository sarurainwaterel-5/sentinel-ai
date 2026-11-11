"""Astra v1 report consistency diagnostic; never authenticates API execution."""
import hashlib
import json
import math
from pathlib import Path
import random

from app.services.cognition.reasoning.release_gate import FROZEN_INPUTS, _bound_path, _time, _unique_object
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticJudgeVerdict
from app.services.cognition.reasoning.statement_admissibility_validator import StatementAdmissibilityResult
from app.services.providers.openai_reasoning_admissibility import OpenAIReasoningAdmissibilityProvider
from evaluation.semantic_judge.astra_runner import CONFIG, ROLES
from evaluation.semantic_judge.runner import digest, load_inputs, summarize

SEMANTIC = "backend/evaluation/semantic_judge/"
REVIEW = SEMANTIC + "SentinelAI_Sprint_20_3_G_Human_Approval_Record.json"
SELECTION = "docs/governance/sprint21-model-selection.json"
FILES = {
    "dataset_sha256": SEMANTIC + "dataset.json",
    "policy_sha256": SEMANTIC + "acceptance.json",
    "review_sha256": REVIEW,
    "runner_sha256": SEMANTIC + "astra_runner.py",
    "adapter_sha256": "backend/app/services/providers/openai_reasoning_admissibility.py",
    "legacy_runner_sha256": SEMANTIC + "runner.py",
    "legacy_adapter_sha256": "backend/app/services/providers/openai_semantic_admissibility.py",
    "model_selection_sha256": SELECTION,
}


def _read(path):
    with path.open("rb") as stream:
        raw = stream.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise ValueError("oversized_evidence")
    return json.loads(raw, object_pairs_hook=_unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite_json")))


def inspect_astra_report(root, report_path=None):
    """Recompute all 108 trials and bindings; eligibility only permits human review."""
    root = Path(root)
    errors, metrics = [], None
    if report_path is None:
        errors.append("astra_report_missing")
    else:
        try:
            report = _read(_bound_path(root, report_path))
            paths = {key: _bound_path(root, name) for key, name in FILES.items()}
            bindings = {key: digest(path) for key, path in paths.items()}
            if any(bindings[key] != value for key, value in FROZEN_INPUTS.items()):
                errors.append("unregistered_benchmark_revision")
            bindings.update(
                prompt_sha256=hashlib.sha256(OpenAIReasoningAdmissibilityProvider.system_message().encode()).hexdigest(),
                verdict_schema_sha256=hashlib.sha256(json.dumps(SemanticJudgeVerdict.model_json_schema(), sort_keys=True).encode()).hexdigest())
            if not isinstance(report, dict) or any(report.get(key) != value for key, value in bindings.items()):
                raise ValueError("astra_binding_mismatch")
            selection = _read(paths["model_selection_sha256"])
            benchmark = selection.get("benchmark", {})
            expected = dict(model=CONFIG["model"], reasoning_effort=CONFIG["reasoning_effort"],
                            max_completion_tokens=CONFIG["max_completion_tokens"], timeout_seconds=CONFIG["timeout"],
                            max_retries=0, sampling_parameters="omitted", expected_cases=36,
                            repetitions=3, planned_calls=108, order_seed=203)
            if (selection.get("version") != "sprint21-model-selection-v1"
                    or selection.get("model_selection_confirmed") is not True
                    or selection.get("roles") != ROLES
                    or selection.get("reasoning_efforts") != {"generation": "low", "semantic_judge": "low", "relevance": "none"}
                    or not isinstance(benchmark, dict)
                    or benchmark.get("version") != "astra-semantic-benchmark-v1"
                    or any(type(benchmark.get(key)) is not type(value) or benchmark[key] != value for key, value in expected.items())
                    or benchmark.get("frozen_input_sha256") != {Path(FILES[key]).name: value for key, value in FROZEN_INPUTS.items()}):
                errors.append("model_selection_config_mismatch")
            cases, policy, labels, blockers = load_inputs(paths["dataset_sha256"], paths["policy_sha256"], paths["review_sha256"])
            errors.extend(blockers)
            if (report.get("version") != "astra-benchmark-v1" or report.get("execution_source") != "actual_api"
                    or report.get("provider") != "OpenAI" or report.get("model") != CONFIG["model"]
                    or json.dumps(report.get("provider_config"), sort_keys=True) != json.dumps(CONFIG, sort_keys=True)
                    or report.get("selected_roles") != ROLES
                    or report.get("criteria") != policy or type(report.get("dataset_size")) is not int
                    or report.get("dataset_size") != 36 or type(report.get("planned_calls")) is not int
                    or report.get("planned_calls") != 108 or type(report.get("executed_calls")) is not int
                    or report.get("executed_calls") != 108 or report.get("blockers") != []):
                errors.append("invalid_astra_execution_metadata")
            for key in ("openai_sdk_version", "python", "commit"):
                if not isinstance(report.get(key), str) or not report[key].strip():
                    errors.append("missing_astra_identity:" + key)
            if _time(report.get("finished_at")) < _time(report.get("started_at")):
                errors.append("invalid_report_timestamp")
            expected_order = []
            for repetition in range(policy["repetitions"]):
                ordered = list(cases)
                random.Random(policy["order_seed"] + repetition).shuffle(ordered)
                expected_order.extend((case["case_id"], repetition) for case in ordered)
            rows = report.get("trials")
            if type(rows) is not list or len(rows) != 108:
                raise ValueError("incomplete_astra_trials")
            for row, identity in zip(rows, expected_order):
                if (type(row) is not dict or type(row.get("case_id")) is not str
                        or type(row.get("repetition")) is not int
                        or (row["case_id"], row["repetition"]) != identity
                        or type(row.get("admissible")) is not bool or type(row.get("operational_error")) is not bool
                        or row.get("scope") != "independent_model_semantic_admissibility"
                        or type(row.get("rejection_reasons")) is not list
                        or not all(type(reason) is str for reason in row["rejection_reasons"])
                        or len(row["rejection_reasons"]) > 17
                        or len(set(row["rejection_reasons"])) != len(row["rejection_reasons"])
                        or type(row.get("elapsed_seconds")) not in (int, float)
                        or not math.isfinite(row["elapsed_seconds"]) or row["elapsed_seconds"] < 0):
                    raise ValueError("malformed_astra_trial")
                StatementAdmissibilityResult(admissible=row["admissible"], rejection_reasons=tuple(row["rejection_reasons"]), validation_scope=row["scope"])
                if (row["operational_error"] != any(reason.startswith("semantic_judge_") for reason in row["rejection_reasons"])
                        or row["admissible"] != (not row["rejection_reasons"])):
                    raise ValueError("inconsistent_astra_trial")
            if labels is not None:
                metrics = summarize(cases, labels, rows, policy)
                # JSON byte comparison distinguishes true/1 and other loose equality.
                if json.dumps(report.get("metrics"), sort_keys=True) != json.dumps(metrics, sort_keys=True):
                    errors.append("astra_metrics_mismatch")
                if metrics["criteria_passed"] is not True:
                    errors.append("astra_criteria_failed")
            if report.get("status") != "passed" or report.get("empirical_acceptance") is not True:
                errors.append("astra_report_not_passing")
        except (OSError, ValueError, TypeError, KeyError, AttributeError, OverflowError, RecursionError):
            errors.append("invalid_astra_evidence")
    return dict(schema_version="astra-report-consistency-v1", status="disabled", enabled=False,
                production_enabled=False, release_authorized=False, semantic_grounding_verified=False,
                proposition_to_inference="closed", empirical_report_eligible_for_human_review=not errors and metrics is not None,
                recomputed_empirical_metrics=metrics, errors=sorted(set(errors)),
                blockers=sorted(set(errors + ["empirical_execution_provenance_and_final_human_review_required",
                    "independent_provider_deployment_review_required", "explicit_production_release_authorization_required"])),
                limitation="Report consistency does not authenticate API execution, model independence or human acceptance.")
