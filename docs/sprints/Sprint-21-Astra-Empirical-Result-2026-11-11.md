# Astra empirical evaluation — 2026-11-11

**The first actual Astra run met every preregistered benchmark threshold.**
Final human acceptance is pending. Production answering remains disabled,
semantic grounding remains unverified and proposition-to-inference stays closed.

## Exact run

- Run source commit: `93724732d722f652c0811c62482d91e7838f6fa5`.
- Requested model: `gpt-6-astra`, reasoning `low`, 4,096 maximum completion
  tokens, 30-second individual timeout, zero SDK retries, no sampling parameters.
- Dedicated judge credential was loaded privately from the user-specified local
  file and was distinct from the general application credential. No credential
  value is in source, the report, terminal output or this record.
- Existing approved 36-case dataset, labels and acceptance policy were unchanged.
  All cases ran three times in the preregistered seed-203 shuffled orders.
- Actual run: 2026-11-11 17:12:51–17:17:48 UTC (11:12–11:17 Central).
- No generation model/client was constructed or called; no automatic retry,
  fallback, case substitution or threshold adjustment occurred.

Exact report:
[`astra-20261111-run1.json`](../../backend/evaluation/semantic_judge/results/astra-20261111-run1.json)

Report SHA-256:
`922844683321ebf816cc56d40c701dd0f002e3b902a7aa25f5ed8446fc860d32`.
The original operator-output copy is preserved outside the checkout in the
workspace's `outputs/sprint21-integration/` directory; its bytes match this copy.

## Measurements

| Measurement | Observed | Required |
|---|---:|---:|
| Recorded assessments | 108 / 108 | Complete |
| Classification accuracy | 100% | At least 95% |
| Correct accepts | 54 | Positive controls covered |
| Correct rejects | 54 | Attack categories covered |
| False accepts | 0 | 0 |
| False rejects | 0 | At most 10% of positives |
| Operational errors | 0 | 0 |
| Stable case decisions | 36 / 36, 100% | 100% |
| Positive category coverage | All 6 categories | All 6 |

All six negative categories were rejected in every trial, and all six positive
categories were accepted in every trial. Classification coverage was 100%.
Rejection-reason sets were stable for 35 of 36 cases (97.22%). For
`recovery-certainty_inflation`, the third repetition additionally reported
`unsupported_fact`; all three repetitions rejected the candidate. The fixed
policy requires decision stability, not identical reason-code sets. This variation
is retained in the exact report and is not hidden or counted as a different decision.

## Validation and scope

Root and a separate review agent independently verified all 108 unique
case/repetition pairs, 36 cases with three trials each, exact shuffled order,
source/input/selection/configuration hashes, strict trial types and all recomputed
metrics. `inspect_astra_report` returned no errors and qualified the report for
human review. Its production and release flags remain false.

[`astra-20261111-run1.audit.json`](../../backend/evaluation/semantic_judge/results/astra-20261111-run1.audit.json)
records the diagnostic. This is automated evidence validation, not a human
acceptance signature or cryptographic proof of provider execution. The operator
observed the actual SDK run; the JSON report alone cannot authenticate provenance.

These are 36 synthetic, human-reviewed cases repeated three times, not 108
independent unseen examples. Success does not prove general entailment, source
truth, model independence or future performance. The report records a requested
model alias; a provider-resolved snapshot ID and token usage were not retained.
It does not evaluate Sol generation, Terra relevance/context assessment, real
document retrieval, vector index correctness, runtime citations or deployed UI.

## Pending acceptance

[`astra-20261111-run1.review.pending.json`](../../backend/evaluation/semantic_judge/results/astra-20261111-run1.review.pending.json)
binds the exact report hash, run commit and configuration. Reviewer and timestamp
are unset; approval fields remain false. Review the measured results, execution
provenance, deployment independence and limited scope before recording final
empirical acceptance. This record cannot authorize production release.

The frozen legacy acceptance packet, labels, policies, runner, adapter, ADR-037,
inference behavior, application database and production service configuration
were not changed by this evaluation. The historical 21-E evaluator remains a
checkpoint inventory; its missing-empirical statement is not retroactively edited.

The current sprint still requires application catalog/index/retrieval integration,
actual generation/relevance/provider composition, runtime answer/citation and
presentation acceptance, final empirical review and bound release authorization.
