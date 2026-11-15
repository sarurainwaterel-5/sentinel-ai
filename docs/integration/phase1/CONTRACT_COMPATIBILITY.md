# Phase 1 contract compatibility verification

Verified November 15, 2026 against Sentinel AI `c2558889e9579e1e44e4ef046906ab03024d25e7`
and Trading AI `8aa8122675cb49d64d0f38c207d921218a402794` plus preserved Trading user edits.
`git show` confirms that c255888 changed CSV tab provenance/tests/docs; 8aa8122
added a documentation handoff and README link only. Neither created connected
runtime integration. The previous 81 focused Sentinel tests were rerun successfully.

## Existing artifacts and mismatches

| Concern | Existing evidence | Resolution for this phase |
|---|---|---|
| Schema versions | Sentinel `contracts.py`: `sentinel.trading.oversight.snapshot.v0.1`; CSV capture `tradingview.py`: evidence.v0.2; Trading `docs/runbooks/sentinel-oversight-handoff.json`: documentation.v0.1 | These are different artifact types, not compatible wire envelopes. Add `sentinel.synthetic.proposal.v1`; no old version is replaced. |
| Event types | Snapshot `Event.type` is bounded free text; Trading `packages/contracts/src/index.ts` AuditEvent.type is string | Synthetic protocol closes event enum to SUBMITTED/REVISED/WITHDRAWN names prefixed PROPOSAL_. It does not import ledger event types. |
| Proposal/trade identifiers | Snapshot candidate_id/candidate_sha256; Trading TradeCandidate.id/idempotencyKey | New synthetic proposal_id and event_id are explicit scoped labels, not order IDs or automatic candidate conversions. |
| Instrument identifiers | Snapshot proposal has no instrument field; Trading candidate uses symbol + contractMonth | Synthetic envelope requires symbol + contract_month; accepts MNQ only, exact calendar month pattern. No rollover/provider entitlement claim. |
| Timestamps/time zones | Snapshot uses exact UTC millisecond strings; Trading Timestamp is a TS string, with runtime validators elsewhere | Exact canonical UTC milliseconds, calendar round trip, no offsets; data <= event <= supplied evaluation clock. Freshness <= 2 seconds is a synthetic test policy. |
| Evidence references | Snapshot SHA-256 refs; Trading evidenceRefs are descriptive IDs such as bar/pool refs | Synthetic bodies are closed fixture assertions hashed by canonical JSON. References must resolve by kind and hash. No automatic conversion of Trading refs or provider authentication. |
| Risk metadata | Snapshot binds policy hashes/account state; Trading RiskAuthorization can carry consumable authority | New synthetic risk metadata is not a RiskAuthorization. Fixed one-MNQ, 50 cents/tick, <= 5000-cent loss budget and net 2R fixture checks only. No account-risk authorization. |
| Strategy metadata | Trading has ict-research-v1 evidence/reconstruction; snapshot binds strategy policy hash | Synthetic `synthetic-ict`, version `1`, with hash-referenced fixture evidence. It neither executes nor substitutes for ICT reconstruction or IMAF definitions. |
| Assessment statuses | Old evaluator overall BLOCKED; no runtime assessment in handoff doc | Six informational outcomes in new module; old BLOCKED remains unchanged. Technical validity, fixture compliance and operational authorization are separate fields. |
| Errors | Old Python CLI has bounded generic errors; no Trading service error contract in handoff | Bounded raw canonical JSON input -> structured INVALID assessment. Missing/pin-invalid local module -> UNAVAILABLE transport result without an assessment. Capacity exhaustion -> explicit error, no overwrite. |
| Idempotency/duplicates | Existing Trading candidate idempotency differs from snapshot batch semantics | Identical accepted event returns immutable original assessment. Conflicting event ID or repeated submission/new event at revision 1 is INVALID, journaled without overwriting original. |
| State transitions | No shared lifecycle state machine | SUBMITTED revision 1 -> REVISED/ WITHDRAWN at revision +1; withdrawal terminal. Account/correlation immutable; timestamps cannot regress. |

Sources: `backend/evaluation/trading_oversight/{contracts,evaluator,tradingview}.py`,
`docs/trading/snapshot-v0.1.schema.json`; in Trading AI:
`packages/contracts/src/index.ts`, `packages/audit/index.js`,
`services/signal-engine/ict-proposal.js`, `services/risk-gateway/evidence.js`,
`services/governance/imaf.js`, `docs/runbooks/sentinel-oversight-handoff.json`.

## Canonical ownership and additive compatibility

Sentinel AI owns `backend/evaluation/synthetic_oversight/proposal-v1.schema.json`
and `protocol.mjs`; these define one additive protocol. Trading AI's
`services/synthetic-oversight/adapter.mjs` imports that exact implementation after
verifying `consumer-pin.json`. It does not contain a second schema or validator.
Both use the same canonical wire and shared contract tests; Trading's actual
`packages/audit/index.js` digest is compared with the shared protocol digest.

The schema is closed. Wire input is a canonical JSON string: sorted keys, no
formatting whitespace, no duplicate keys, safe integers, bounded arrays/depth and
32 KiB maximum. Use canonical() only to serialize trusted synthetic objects;
pass untrusted wire directly to assess(). Errors never echo source payloads.

No breaking contract changes were required. Future incompatible changes require a
new version and explicit review, not mutation of this version or silent pin refresh.
The consumer's hash pins establish local file consistency, not producer identity,
source authenticity, race-proof hostile-filesystem isolation or a production trust root.
