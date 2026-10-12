# Sprint 21-E offline release-readiness inventory

Run from `backend`:

```sh
python -m evaluation.governed_answers.evaluate_readiness
```

The evaluator emits a JSON gate inventory for the frozen packet at `81e2a712ce2788054a8c5e218af1d52f098e6811`, its approved answer review and the previously approved Sprint 20.3-G gold-label record. It distinguishes completed fixture review and criteria acceptance from missing empirical and integration evidence. It reads only fixed paths and hash-bound packet inputs; it does not follow arbitrary report references or scan for receipts.

Current evidence has valid integrity but release readiness is **blocked**. Exit code **2** means a valid-but-blocked checkpoint. Exit code **1** means invalid evidence. Neither means production readiness; there is no production-ready success path in this checkpoint-specific evaluator.

The report includes gate IDs, statuses, evidence paths, SHA-256 values for inspected inputs, blockers, errors and historical-evidence notes. It marks the frozen manifest's pending answer review wording as historical once the approved companion review validates. The saved preflight's missing-human-review wording also predates the already approved 36-case gold-label record. The preflight still has zero trials, null metrics and no empirical acceptance. Its old configuration blockers are not live configuration checks; the evaluator never inspects credentials or environment variables.

Fixture labels, rationale adoption, source support and acceptance criteria do not certify actual judge accuracy, production question relevance, full-context relationship assessment or rendered answer citations. Remaining gates include actual 20.3-G empirical results and final acceptance; authenticated retrieval/catalog/race integration; production provider composition/budgets; runtime gate consumption; rendered answer/citation acceptance; explicit production authorization; and code enablement.

All reports fix `release_authorized=false`, `production_enabled=false`, `semantic_grounding_verified=false`, `empirical_acceptance=false` and `proposition_to_inference=closed`. The evaluator imports no providers or application modules, constructs no clients, executes no benchmark, and is not consumed by the answer route. Frozen packet/review bytes, existing thresholds, ADR-037 and runtime behavior remain unchanged.

This inventory validates content and recorded attestations, not authenticated reviewer identity, source truth or empirical semantic accuracy. Future actual-API or integration evidence requires a newly governed checkpoint and explicit validation support; dropping a passing receipt beside these files or rewriting manifest flags cannot unlock readiness.
