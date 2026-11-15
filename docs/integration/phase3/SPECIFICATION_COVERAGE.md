# Independent IMD/IMAF specification coverage

Verdict: a deterministic **research subset is implemented**; **full IMD/IMAF strategy
compliance is INCOMPLETE**. Missing doctrine is not converted into thresholds or
approval switches. No execution authority follows from any result.

## Inspected sources and precedence

Trading baseline `61bb7dd`, Sentinel baseline `b9f3ce3`; existing unrelated Trading
changes remain outside this implementation. The machine-readable specification
`backend/evaluation/synthetic_oversight/strategy/specification-v1.json` pins exact
selected source hashes and the owner Phase 3 mission hash.

Sources in Trading AI:

- `docs/architecture/IMAF-GAP-001.md`: manuscript identity, physical/printed page
  references, qualitative gaps, Four Pillars and seven Observation Ladder rungs.
- `docs/architecture/ADR-005-imaf-governance.md`, `services/governance/imaf.js`:
  owner-selected ten-stage Current Canon, registered timeframe pairs and entry lock.
- `research/governance/IMAF-OPERATIONAL-QUESTIONS.json`: four unresolved definitions,
  each approvedDefinition:null. No approval is inferred from this task.
- `docs/strategy/STRATEGY-001.md`, `packages/ict-model/index.js`,
  `packages/config/ict-research.js`, `services/signal-engine/ict-proposal.js`,
  `packages/ict-model/context.js`: executable research predicates and limits.
- `research/governance/proposals/imaf-operational-v0.1.json`: existing draft for
  review, not activated definitions. `services/governance/research-expiry.js` and
  research/session-timeframe docs describe separate unauthenticated research tools.

This phase inspected repository source reviews and implementation, not a fresh
independent transcription/attestation of the external manuscript PDF. The repository
pins v0.9 source hash e170611529c68f674b5f4187515a8e6fba7e15624c365f844b750b82ffa06ece.
No internet ICT definition was substituted for supplied doctrine.

## Classification and verified scope

| Concept | Classification / source | Implemented independent check and limitation |
|---|---|---|
| Swings | Fully specified research predicate; STRATEGY-001, ict-model | Strict left/right pivots, no ties, confirmation-bar closure and receipt before sweep. Active PAPER profile uses left/right 1; not manuscript authority. |
| Liquidity sweep | Fully specified research predicate; ict-model | Strict excursion and close back across an independently derived supplied session extreme. Equality is not sweep. Significance/ranking remain partial. |
| Structural break / MSS | Research rule explicit; accepted transition incomplete | Close beyond pre-sweep known opposing pivot after sweep; wick-only break insufficient. This is not canon's accepted structural transition. |
| Displacement | Explicit research parameters; not canonical thresholds | Integer-rational body/range and prior-only baseline checks, with referenced candles. Institutional intent is not inferred. |
| FVG | Explicit research three-bar geometry | Strict nonoverlap, minimum existing one-tick gap, three closed/available bars; does not establish significance or participation alone. |
| Entry/OTE | Explicit research arithmetic; strategy choice provisional | Existing .62–.79 interval, FVG intersection, rounded midpoint, later first retracement, structural stop buffer and no prior stop violation. .786 is not forced to a tick or treated as an exclusive entry. |
| Premium/discount | Explicit midpoint research arithmetic | Independently derives supplied paired analysis range; entry strict discount/premium and acquisition-side pool location. PD-array selection is not resolved. |
| HTF directional bias | Partial/discretionary/missing operational rule | No invented trend or close/open bias threshold. Explicit UNRESOLVED. A range-location check is not directional-bias certification. |
| Session liquidity | Explicit arithmetic; calendar/objective selection partial | Complete explicit earlier window -> high/low with source candles and availability. Calendar legitimacy, significance and window selection remain supplied/unverified. |
| Target selection | Partial | Opposing extreme in the explicit supplied pool window; no claim that this is the authoritative objective across all market pools. Global ranking/expiry unresolved. |
| Price delivery alignment | Partial/discretionary | Causal research sweep/break/displacement/FVG/OTE geometry is checked. Canonical acceptance, participation, narrative and array selection remain unresolved. |
| Canonical acceptance/rejection | Missing approved numerical rule | Registry remains null; existing research sweep is never promoted to acceptance/rejection. |
| Accepted structural transition | Missing approved operational rule | Research MSS stays distinct; no two-close draft confirmation silently activated. |
| Narrative coherence / independent participation | Qualitative/discretionary; approval missing | Price effects recorded; no participant identity, intent or certainty manufactured. |
| NY windows | Owner mission specifies times; expiry/calendar still partial | Three stated early windows plus explicit bounded post-09:30 opportunity, America/New_York/DST. Half-open decision-time interval is a documented synthetic convention, not canonical discovery/expiry approval. |
| One trade/day / 48h error pause | Owner mission advisory restrictions | Supplied synthetic state must be current/complete; exact UTC 48h, NY calendar-day label. Exchange-day rollover/calendar authority remains unresolved; no ledger-authenticated state is inferred. |
| Risk economics | Existing research limits, not account authorization | One MNQ, 50 cents/tick, <=5000-cent planned loss, >=2 net R, -10000-cent loss lockout, no open/pending exposure; checked only on supplied synthetic state. |
| Market out of balance | Missing computational definition | A supplied true flag blocks; null/missing state is insufficient. A supplied false flag is not independently proved balanced; canonical balance remains unresolved. |

## Conflicting / versioned definitions

- Eight historical stages vs ten Current Canon: already resolved by owner in ADR-005;
  ten is primary. This evaluator does not replace the existing governance engine.
- DEFAULT_RULES uses 2/2 swing widths and baseline 5; active PAPER_STRATEGY_RULES
  overrides to 1/1 and baseline 3. We pin the latter because imaf.js uses it. Both
  are research choices; selecting one does not approve it as manuscript doctrine.
- Existing draft discovery starts 09:30 and ends before 11:00. This mission explicitly
  requests earlier windows and approved later opportunities. We implement the
  mission's bounded decision-window checks and leave discovery/expiry doctrine
  unresolved. The draft is not loaded as runtime policy.
- Prior signal engine supports only bounded 1M/5M inputs and injected 1H/4H contexts.
  This independent synthetic verifier supports all four registered pairs, including
  15-second/15-minute execution; that does not complete the existing production
  context producer or approve its new timeframes.

Full canonical numerical coverage is not established. See PROPOSED_DEFINITIONS.md
for the concrete human review packet; READINESS.md lists affected incomplete areas.
