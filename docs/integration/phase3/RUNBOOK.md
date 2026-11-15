# Independent synthetic strategy review runbook

Canonical implementation:
`backend/evaluation/synthetic_oversight/strategy/evaluator.mjs` and
`strategy/specification-v1.json`. No Trading detector is imported or trusted as a
confirmation. The evaluator checks supplied proposal anchors; it does not search
for or emit new trading proposals/signals.

The additive review envelope version is `sentinel.imaf.synthetic.review.v1`:

- version/spec_version/strategy_version, as_of and unchanged Phase 1 proposal object;
- execution, analysis and liquidity_session: timeframe_ms, explicit opens/closes,
  complete candles (timestamp/available_at, MNQ/contract, integer OHLCV);
- anchors: supplied sweep/MSS/FVG-end/entry indices; independent predicates verify
  them and derive the known opposing pivot, range, pool and target;
- explicit NY session bounds/date and optional bounded post-09:30 opportunity with
  availability and synthetic review reference; no default unrestricted later period;
- complete current synthetic risk state or null; platform claims boolean/null.

Maximum 65536-byte bounded JSON input; execution <=128, analysis <=32, pool <=64
candles. These are engineering bounds, not market thresholds. Strict UTC millisecond
strings, UTC interval alignment, complete contiguous series and source availability
are required. Future/unclosed/unreceived candles are rejected before computation.
The newest closed execution bar may be at most one execution interval old, matching
the existing research freshness policy. Analysis and pool inputs must have been
available before the relevant discovery/history boundary.

Run pure review with `evaluateStrategyReview(snapshot,{evaluatedAt})`. It returns
contract validity, research subset compliance, evidence sufficiency, synthetic risk
check, session check, unresolved doctrine, observations/disagreements and DENIED
execution authority. All top-level outcomes remain within the existing six; current
unresolved doctrine prevents full COMPLIANT. A valid research subset therefore
returns REVIEW_REQUIRED. Missing evidence returns INSUFFICIENT_EVIDENCE; known
contradictions NON_COMPLIANT; malformed/unavailable/future input INVALID as appropriate.

Observation records contain rule, PASS/FAIL/UNRESOLVED, exact supporting candle
prices/timestamps/availability, calculated levels and content references. Platform
claims are compared only after independent computation. Observation Ladder fields
separate facts/claims/unknowns, avoid inferred institutional identity, retain the
supplied hypothesis, and keep future professional review pending.

## Phase 2 persistence and replay

No SQL migration or Phase 1 proposal schema change was required. Phase 2 submit has
an additive `strategyReview` option. It verifies proposal equality, evaluates the
review independently, and atomically archives exact snapshot, full specification
text, result, snapshot/assessment/spec/evaluator hashes, Node/ICU/timezone versions
with the original proposal decision. The original core synthetic assessment remains
a distinct field; use strategy_assessment for this phase, never confuse an old
fixture-only COMPLIANT with full strategy compliance.

```js
store.submit(canonical(snapshot.proposal), {
  evaluationTime: snapshot.as_of,
  strategyReview: snapshot
});
```

Identical proposal AND snapshot return the original strategy result. Changed snapshot
under the same proposal ID creates an auditable STRATEGY_SNAPSHOT_CONFLICT; it cannot
replace history. Explicit new-identity supersession remains available under Phase 2.
Replay reads the stored snapshot and original cutoff, not a mutable source file or
new candles. MATCH requires exact core and strategy reproduction. Changed/missing
historical dependencies produce UNAVAILABLE, disagreement produces MISMATCH; both
are separate replay records. Original rows remain immutable.

CLI extends Phase 2 submit with `--strategy-input /absolute/private/review.json`.
Both proposal and review files must contain exact canonical JSON, without a trailing
newline, under the existing explicit private database workflow. Review file reads
are bounded/regular/no-follow; no credentials/default path/network is discovered.

In Trading AI use `evaluateSyntheticStrategy({consumerRoot,snapshot,evaluatedAt})`
for a pure pinned review and existing `openDurableSupervisor` for persistence.
Trading owns no duplicate evaluator, specification or ledger for this function.
Its consumer pin includes the canonical module/specification and reviewed fixtures.

## Reproduce tests

From Sentinel AI root:

```sh
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/strategy/evaluator.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/strategy/durable.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/strategy/security.test.mjs
```

From Trading AI root:

```sh
SENTINEL_SYNTHETIC_CONSUMER_ROOT=/absolute/path/sentinel-ai \
node --import /absolute/path/sentinel-ai/backend/evaluation/synthetic_oversight/deny-network.mjs \
  services/synthetic-oversight/strategy.test.mjs
```

See SPECIFICATION_COVERAGE.md, VALIDATION.md, SECURITY_BOUNDARIES.md and READINESS.md.
Synthetic scenario/disagreement/replay HTML and JSON are retained outside Git under
workspace `outputs/phase3-independent-imaf/`. No live/account-derived input is used.
