"""Validate Rain's approved offline fixture presentation, never production acceptance.

Fixed artifact/source paths and pinned checkpoint hashes prevent caller metadata
from rebinding the review. No providers, browser, credentials or runtime imports.
"""
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path

from .inspect_review import _load, _text, _utc, inspect_review

ROOT = Path(__file__).resolve().parents[3]
FOLDER = "backend/evaluation/governed_answers/"
RECORD = FOLDER + "presentation_review.offline.approved.json"
FIXTURES = FOLDER + "presentation_fixtures.reviewed.json"
HTML = "docs/sprints/Sprint-21-E-Guarded-Presentation.reviewed.html"
GUARD_COMMIT = "2c4a853b2f88a43b4d1e705ff4d3297bcd78d8bc"
# Recorded review checkpoint, not caller-controlled expected hashes.
SOURCE_BINDINGS = {
    "backend/evaluation/governed_answers/answer_cases.proposed.json": "d5a4391d5108e14894fec3158261d9a91600e5b7b28695138388e29218891ba9",
    "backend/evaluation/governed_answers/answer_review.human.approved.json": "3394b69158b48e0b28db4b25017c64add583f1df8a0ffc6af99edd0ee7337e23",
    "backend/app/services/cognition/reasoning/answer_renderer.py": "cc6f0b9bfbdb605ff3816d377753a75c517cd9f2c4eeb934df2a13ffab60f776",
    "backend/app/services/cognition/reasoning/answer_orchestrator.py": "2a2a6334b68a2cbb16f2092cdf80327ea791300542c7b079ff5656a8eadf4c2d",
    "backend/app/services/cognition/reasoning/answer_models.py": "cb36c55a2c0ae0890a885b2093018d4d652b23a9bc5a2a2ff4c5295def9d2e14",
    "frontend/src/components/answers/GovernedAnswerPanel.jsx": "80bf8db603fc70e764f5217a6bc6d7fa9a56e8b39f7b9b932a0beb5805eeb72c",
    "frontend/src/styles/workspaces.css": "a9061fb74f37849c343107d46d823dcf34027849eac6787077db642bfc4352b6",
    "backend/evaluation/governed_answers/presentation_guard.py": "136e996c2b5ccd19733a1affbb867989acf31336519172449f98f750a5a7fce0"
}
ARTIFACT_BINDINGS = {
    "backend/evaluation/governed_answers/presentation_fixtures.reviewed.json": "bc58d64c32a8cd3cf44d62d4b4cbbe184140213670f9d264cba8e55bad666cdc",
    "docs/sprints/Sprint-21-E-Guarded-Presentation.reviewed.html": "04a7c92570493316230088cf5435ec0a2b44734b2df6de9e705f2b5c3d1c642a"
}
CHECK_SCOPES = {
    "accepted_preview_text": "Six accepted previews retain the exact statements.",
    "citation_targets_and_quotes": "Citation links lead to complete, correctly attributed source quotes.",
    "qualifications_conflicts_uncertainty": "Conditions, opposing reports, and uncertainty remain visible.",
    "rejected_and_irrelevant_withheld": "Six rejected cases and the irrelevant case show no synthesis preview.",
    "failed_and_malformed_withheld": "Failed relevance assessments and malformed samples remain withheld.",
    "offline_disabled_scope_clear": "Offline status, production-disabled labeling, and limits are clear."
}


class _HTMLInventory(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []
        self.text = []
        self.scripts = 0

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag == "a":
            self.links.append(attributes.get("href"))
        if tag == "script":
            self.scripts += 1

    def handle_data(self, text):
        self.text.append(text)


def _bound_bytes(root, name, digest, errors):
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()):
        errors.append("unsafe_path:" + name)
        return None
    try:
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            errors.append("changed_binding:" + name)
            return None
        return data
    except OSError:
        errors.append("missing_binding:" + name)
        return None


def inspect_presentation(root: Path, record=None):
    """Validate this approved packet-level attestation and exact review samples."""
    errors = []
    answer_review = inspect_review(root)
    if not answer_review["human_review_approved"]:
        errors.extend("answer_review:" + error for error in answer_review["errors"])
    for name, digest in SOURCE_BINDINGS.items():
        _bound_bytes(root, name, digest, errors)
    fixtures = _load(root, FIXTURES, errors, ARTIFACT_BINDINGS[FIXTURES])
    html = _bound_bytes(root, HTML, ARTIFACT_BINDINGS[HTML], errors)
    if record is None:
        record = _load(root, RECORD, errors)
    expected_ids = set()
    if fixtures:
        expected_ids = {case["case_id"] for case in fixtures["cases"]}
    if not isinstance(record, dict):
        errors.append("invalid_presentation_record")
    else:
        if record.get("version") != "21-E-guarded-presentation-review-v1" or record.get("guard_implementation_commit") != GUARD_COMMIT:
            errors.append("invalid_presentation_checkpoint")
        if record.get("approved") is not True:
            errors.append("offline_presentation_unapproved")
        for key in ("release_approval", "production_presentation_accepted", "production_enabled", "empirical_acceptance"):
            if record.get(key) is not False:
                errors.append("invalid_authority:" + key)
        for key in ("release_authorized", "semantic_grounding_verified"):
            if key in record and record[key] is not False:
                errors.append("invalid_authority:" + key)
        if "proposition_to_inference" in record and record["proposition_to_inference"] != "closed":
            errors.append("invalid_authority:proposition_to_inference")
        reviewer = record.get("reviewer")
        if not _text(reviewer) or not _utc(record.get("reviewed_at")):
            errors.append("missing_reviewer_or_utc_time")
        approval = record.get("approval_evidence")
        if not isinstance(approval, dict) or approval.get("reviewer") != reviewer or approval.get("human_response") != "yes" or approval.get("recorded_at") != record.get("reviewed_at") or not _text(approval.get("context")) or not _text(approval.get("timestamp_basis")):
            errors.append("invalid_explicit_approval_evidence")
        confirmation = record.get("confirmation_evidence")
        if not isinstance(confirmation, dict) or confirmation.get("reviewer") != reviewer or confirmation.get("human_response") != "yes confirm" or not _text(confirmation.get("context")):
            errors.append("invalid_presentation_confirmation")
        checks = record.get("packet_assessments")
        if not isinstance(checks, dict) or set(checks) != set(CHECK_SCOPES) or any(
                not isinstance(checks.get(key), dict) or checks[key].get("confirmed") is not True or checks[key].get("scope") != scope
                for key, scope in CHECK_SCOPES.items()):
            errors.append("incomplete_or_changed_presentation_checks")
        if record.get("source_bindings") != SOURCE_BINDINGS:
            errors.append("invalid_source_bindings")
        if record.get("reviewed_artifact_paths") != {"fixtures": FIXTURES, "html": HTML} or record.get("fixture_packet_sha256") != ARTIFACT_BINDINGS[FIXTURES] or record.get("html_sha256") != ARTIFACT_BINDINGS[HTML]:
            errors.append("invalid_reviewed_artifact_bindings")
        if not _text(record.get("assessment_scope")) or not _text(record.get("approval_limitation")):
            errors.append("missing_offline_scope")
        browser = record.get("browser_visual_inspection")
        if not isinstance(browser, dict) or browser.get("assistant_completed") is not False or not _text(browser.get("human_confirmation")):
            errors.append("misattributed_browser_inspection")
        cases = record.get("case_reviews")
        ids = []
        if not isinstance(cases, list):
            errors.append("invalid_case_worksheet")
            cases = []
        for case in cases:
            if not isinstance(case, dict) or not _text(case.get("case_id")):
                errors.append("invalid_case_worksheet_entry")
                continue
            ids.append(case["case_id"])
            if any(value is not None for key, value in case.items() if key != "case_id"):
                errors.append("unprovided_case_rating_or_rationale:" + case["case_id"])
        if len(ids) != 13 or len(set(ids)) != 13 or set(ids) != expected_ids:
            errors.append("incomplete_presentation_case_coverage")
    counts = {"accepted_previews": 0, "withheld_cases": 0}
    if fixtures:
        # Exact artifact bytes are pinned; these checks explain their contents.
        if fixtures.get("source_bindings") != SOURCE_BINDINGS:
            errors.append("invalid_fixture_source_bindings")
        for case in fixtures["cases"]:
            preview = case["report"].get("fixture_claim")
            expected = case["human_classification"] == "accept"
            if bool(preview) != expected:
                errors.append("unexpected_fixture_preview:" + case["case_id"])
            counts["accepted_previews" if preview else "withheld_cases"] += 1
            public = case["report"]["public_response"]
            guard = case["report"]["presentation_guard"]
            if public.get("answer_text") is not None or public.get("claims") != [] or guard.get("production_enabled") is not False or guard.get("release_authorized") is not False:
                errors.append("fixture_authority_violation:" + case["case_id"])
        if counts != {"accepted_previews": 6, "withheld_cases": 7}:
            errors.append("unexpected_presentation_counts")
    if html is not None:
        inventory = _HTMLInventory()
        inventory.feed(html.decode("utf-8"))
        if inventory.scripts or len(inventory.ids) != len(set(inventory.ids)) or any(
                not isinstance(link, str) or not link.startswith("#") or link[1:] not in inventory.ids
                for link in inventory.links):
            errors.append("invalid_static_html_inventory")
        if fixtures:
            text = "\n".join(inventory.text)
            for case in fixtures["cases"]:
                for source in case["report"]["public_response"]["evidence"]:
                    if source["text"] not in text:
                        errors.append("missing_exact_source_quote:" + case["case_id"])
                claim = case["report"].get("fixture_claim")
                if claim and claim["statement"] not in text:
                    errors.append("changed_preview_text:" + case["case_id"])
    return {"schema_version": "21-E-offline-presentation-inspection-v1",
            "presentation_integrity": "invalid" if errors else "valid",
            "offline_fixture_presentation_approved": not errors,
            "errors": sorted(set(errors)), "observed_counts": counts,
            "production_presentation_accepted": False,
            "release_authorized": False, "production_enabled": False,
            "semantic_grounding_verified": False, "empirical_acceptance": False,
            "proposition_to_inference": "closed",
            "assistant_browser_visual_inspection_completed": False,
            "limitation": "Pinned static artifact/content and recorded human-attestation checks only. No authenticated identity, real-provider relevance accuracy, browser telemetry, production presentation acceptance or release authority."}


def main():
    report = inspect_presentation(ROOT)
    print(json.dumps(report, indent=2))
    return 0 if report["presentation_integrity"] == "valid" else 1


if __name__ == "__main__":
    raise SystemExit(main())
