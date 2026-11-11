# Sprint 21 release integration and acceptance audit

This audit separates implemented offline contracts from demonstrated runtime
behavior and human release acceptance. Sprint 21 is open. Production answering
remains disabled and ADR-037 remains Proposed; the Proposition → Inference
boundary stays closed.

## Actual independent semantic benchmark

The saved approved gold record already contains all 36 reviewed labels. The
semantic benchmark README's historical statement that human labeling is absent
predates that record. Do not regenerate or overwrite its approval.

From `backend`, with pinned dependencies installed and a dedicated, securely
configured `SEMANTIC_JUDGE_API_KEY` and explicit `SEMANTIC_JUDGE_MODEL` in the
process environment:

```sh
python -m evaluation.semantic_judge.runner \
  --review evaluation/semantic_judge/SentinelAI_Sprint_20_3_G_Human_Approval_Record.json \
  --output /tmp/sentinel-judge-results.json
```

The command performs 108 actual API calls: 36 cases, three seed-shuffled
repetitions, 30-second individual timeout, zero SDK retries. No generation client
is created. It does not load application dotenv or fall back to `OPENAI_API_KEY`.
Missing configuration produces a blocked report with zero trials and null
metrics. A successful small synthetic benchmark does not prove source truth or
general entailment. If it fails, preserve the result; improvements require fresh
reviewed holdout cases and a versioned benchmark, without relaxing thresholds.

Before execution, record the requested judge deployment separately from the
generation and question/full-context assessment deployment. Separate Python
objects or keys do not establish model independence. Record provider/model
identity, deployment, prompts, isolation, budgets and the independence review.
Credentials are never part of review evidence or repository artifacts.

## Runtime gate diagnostic

`app.services.cognition.reasoning.release_gate.inspect_release_gate` is a current
runtime denial gate, separate from the immutable Sprint 21-E historical inventory.
It creates no client and always returns `enabled=false`,
`release_authorized=false`, `semantic_grounding_verified=false`, and a closed
inference boundary. Without a report it does no benchmark imports or execution.

An explicitly supplied report must be inside the repository, including after
symlink resolution. Copy a result from `/tmp` to a private, untracked repository
location before inspection. Never include keys or raw provider payloads. The gate
checks current dataset, policy, approved review, runner, prompt and schema hashes;
execution metadata; timestamps; exact pre-registered shuffled trial coverage;
decision/error structure; and recomputed full metrics. Changing only a `passed`
or `empirical_acceptance` boolean cannot qualify a report.

Even a report that passes these checks is only eligible for human review. JSON
consistency and hashes cannot authenticate that API calls occurred. A forged
internally consistent report remains unable to authorize production. The
diagnostic intentionally has no mechanism for arbitrary approval receipts to
unlock release.

## Evidence still needed for sprint acceptance

The unregistered `isolated_acceptance_app.create_isolated_acceptance_app` factory
consumes the denial gate before its answer path performs catalog or provider
work. Its source-inspection path exercises a disposable relational catalog and
credential/grant store, rechecking authority and lifecycle state before returning
bytes. These isolated HTTP/SQLite checks are integration evidence for that harness;
they do not wire the deployed production route, authorize source bytes as governed
evidence, demonstrate PostgreSQL behavior, or satisfy live answer acceptance.

| Gate | Evidence required |
| --- | --- |
| Storage integration | Isolated real database migration up/down, document/version/tombstone behavior, transactional outbox rollback, update/archive/revocation race outcomes, and runtime index/retrieval integration. SQLite-only results cannot attest PostgreSQL behavior. |
| Authenticated retrieval | Trusted session identity mapped to principal grants; server-enforced tenant/document scopes; final rechecks after async/provider work; revocation and lifecycle race demonstrations. Caller-supplied identity is not authentication. |
| Providers and budgets | Real independently configured generation, semantic assessment, question and full-context review; fail-closed timeout/refusal/malformed behavior; enforced request/call/token/time budgets. |
| Empirical judge | Actual 108-call report and reviewed execution provenance; frozen thresholds met without operational errors; final human acceptance of the measured limitations. |
| Answer quality | Governed answer run covering all six positive categories and fail-closed cases; zero unsupported published claims, wrong/missing citations, suppressed conflicts, out-of-scope disclosures, or false enabled states; question/context review evidence. |
| Production presentation | Human inspection of exact runtime answer text, qualifications, uncertainty, conflicts, status and source links in the rendered UI, including rejected/withheld/error states. Static fixture approval does not approve runtime output. |
| Release | Bound final integration/empirical/presentation evidence, reviewed implementation, explicit production authorization, and a separately reviewed mechanism for deployed runtime consumption. The isolated app currently consumes denial only. |

The human-only steps are empirical final acceptance, independence assessment,
rendered production presentation acceptance and explicit release authorization.
An implementation agent may prepare exact review artifacts, but must not sign
these on the user's behalf or reinterpret broad implementation authorization as
approval of unseen results.

## Historical integrity

`evaluation.governed_answers.evaluate_readiness` inventories the frozen 21-E
packet. Its original source bindings and missing-evidence statements describe that
checkpoint, not every later implementation. Preserve these bindings. New runtime
integration needs new evidence; editing the old manifest or approval record would
invalidate its historical verification rather than establish acceptance.
