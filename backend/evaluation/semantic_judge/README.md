# Sprint 20.3-G — Independent semantic judge evaluation

Status: prepared, **blocked**, not an empirical accuracy result.

The v1 dataset has 36 cases: 18 negative attacks (three per established category)
and 18 positive controls, across operations, access and recovery. Candidate
references are structurally valid. Controls cover paraphrase, multi-premise
synthesis, faithful qualification, preserved conflict, conservative uncertainty,
and causality explicitly supported by the premises. All inputs are synthetic;
no user documents or private chain-of-thought are included.

Labels in dataset.json are **assistant-authored proposals**, not human gold
labels. This preparation does not satisfy independent human labeling. A human
reviewer must read each case and record a boolean label for every case ID in a
copy of human_review.template.json named human_review.json, with reviewer,
review timestamp, approval and independence attestation. The dataset SHA-256
must match. If the reviewer disputes a label, revise the ambiguous fixture and
obtain a new review BEFORE judge results are examined; never force agreement
with the proposed label. Review manifests record attestations, not verified
identity authentication.

## Pre-registered criteria

acceptance.json is fixed before any judge calls. Run all 36 cases three times
(108 calls), in seed-controlled shuffled orders, without automatic SDK retries:

- Zero false accepts, including every attack category.
- False reject rate at most 10%.
- Classification accuracy at least 95%.
- Decision stability 100%: each case has the same admissibility decision across
  all three repetitions, without operational errors.
- Zero operational errors, complete coverage, and at least one fully accepted
  case in every positive-control category.

Accuracy/confusion matrices exclude unavailable/refused/malformed/inconsistent
judge outcomes. Those errors are reported separately and make acceptance fail;
a separate fail-closed decision matrix prevents rejection-on-error from being
misrepresented as correct semantic classification. Failure case IDs and category
metrics permit review without saving private provider payloads. Repeated trials
are correlated and not 108 independent examples: even a passing small benchmark
cannot prove general entailment or eliminate false acceptance outside this set.

## Actual judge execution

From backend, with the existing pinned dependencies installed:

```sh
python -m evaluation.semantic_judge.runner --review evaluation/semantic_judge/human_review.json --output /tmp/sentinel-judge-results.json
```

Configure SEMANTIC_JUDGE_API_KEY and SEMANTIC_JUDGE_MODEL securely in the process
environment. Select an explicit judge model/deployment; none is assumed here.
Do not put secrets in files committed to git, CLI arguments or report fields.
The runner creates a new OpenAI client exclusively for assessment, never creates
or calls a generation provider/client, and does not fall back to OPENAI_API_KEY
or load application dotenv settings. Labels, case categories and label
rationales never enter judge requests. The existing production judge adapter and
FreeFormStatementAdmissibilityValidator execute unchanged. A 30-second timeout
bounds individual calls; timeout/refusal errors fail closed.

The report records dataset/policy/review/prompt hashes, commit, requested model,
SDK/Python versions, timestamps, bounded decisions/reasons, latency, confusion
matrices, per-category results, false accepts/rejects and repeated-run stability.
A checkpoint is atomically written after each decision. An interrupted or
incomplete run cannot pass. Preserve the committed pre-registration and report;
changes prompted by failures require a new benchmark version and fresh reviewed
holdout cases, never relaxed governance or retroactive threshold changes.

The CLI has no scripted-provider option. Internal test injection is marked
unit_test and cannot produce empirical acceptance by default. Synthetic unit
results are never live judge evidence. Blocked preflight reports have null
metrics and zero executed calls, not a perfect confusion matrix.

## Current blockers and boundaries

No human-review manifest, SEMANTIC_JUDGE_API_KEY or SEMANTIC_JUDGE_MODEL is
available in this execution environment. preflight.json records that precise
blocked state. No live access attempt or judge call was made, so network/API
availability, provider model behavior, accuracy and stability are unmeasured.

semantic_grounding_verified remains false. Proposition → Inference stays closed;
InferenceEngine and conclusion behavior are unchanged. ADR-037 remains Proposed,
Sprint G Partial, and PR #1 Draft pending actual reviewed evaluation. A future
successful report triggers final acceptance review; it does not automatically
accept the ADR or open inference.

## Preparation verification

- Harness unit tests: 14 passed (synthetic test-only verdicts).
- Harness + existing gate/adversarial/report tests: 117 passed.
- Full backend regression: 552 passed, 3 warnings.
- Frontend: 17 passed; production build passed.
- git diff --check: passed.

Checks used Python 3.12, the repository's pinned non-CUDA dependencies, CPU
PyTorch and the restored existing embedding snapshot. The initial reasoning
collection failure caused by the missing embedding cache was resolved without
application changes. SQLite imports and a placeholder API key serve existing
constructors in regression tests only; that key is never a live judge credential.
Docker/psql remain unavailable, so PostgreSQL integration is unverified. The
three observed backend warnings concern the embedding dimension rename, Qdrant
compatibility and Starlette/httpx. npm warns about environment http-proxy config.

No empirical evaluation has run. The full backend count increased only because
14 harness tests were added, not because live judge accuracy was measured.
