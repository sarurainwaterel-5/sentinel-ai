# Approved offline presentation-record inspection

Run from `backend`:

```sh
python -m evaluation.governed_answers.inspect_presentation
python -m evaluation.governed_answers.evaluate_readiness
```

The presentation inspector validates the packet-level approval recorded by Rain at `2026-10-12T16:46:19Z`, preserved in commit `4a9dd72`. It checks six exact confirmed scopes, explicit approval/confirmation evidence, reviewer and UTC time, 13 unique worksheet case IDs, and pinned artifact/source hashes for the reviewed static JSON/HTML samples and guard implementation at `2c4a853`.

The six accepted previews and seven withheld cases remain bound to the exact inspected samples. HTML checks verify unique anchor targets, no script elements, exact candidate text and source quotes. A caller cannot renew approval by rewriting expected hashes or injecting arbitrary artifact paths. Paths are fixed and symlink escape is rejected. The approved record's per-case worksheet slots remain null because Rain approved six packet-level checks; no unprovided individual rating/rationale or independent human authorship is invented. Assistant browser visual inspection remains uncompleted; the recorded human confirmation is an attestation, not authenticated browser telemetry.

The original generation artifacts retain `approved=false` as preparation metadata. The distinct human review record is the approval evidence for these static offline fixtures. Neither artifact metadata nor review approval grants production presentation acceptance.

Exit zero from `inspect_presentation` means artifact/content/attestation integrity only. The updated readiness report separately marks `offline_fixture_presentation_review=accepted` and leaves production `rendered_answer_and_citation_acceptance=missing`. It continues to return exit 2 for valid-but-blocked evidence and exit 1 for invalid evidence; there is no production-ready success path. Its schema version is `21-E-offline-readiness-v2`.

All reports fix production presentation acceptance, release authorization, production enablement, empirical acceptance and semantic grounding to false, with proposition-to-inference closed. Inspectors import no providers, runtime modules, browser interfaces or credential configuration. No benchmark or network runs, runtime wiring, old packet/review changes, ADR-037 change, deployment or PR #1 merge is involved. The new presentation validator is checkpoint-specific; later revised artifacts require fresh review/version support.
