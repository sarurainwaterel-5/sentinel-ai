# Sprint 21 selected-provider result — 2026-11-12

The bounded Responses rehearsal completed pending human review. All 44 transport
attempts completed: six Sol generation calls, 19 Astra statement assessments and
19 Terra relevance assessments. There were no operational failures or structural
rejections. This is a single run over reviewed synthetic sources, not production
retrieval or general model accuracy evidence.

The owner explicitly approved process-local assignment of the existing Sentinel
application key to Sol and Terra, preserving the distinct Astra judge key. No
credential was written to the repository or report. Model configuration remained
Sol low, Astra low and Terra none, with zero SDK retries and the original budgets.
Execution ran at 2026-11-13 05:31:09–05:33:13 UTC (November 12 in Chicago), from
implementation commit `331402b`.

## Observations requiring review

- Astra matched all 13 reviewed control statement labels. Terra matched 12 of 13
  control relevance labels. For `certainty`, Terra judged the overstated answer
  relevant while the reviewed relevance label was false. Astra rejected its
  statement, so the combined decision withheld it. Preserve this disagreement;
  this run does not authorize changing the frozen labels or assessment policy.
- The combined controls produced six review previews and seven withheld results.
- Four generated candidates reached review preview. `multi-premise` was withheld
  by relevance: its qualification distinguishes observed retention from a required
  retention rule. `causality` was withheld by Astra with `unsupported_fact`, despite
  Terra finding it relevant. These are assessment observations awaiting exact-text
  review, not agent-certified correct or incorrect verdicts.
- All 19 rows retained their exact supplied question, sources, premises and
  relationships. A separate post-run check verified those fields against the frozen
  inputs, every completed request/response digest, every relevance context echo,
  and the role counts. All production, empirical and release flags remain false.

## Preserved evidence

Private files remain outside Git under
`outputs/sprint21-provider-review/private/`:

- `sol-astra-terra-20261112-run1.json`: exact requests, returned structured outputs,
  comparisons and execution bindings; SHA-256
  `c51575a020cc9e6edbe5ebd80d3b93e04fcdebd5c382665b96999a801632a364`.
- `sol-astra-terra-20261112-run1.html`: escaped exact-candidate and complete-context
  review rendering, including withheld candidates. Owner-only directory and files.

The report's execution-authentication and semantic-grounding flags remain false;
this local evidence is not an independent provider attestation. No repeat calls,
policy adjustments, human acceptance or production enablement were performed.
The preceding 108-call Astra Chat Completions benchmark remains separate evidence.

Next: owner review of the preserved outputs and disagreement, followed by the
remaining application lifecycle/storage/retrieval/publication integration and
source-remediation work. ADR-037 stays Proposed; Sprint 21 remains open.
