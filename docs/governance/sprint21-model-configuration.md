# Selected governed-answer models

User selection confirmed 2026-11-10. The nonsecret source of configuration is
`sprint21-model-selection.json`; production and empirical acceptance remain false.

| Role | Model | Reasoning effort | Explicit credential mapping key |
|---|---|---|---|
| Generation | `gpt-6.1-sol` | `low` | `SEMANTIC_GENERATION_API_KEY` |
| Semantic assessment | `gpt-6-astra` | `low` | `SEMANTIC_JUDGE_API_KEY` |
| Relevance/context assessment | `gpt-6.1-terra` | `none` | `SEMANTIC_RELEVANCE_API_KEY` |

`selected_model_configuration.create_selected_model_clients` validates the selected
artifact and all three explicit credential entries before creating clients.
It constructs separate async clients with zero retries and 30-second timeouts,
then injects model/effort configurations into the structured-output transport.
It reads no environment or dotenv and never substitutes the general application
credential. No credential belongs in this artifact, source control, or reports.
Model selection and separate clients do not establish independent judgment or
semantic accuracy. The existing production governed-answer route stays disabled.

## Astra benchmark checkpoint

The frozen legacy adapter and runner remain byte-for-byte unchanged. The new
`OpenAIReasoningAdmissibilityProvider` sends explicit low reasoning and bounded
completion tokens, with no temperature, top-p, log-probability or automatic retry
settings. This follows [OpenAI's parameter compatibility guidance](https://developers.openai.com/api/docs/guides/latest-model?model=gpt-6-astra).
The legacy system prompt and verdict schema remain unchanged.

New execution from the repository root, after securely configuring only the
dedicated judge key in the process environment:

```sh
PYTHONPATH=backend python -m evaluation.semantic_judge.astra_runner \
  --output /absolute/new/private/astra-benchmark-result.json
```

The output must be absent. The runner refuses existing paths, symlinks, tracked
files and governed input/implementation targets, and reserves the new file
exclusively. It requires the selected artifact and independently pinned frozen
dataset, policy and approved 36-label record. It runs 108 seed-ordered assessments
with low reasoning, 4,096 maximum completion tokens, 30-second per-call timeouts,
and zero SDK retries. No generation client or generation model is called by this
judge benchmark. No model is inferred from ambient configuration. Credentials
are never written to the result.

Reports bind new and legacy runner/adapter hashes, exact selection and provider
configuration, dataset/policy/review hashes, prompt, schema, commit and timing.
Missing dedicated credentials produce zero trials and null metrics, not accuracy.
Thresholds remain the original preregistered policy. Failed measurements must be
preserved and must not prompt retrospective threshold changes.

`evaluation.semantic_judge.astra_report.inspect_astra_report` is the versioned
diagnostic for this report format. The earlier runtime denial diagnostic continues
to validate its own historical format. The new diagnostic checks exact trial
coverage/order, configuration and artifact bindings, strict values, recomputed
metrics and bounded JSON. Even a consistent passing report can qualify only for
human review; it does not authenticate execution provenance or authorize release.

## Current state

Models and configuration are selected and checked in. The dedicated judge key
is absent from the execution environment; the owner has been asked for a secure
configuration path without pasting a key into chat. No live model call or semantic
measurement occurred during configuration. Live provider composition, index and
retrieval integration, final empirical/presentation review and bound production
authorization remain tracked in `../sprints/Sprint-21-Completion-Status.md`.

Validation: **132 focused and related regression tests passed in 23.89s**, covering
all three selected role dispatches, credential isolation, client cleanup,
reasoning compatibility, output-file preservation, frozen benchmark input pins,
new report consistency and legacy harness/gate behavior. All four historical
governance integrity inspectors remained valid with no errors; readiness stayed
blocked. No legacy prompt, schema, acceptance policy, approved label record,
adapter or benchmark runner was changed. The optional reasoning configuration
leaves existing transport callers unchanged when omitted.
