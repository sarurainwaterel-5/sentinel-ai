"""Offline evidence inventory for the frozen Sprint 21-E checkpoint.

No providers, environment/credential inspection, benchmark execution or runtime
imports. This diagnostic never grants production or inference authority.
"""
import hashlib
import json
from pathlib import Path

from .inspect_packet import inspect_packet
from .inspect_presentation import ARTIFACT_BINDINGS, SOURCE_BINDINGS, RECORD as PRESENTATION_RECORD, inspect_presentation
from .inspect_review import BINDINGS, COMMIT, FOLDER, PROVENANCE, REVIEW, _load, _text, _utc, inspect_review

ROOT = Path(__file__).resolve().parents[3]
SEMANTIC = "backend/evaluation/semantic_judge/"
GOLD = SEMANTIC + "SentinelAI_Sprint_20_3_G_Human_Approval_Record.json"
DATASET = SEMANTIC + "dataset.json"
POLICY = SEMANTIC + "acceptance.json"
PREFLIGHT = SEMANTIC + "preflight.json"
MANIFEST = FOLDER + "release_manifest.json"


def _gold_valid(record, dataset, dataset_digest):
    if not isinstance(record, dict) or not isinstance(dataset, dict):
        return False
    cases = dataset.get("cases")
    if not isinstance(cases, list) or len(cases) != 36:
        return False
    ids = [case.get("case_id") for case in cases if isinstance(case, dict)]
    if len(ids) != 36 or any(not _text(cid) for cid in ids) or len(set(ids)) != 36:
        return False
    labels = record.get("labels")
    return (record.get("approved") is True
            and _text(record.get("reviewer")) and _utc(record.get("reviewed_at"))
            and record.get("independent_of_candidate_generation_and_judge") is True
            and _text(record.get("approval_evidence"))
            and record.get("dataset_sha256") == dataset_digest
            and isinstance(labels, dict) and set(labels) == set(ids)
            and all(type(value) is bool for value in labels.values())
            and sum(value is True for value in labels.values()) == 18
            and sum(value is False for value in labels.values()) == 18)


def evaluate_readiness(root: Path):
    """Read fixed, bound evidence and report completed and outstanding gates.

No arbitrary gate receipt or path is accepted. Future empirical/integration
artifacts require a new governed checkpoint and evaluator, not a metadata toggle.
"""
    review = inspect_review(root)
    presentation = inspect_presentation(root)
    errors = list(review["errors"])
    errors.extend("presentation:" + error for error in presentation["errors"])
    manifest = _load(root, MANIFEST, errors, BINDINGS[MANIFEST])
    packet_valid = False
    if manifest is not None:
        packet_result = inspect_packet(root, manifest)
        packet_valid = packet_result["packet_integrity"] == "valid"
        errors.extend("packet:" + error for error in packet_result["errors"])
    evidence = {}
    inspected = dict(BINDINGS)
    if manifest is not None:
        for name in (GOLD, DATASET, POLICY, PREFLIGHT):
            expected = manifest["sha256_bindings"][name]
            evidence[name] = _load(root, name, errors, expected)
            inspected[name] = expected
    gold_valid = packet_valid and _gold_valid(
        evidence.get(GOLD), evidence.get(DATASET), inspected.get(DATASET))
    if packet_valid and not gold_valid:
        errors.append("invalid_20_3_gold_review")
    preflight = evidence.get(PREFLIGHT)
    historical_preflight_valid = (packet_valid and isinstance(preflight, dict)
        and preflight.get("execution_source") == "not_executed"
        and preflight.get("trials") == [] and preflight.get("metrics") is None
        and preflight.get("empirical_acceptance") is False
        and preflight.get("dataset_sha256") == inspected.get(DATASET)
        and preflight.get("policy_sha256") == inspected.get(POLICY))
    if packet_valid and not historical_preflight_valid:
        errors.append("invalid_historical_preflight")
    # The frozen checkpoint registers no passing empirical or presentation report.
    # Never follow an injected path or accept an unregistered claimed result.
    if manifest is not None:
        for key in ("empirical_judge_report", "answer_presentation_review"):
            if manifest.get(key) is not None:
                errors.append("unregistered_release_evidence:" + key)
    gates = []

    def gate(identifier, status, description, paths=()):
        gates.append({"gate_id": identifier, "status": status,
                      "description": description, "evidence_paths": list(paths)})

    gate("packet_integrity", "verified" if packet_valid else "invalid",
         "Frozen implementation and review inputs match the original packet hashes.", (MANIFEST,))
    gate("answer_fixture_human_review", "accepted" if review["human_review_approved"] else "invalid",
         "13 reviewed cases; 6 accepts, 6 rejects and 1 admissible-but-withheld statement. Fixture-only review.",
         (REVIEW, PROVENANCE))
    gate("supplemental_criteria", "accepted" if review["human_review_approved"] else "not_validated",
         "Bound supplemental requirements accepted by Rain; no passing measurements claimed.",
         (REVIEW, FOLDER + "answer_acceptance.proposed.json"))
    gate("offline_fixture_presentation_review",
         "accepted" if presentation["offline_fixture_presentation_approved"] else "invalid",
         "Rain approved the exact guarded static fixture packet; this is separate from production presentation acceptance.",
         (PRESENTATION_RECORD, *ARTIFACT_BINDINGS))
    gate("20_3_gold_human_review", "accepted" if gold_valid else "not_validated",
         "Existing 36-case, 18/18 human-label record; separate from empirical judge acceptance.",
         (GOLD, DATASET))
    gate("20_3_empirical_acceptance", "missing",
         "No registered actual-API result. Historical preflight has zero trials and null metrics.",
         (MANIFEST, PREFLIGHT, POLICY))
    gate("20_3_final_acceptance", "missing",
         "Final empirical acceptance review is absent; human label approval does not satisfy it.")
    gate("production_question_and_context_assessment", "not_demonstrated",
         "Fixture relevance/preservation attestations do not establish production question or full-context assessment.")
    gate("authenticated_retrieval_catalog_and_races", "not_implemented_in_checkpoint",
         "The frozen acceptance packet records missing authenticated retrieval/catalog eligibility and update/archive race integration.",
         ("docs/sprints/Sprint-21-E-Acceptance-Packet.md",))
    gate("production_provider_composition_and_budgets", "not_implemented_in_checkpoint",
         "Only offline injected composition exists in the bound checkpoint; production providers/budgets remain outstanding.",
         ("backend/app/services/cognition/reasoning/answer_orchestrator.py",))
    gate("runtime_release_gate_consumption", "not_implemented_in_checkpoint",
         "The original manifest and companion diagnostics are not consumed by runtime answering.",
         (MANIFEST,))
    gate("rendered_answer_and_citation_acceptance", "missing",
         "Approved offline rendered fixtures are separate from missing production answer/citation presentation acceptance.",
         (REVIEW, MANIFEST))
    gate("explicit_production_authorization", "not_authorized",
         "The human record has release_approval=false; no production authorization exists.", (REVIEW,))
    gate("production_code_enablement", "disabled",
         "The pinned answer route and contracts remain literally disabled before retrieval/provider work.",
         ("backend/app/routes/governed_answers.py", "backend/app/services/cognition/reasoning/answer_models.py"))
    # Missing/tampered evidence must not leave apparently trustworthy statements
    # about the bound implementation. Preserve descriptions as checkpoint scope.
    if not packet_valid:
        for item in gates:
            if item["gate_id"] not in {"packet_integrity", "answer_fixture_human_review", "supplemental_criteria"}:
                item["status"] = "not_validated"
    blockers = [item["gate_id"] for item in gates if item["status"] not in {"accepted", "verified"}]
    hashes = {}
    for name in inspected:
        path = root / name
        if path.resolve().is_relative_to(root.resolve()):
            try:
                hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                pass
    for name in (REVIEW, PROVENANCE, PRESENTATION_RECORD, *ARTIFACT_BINDINGS, *SOURCE_BINDINGS):
        path = root / name
        if path.resolve().is_relative_to(root.resolve()):
            try:
                hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                pass
    historical = []
    if review["human_review_approved"]:
        historical.append("The frozen manifest's answer-case/criteria review-pending blocker is historical; the bound approved companion record completes fixture review only.")
    if gold_valid:
        historical.append("The saved preflight's human_review_missing blocker predates the approved 36-case record. It is not a current label-review blocker; no live configuration was inspected.")
    return {"schema_version": "21-E-offline-readiness-v2", "checkpoint_commit": COMMIT,
        "evidence_integrity": "invalid" if errors else "valid",
        "readiness_status": "invalid_evidence" if errors else "blocked",
        "human_review_approved": review["human_review_approved"],
        "offline_fixture_presentation_approved": presentation["offline_fixture_presentation_approved"],
        "production_presentation_accepted": False,
        "gates": gates, "blockers": blockers, "errors": sorted(set(errors)),
        "inspected_sha256": hashes, "historical_evidence_notes": historical,
        "historical_preflight": {"verified_not_executed": historical_preflight_valid,
            "recorded_trials": 0 if historical_preflight_valid else None,
            "metrics": None, "live_configuration_inspected": False},
        "release_authorized": False, "production_enabled": False,
        "semantic_grounding_verified": False, "proposition_to_inference": "closed",
        "empirical_acceptance": False, "benchmark_executed": False,
        "limitation": "Checkpoint-specific offline evidence inventory, not a general release engine. No authenticated identity, source truth, empirical semantic accuracy or runtime authority is established."}


def main():
    report = evaluate_readiness(ROOT)
    print(json.dumps(report, indent=2))
    # Even valid evidence is blocked. Never return a success code implying ready.
    return 1 if report["evidence_integrity"] == "invalid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
