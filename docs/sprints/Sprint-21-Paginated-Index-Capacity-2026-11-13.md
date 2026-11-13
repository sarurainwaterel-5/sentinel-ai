# Paged governed index and selected context capacity

This additive engineering checkpoint removes the earlier 128-chunk **document**
restriction from index reconciliation and immutable-manifest publication validation.
Production remains disabled. No installed corpus was migrated, reindexed or supplied
to providers during this work.

## Supported protocol bounds

- Immutable manifests: up to 100,000 contiguous locators, each 1..65,536 bytes, with
  a total verified UTF-8 chunk-byte budget of 64 MiB. SQL pages hold 256 locators.
- Complete index readback: up to 391 pages of 256 points, detecting duplicate IDs,
  repeated/invalid cursors, extra/missing points, stale epochs and changed metadata.
  No partial page is treated as a complete manifest. Points store locators/digests,
  scope, version/epochs and vector-policy identity; source text resolves from CAS.
- Index updates: 256 points per request; explicit vector adapter calls use batches
  of at most 32 texts. Dimensions are configured in 1..4096 and must match the
  collection. Finite exact-dimension outputs and stable model/policy identity are
  required. The existing default remains a visibly synthetic four-dimensional
  fixture. The local embedding adapter is a separate explicit configuration.
- Inspection context: callers explicitly select 1..128 unique chunk indices after
  full manifest/index verification. For documents above 128 chunks, omitting the
  selection denies. The provider's existing input-byte budget still applies;
  selecting 128 large chunks does not guarantee an admissible provider request.
- Publication validates the complete paged SQL manifest and its pinned digest,
  then verifies every selected exact CAS chunk, locator and extractive premise.
  Sources need not exhaust the document. The immutable artifact records selected
  indices and the exact SQL publication proof including version, epochs, scope,
  manifest and gate identity. Missing or unsupported selections never truncate
  verification or create a partial answer.

The checked retrieval here is explicit locator retrieval, not an evaluated semantic
ranking system. A caller-supplied selection is not evidence of question relevance;
that remains subject to the separate model assessment and owner review. A model/policy
hash identifies configuration, not independently verified model weight files.

## Executed evidence and limits

An actual disposable PostgreSQL/Qdrant test uses 257 synthetic chunks, a configured
two-dimensional vector adapter, batched embedding fixtures, complete two-page index
readback and a selected context containing locators 0 and 256. It completes SDK HTTP
mock generation/judgment/relevance, conditional SQL publication and checked reading.
Changing an **unselected** point's chunk digest denies retrieval, demonstrating that
selected context does not bypass full index verification. A different vector policy
also denies. Additional injected page tests cover duplicates, cursor loops, oversized
pages and dimension mismatch.

This crosses the pagination boundary; it does not benchmark 9,103-chunk dictionary
performance, prove capacity at 100,000 chunks, demonstrate real embedding/ranking
accuracy, or establish extraction faithfulness to source originals. Those operational
and acceptance checks remain separate. Original source review, catalog migration,
unsupported lifecycle replacement/reindex flows, owner semantic acceptance and bound
production authorization remain outstanding. ADR-037 stays Proposed.

## Bounded lease renewal

The reconciler uses a configurable monotonic outer budget of at most 3,600 seconds
and an explicit 1..120-second lease (120 by default). It renews only the same live
claim around manifest pages, embedding batches, index writes, every index readback
page and before acknowledgement. The catalog refuses expired, wrong-token,
superseded or changed-version renewals; renewal never revives stale work or resets
claim-attempt counts. Deadline exhaustion leaves the operation unacknowledged.
Synchronous embedding, CAS and HTTP calls cannot be forcibly preempted by a progress
callback: if one blocks beyond its lease/budget, the next check denies and SQL
acknowledgement still independently requires a live current lease. These are bounded
cooperative checks, not a hard realtime guarantee or measured large-corpus throughput.
Actual service regressions inject deadline exhaustion during an embedding batch and
force lease expiry; both preserve restoring/unacknowledged state.
