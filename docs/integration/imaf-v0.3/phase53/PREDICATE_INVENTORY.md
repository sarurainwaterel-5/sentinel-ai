# Phase 53.1 — Complete scoped predicate inventory

**DRAFT — NOT APPROVED FOR EXECUTION.**

Execution authorization: **DENIED**. Inventory created before new Phase 53 analytical logic. “Approved” below means a narrowly authorized engineering/research invariant in the current Decision 53 directive, never an approved executable trading predicate. This inventory covers every newly proposed predicate in this increment and cross-references all inherited compound records. It does not claim the inherited compounds have become a complete atomic executable strategy.

Source authority: current Decision 53 attachment `/home/rain/.codex/attachments/14fb6661-4d76-48d2-b698-c77013adefa8/Pasted text.txt`, sections 3–12; predecessor [predicate register](../PREDICATE_READINESS_REGISTER_V0.3.md), [owner records](../OWNER_DECISIONS_17_36.md), [canonical catalog](../IMAF_CANONICAL_SPEC_V0.3_DRAFT.md#exact-manuscript-source-catalog). Test labels below are acceptance obligations, **not claims that tests have run**; actual counts and commands belong to the acceptance report.

## Common causal and failure contract

For every record: evaluation at cutoff T may use only completed evidence available at or before T. Evidence IDs, source/data/model versions, event time, receipt/availability time, classification time and dependency lineage must be retained. Earliest valid classification is no earlier than maximum dependency availability. Unknown comparisons or unavailable dependencies yield explicit UNRESOLVED, never false confirmation. Malformed input is INVALID; missing evidence is an explicit non-confirming result. The distinction between event, observation, interpretation, confirmation and authorization is mandatory.

## Inherited canonical records — unchanged and unresolved

All exact-rule values below remain **null**. Each record retains its original ID. Earliest evaluation is max availability of its listed prerequisites, further constrained by its inherited cutoff; no canonical sufficient condition is approved. Failure is UNRESOLVED/INSUFFICIENT_EVIDENCE with a reason. Tests: undefined-predicate fail-closed (F), no unsupported promotion (D/F), temporal dependency and deterministic replay (G), and applicable lifecycle no-revival (H). The inherited register contains the detailed positive/negative/contradictory evidence fields.

### P01 — LIQUIDITY_OBJECTIVE_SELECTION

- Stable ID: `IMAF-V02-LIQUIDITY_OBJECTIVE_SELECTION` (P01).
- Decision source/prerequisites: D7/D10; current owner refinements: [D19](../OWNER_DECISIONS_17_36.md#d19), [D22](../OWNER_DECISIONS_17_36.md#d22), [D24](../OWNER_DECISIONS_17_36.md#d24)
- Input evidence: Known objective candidates, larger-context evidence, session context, already-acquired flags and candidate source times.
- Earliest evaluation/cutoff: Objective selected before acquisition interpretation; retain original selection time.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: Controlling objective/significance must not depend on the bias it is used to prove; distinguish initial candidates from later contextual ranking.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P01](../PREDICATE_READINESS_REGISTER_V0.3.md#p01).

### P02 — LIQUIDITY_ACQUISITION

- Stable ID: `IMAF-V02-LIQUIDITY_ACQUISITION` (P02).
- Decision source/prerequisites: D1/D10; current owner refinements: [D17](../OWNER_DECISIONS_17_36.md#d17), [D20](../OWNER_DECISIONS_17_36.md#d20), [D21](../OWNER_DECISIONS_17_36.md#d21), [D22](../OWNER_DECISIONS_17_36.md#d22), [D23](../OWNER_DECISIONS_17_36.md#d23)
- Input evidence: Pinned objective/boundary, instrument, closed OHLCV, event/availability times.
- Earliest evaluation/cutoff: Boundary known before acquisition; exact onset-vs-close availability rule unresolved.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D20](../OWNER_DECISIONS_17_36.md#d20)/[D21](../OWNER_DECISIONS_17_36.md#d21) now separate penetration facts from significant acquisition/return/confirmation. Boundary provenance/tick/causal interaction profile still not approved.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P02](../PREDICATE_READINESS_REGISTER_V0.3.md#p02).

### P03 — QUALIFYING_DISPLACEMENT

- Stable ID: `IMAF-V02-QUALIFYING_DISPLACEMENT` (P03).
- Decision source/prerequisites: D1/D4; current owner refinements: [D27](../OWNER_DECISIONS_17_36.md#d27), [D29](../OWNER_DECISIONS_17_36.md#d29), [D32](../OWNER_DECISIONS_17_36.md#d32)
- Input evidence: Closed directional OHLCV, prior-only comparison history, instrument tick metadata.
- Earliest evaluation/cutoff: Comparison inputs and displacement available by cutoff, no later baseline.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D27](../OWNER_DECISIONS_17_36.md#d27) gives context dimensions, not body/range/baseline thresholds. Same candle may support MSS but is not additional independent confirmation.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P03](../PREDICATE_READINESS_REGISTER_V0.3.md#p03).

### P04 — PROVISIONAL_REJECTION

- Stable ID: `IMAF-V02-PROVISIONAL_REJECTION` (P04).
- Decision source/prerequisites: D1; current owner refinements: [D17](../OWNER_DECISIONS_17_36.md#d17), [D20](../OWNER_DECISIONS_17_36.md#d20), [D33](../OWNER_DECISIONS_17_36.md#d33)
- Input evidence: P02 acquisition, known boundary, qualifying inside return, P03 displacement, timestamps.
- Earliest evaluation/cutoff: Each component observable by provisional classification time; same-bar vs later-bar rule unresolved.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: Prior D1 return+displacement is provisional; [D17](../OWNER_DECISIONS_17_36.md#d17)/[D20](../OWNER_DECISIONS_17_36.md#d20) discovery is earlier acquisition, not the same response conclusion.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P04](../PREDICATE_READINESS_REGISTER_V0.3.md#p04).

### P05 — CONTEXTUAL_PARTICIPATION

- Stable ID: `IMAF-V02-CONTEXTUAL_PARTICIPATION` (P05).
- Decision source/prerequisites: D4; current owner refinements: [D26](../OWNER_DECISIONS_17_36.md#d26), [D27](../OWNER_DECISIONS_17_36.md#d27), [D32](../OWNER_DECISIONS_17_36.md#d32)
- Input evidence: Larger objective, liquidity behavior, displacement, subsequent delivery and alternative explanations.
- Earliest evaluation/cutoff: Only observations already available; subsequent evidence changes a later record.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D32](../OWNER_DECISIONS_17_36.md#d32) needs dependency-aware independent evidence and source applicability; optional volume/orderflow cannot be fabricated or silently made universally mandatory.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P05](../PREDICATE_READINESS_REGISTER_V0.3.md#p05).

### P06 — LIQUIDITY_ACCEPTANCE

- Stable ID: `IMAF-V02-LIQUIDITY_ACCEPTANCE` (P06).
- Decision source/prerequisites: D2/D3; current owner refinements: [D20](../OWNER_DECISIONS_17_36.md#d20), [D34](../OWNER_DECISIONS_17_36.md#d34)
- Input evidence: Known boundary, acquisition side, directional response, persistence/delivery context.
- Earliest evaluation/cutoff: Acceptance evidence must precede its use in invalidation or confirmation.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D34](../OWNER_DECISIONS_17_36.md#d34) requires contextual response evidence; no selected count, retest sufficiency or conjunction/alternative rule.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P06](../PREDICATE_READINESS_REGISTER_V0.3.md#p06).

### P07 — REJECTION_CONFIRMATION_ROUTE

- Stable ID: `IMAF-V02-REJECTION_CONFIRMATION_ROUTE` (P07).
- Decision source/prerequisites: D2; current owner refinements: [D33](../OWNER_DECISIONS_17_36.md#d33)
- Input evidence: P04 provisional rejection, P05 participation, pre-event larger-context interpretation, structural or persistence evidence.
- Earliest evaluation/cutoff: No final narrative/accepted transition from same assessment used as its prerequisite.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D33](../OWNER_DECISIONS_17_36.md#d33) eligibility must be pinned prospectively; structural route must not require the same accepted transition that requires its own confirmed response.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P07](../PREDICATE_READINESS_REGISTER_V0.3.md#p07).

### P08 — REJECTION_INVALIDATION

- Stable ID: `IMAF-V02-REJECTION_INVALIDATION` (P08).
- Decision source/prerequisites: D3; current owner refinements: [D18](../OWNER_DECISIONS_17_36.md#d18), [D33](../OWNER_DECISIONS_17_36.md#d33), [D34](../OWNER_DECISIONS_17_36.md#d34)
- Input evidence: Original rejection identity, qualifying reclaim, P06 opposite acceptance, cutoff.
- Earliest evaluation/cutoff: Reclaim and acceptance both available when invalidation is asserted.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D18](../OWNER_DECISIONS_17_36.md#d18) invalidation requires approved contradiction; prior D3 reclaim+opposite acceptance not a single contrary close; same-instant conflict unresolved.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P08](../PREDICATE_READINESS_REGISTER_V0.3.md#p08).

### P09 — STRUCTURAL_PERSISTENCE

- Stable ID: `IMAF-V02-STRUCTURAL_PERSISTENCE` (P09).
- Decision source/prerequisites: D5; current owner refinements: [D22](../OWNER_DECISIONS_17_36.md#d22), [D23](../OWNER_DECISIONS_17_36.md#d23), [D28](../OWNER_DECISIONS_17_36.md#d28), [D29](../OWNER_DECISIONS_17_36.md#d29), [D30](../OWNER_DECISIONS_17_36.md#d30)
- Input evidence: Preknown structure/swing, observed close break, subsequent structural observations.
- Earliest evaluation/cutoff: Pivot selection/confirmation known before event; persistence observable before use.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D23](../OWNER_DECISIONS_17_36.md#d23)/[D28](../OWNER_DECISIONS_17_36.md#d28)–[D30](../OWNER_DECISIONS_17_36.md#d30) require candidate/confirmed/significant distinction, break classification and persistence. Research pivot geometry alone supplies no canonical significance.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P09](../PREDICATE_READINESS_REGISTER_V0.3.md#p09).

### P10 — PRICE_DELIVERY_CONFIRMATION

- Stable ID: `IMAF-V02-PRICE_DELIVERY_CONFIRMATION` (P10).
- Decision source/prerequisites: D4/D5; current owner refinements: [D26](../OWNER_DECISIONS_17_36.md#d26), [D27](../OWNER_DECISIONS_17_36.md#d27), [D31](../OWNER_DECISIONS_17_36.md#d31), [D32](../OWNER_DECISIONS_17_36.md#d32)
- Input evidence: Earlier liquidity event, raw follow-through/delivery observations, alternative paths.
- Earliest evaluation/cutoff: Delivery observed before transition inference; no completed later narrative prerequisite.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D31](../OWNER_DECISIONS_17_36.md#d31) later delivery cannot be satisfied solely by original MSS candle; independent additional information and sufficient progress/contradiction remain undefined.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P10](../PREDICATE_READINESS_REGISTER_V0.3.md#p10).

### P11 — ACCEPTED_STRUCTURAL_TRANSITION

- Stable ID: `IMAF-V02-ACCEPTED_STRUCTURAL_TRANSITION` (P11).
- Decision source/prerequisites: D5; current owner refinements: [D18](../OWNER_DECISIONS_17_36.md#d18), [D28](../OWNER_DECISIONS_17_36.md#d28), [D29](../OWNER_DECISIONS_17_36.md#d29), [D30](../OWNER_DECISIONS_17_36.md#d30), [D31](../OWNER_DECISIONS_17_36.md#d31), [D34](../OWNER_DECISIONS_17_36.md#d34)
- Input evidence: Preceding liquidity response/participation, P09 persistence AND P10 delivery confirmation.
- Earliest evaluation/cutoff: All prerequisites available before accepted-transition record.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: Persistence AND independent delivery necessary, not sufficient by labeling. Pre-response participation/response dependencies must be noncircular.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P11](../PREDICATE_READINESS_REGISTER_V0.3.md#p11).

### P12 — HIERARCHICAL_CONTEXT

- Stable ID: `IMAF-V02-HIERARCHICAL_CONTEXT` (P12).
- Decision source/prerequisites: D7; current owner refinements: [D19](../OWNER_DECISIONS_17_36.md#d19), [D22](../OWNER_DECISIONS_17_36.md#d22), [D23](../OWNER_DECISIONS_17_36.md#d23), [D24](../OWNER_DECISIONS_17_36.md#d24), [D25](../OWNER_DECISIONS_17_36.md#d25), [D28](../OWNER_DECISIONS_17_36.md#d28), [D35](../OWNER_DECISIONS_17_36.md#d35)
- Input evidence: P01 larger objective, required timeframe contexts, lower movement evidence.
- Earliest evaluation/cutoff: Larger-context evidence known at its use; freeze interpretation before evaluating lower outcome.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D19](../OWNER_DECISIONS_17_36.md#d19)/[D24](../OWNER_DECISIONS_17_36.md#d24) hierarchy/range anchors and update rules cannot be fitted to OTE or favorable target; exact mappings selected but context producer incomplete.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P12](../PREDICATE_READINESS_REGISTER_V0.3.md#p12).

### P13 — NARRATIVE_CLASSIFICATION_AND_COHERENCE

- Stable ID: `IMAF-V02-NARRATIVE_CLASSIFICATION_AND_COHERENCE` (P13).
- Decision source/prerequisites: D6; current owner refinements: [D18](../OWNER_DECISIONS_17_36.md#d18), [D26](../OWNER_DECISIONS_17_36.md#d26), [D35](../OWNER_DECISIONS_17_36.md#d35), [D36](../OWNER_DECISIONS_17_36.md#d36)
- Input evidence: P01/P05/P06/P07/P11/P12 and delivery evidence, competing explanations, invalidation hypothesis.
- Earliest evaluation/cutoff: Synthesis after prerequisite observations; later verification cannot backfill it.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D35](../OWNER_DECISIONS_17_36.md#d35) taxonomy now names confirmed reversal; earlier confirmed directional transition is not silently treated as identical operational state.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P13](../PREDICATE_READINESS_REGISTER_V0.3.md#p13).

### P14 — PD_ARRAY_GEOMETRY_AND_CONTEXT

- Stable ID: `IMAF-V02-PD_ARRAY_GEOMETRY_AND_CONTEXT` (P14).
- Decision source/prerequisites: D8; current owner refinements: [D24](../OWNER_DECISIONS_17_36.md#d24), [D25](../OWNER_DECISIONS_17_36.md#d25), [D26](../OWNER_DECISIONS_17_36.md#d26), [D31](../OWNER_DECISIONS_17_36.md#d31)
- Input evidence: Array type/geometry/version, prior liquidity event, participation, transition, narrative and invalidation.
- Earliest evaluation/cutoff: Geometry and context available by use; later retest cannot justify earlier classification.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D25](../OWNER_DECISIONS_17_36.md#d25) 78.6 is contextual precision only; [D26](../OWNER_DECISIONS_17_36.md#d26) geometric/relevant/setup-qualified FVG distinct. Exact geometry profile/range/tick convention and model qualification remain incomplete.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P14](../PREDICATE_READINESS_REGISTER_V0.3.md#p14).

### P15 — OUT_OF_BALANCE_ASSESSMENT

- Stable ID: `IMAF-V02-OUT_OF_BALANCE_ASSESSMENT` (P15).
- Decision source/prerequisites: D9; current owner refinements: [D35](../OWNER_DECISIONS_17_36.md#d35), [D36](../OWNER_DECISIONS_17_36.md#d36)
- Input evidence: Auction evidence, P13 coherence/actionability reasoning, known missing inputs.
- Earliest evaluation/cutoff: Classify only from evidence available at cutoff.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: Reuse approved narrative coherence when available; [D36](../OWNER_DECISIONS_17_36.md#d36) fresh evidence/recovery cannot revive old setup or manufacture balance from a supplied false flag.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P15](../PREDICATE_READINESS_REGISTER_V0.3.md#p15).

### P16 — WINDOW_AND_DISCOVERY

- Stable ID: `IMAF-V02-WINDOW_AND_DISCOVERY` (P16).
- Decision source/prerequisites: D12; current owner refinements: [D17](../OWNER_DECISIONS_17_36.md#d17)
- Input evidence: Versioned explicit NY window/session, acquisition/other selected discovery event and availability.
- Earliest evaluation/cutoff: Discovery event availability vs event-time selection unresolved; preserve both.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D17](../OWNER_DECISIONS_17_36.md#d17) supplies four exact CT windows; existing helper only outer opening/cutoff. Model-specific qualifying event availability remains undefined; probe discrepancies documented.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P16](../PREDICATE_READINESS_REGISTER_V0.3.md#p16).

### P17 — SETUP_LIFECYCLE_AND_EXPIRY

- Stable ID: `IMAF-V02-SETUP_LIFECYCLE_AND_EXPIRY` (P17).
- Decision source/prerequisites: D12; current owner refinements: [D17](../OWNER_DECISIONS_17_36.md#d17), [D18](../OWNER_DECISIONS_17_36.md#d18), [D36](../OWNER_DECISIONS_17_36.md#d36)
- Input evidence: Immutable setup/acquisition IDs, P16 discovery, explicit finite bound, causal update events.
- Earliest evaluation/cutoff: Expiry committed from approved inputs before continued evaluation; receipt delays cannot extend.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D17](../OWNER_DECISIONS_17_36.md#d17) finite expiry deadline source/maximum lifetime remains explicitly unresolved. Fresh recovery event cannot extend/relabel old identity; historical replay is not a new opportunity.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P17](../PREDICATE_READINESS_REGISTER_V0.3.md#p17).

### P18 — EXCHANGE_TRADING_DAY_CALENDAR

- Stable ID: `IMAF-V02-EXCHANGE_TRADING_DAY_CALENDAR` (P18).
- Decision source/prerequisites: D11; current owner refinements: [D17](../OWNER_DECISIONS_17_36.md#d17), [D22](../OWNER_DECISIONS_17_36.md#d22), [D36](../OWNER_DECISIONS_17_36.md#d36)
- Input evidence: Calendar ID/version/source, instrument/product, UTC intervals, exchange day IDs, holiday/exception coverage.
- Earliest evaluation/cutoff: Calendar version/effective coverage known before accounting decision.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: Existing Trading calendar/manifest validators can be reused; no authoritative covered calendar data demonstrated in this audit.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P18](../PREDICATE_READINESS_REGISTER_V0.3.md#p18).

### P19 — TRADING_DAY_AND_ACCOUNT_ALLOWANCE

- Stable ID: `IMAF-V02-TRADING_DAY_AND_ACCOUNT_ALLOWANCE` (P19).
- Decision source/prerequisites: D11; current owner refinements: [D17](../OWNER_DECISIONS_17_36.md#d17), [D36](../OWNER_DECISIONS_17_36.md#d36)
- Input evidence: P18 trading-day ID, strategy/version, account-specific restrictions, authentic entry history.
- Earliest evaluation/cutoff: Complete historical account events available by decision time.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: Trade/attempt/fill consumption identity, authenticated current account history, day/version binding and independent account restrictions unresolved.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P19](../PREDICATE_READINESS_REGISTER_V0.3.md#p19).

### P20 — INDEPENDENT_PROFESSIONAL_RISK_EVIDENCE

- Stable ID: `IMAF-V02-INDEPENDENT_PROFESSIONAL_RISK_EVIDENCE` (P20).
- Decision source/prerequisites: D9/D11 and preserved controls; current owner refinements: [D17](../OWNER_DECISIONS_17_36.md#d17), [D36](../OWNER_DECISIONS_17_36.md#d36)
- Input evidence: Existing hard-limit policy, proposal risk geometry, account/exposure history, error log, operator/operational readiness where required.
- Earliest evaluation/cutoff: Only actual available account/human/operational evidence; no guessed attestations.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: Pure risk/ledger controls exist but genuine source/account/operator truth not established; backup/recovery and live authority not implied by arithmetic.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P20](../PREDICATE_READINESS_REGISTER_V0.3.md#p20).

### P21 — PROFESSIONAL_REVIEW_COMPLETENESS

- Stable ID: `IMAF-V02-PROFESSIONAL_REVIEW_COMPLETENESS` (P21).
- Decision source/prerequisites: All decisions, review checkpoint; current owner refinements: [D36](../OWNER_DECISIONS_17_36.md#d36)
- Input evidence: Original decision/evidence/cutoff, subsequent outcomes, factual attribution, interpretive process review.
- Earliest evaluation/cutoff: Outcome used only after its availability; never modifies earlier rationale.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: Factual outcome receipt exists in Trading; independent interpretive process-completeness/attribution and genuine reviewed outcomes not established.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P21](../PREDICATE_READINESS_REGISTER_V0.3.md#p21).

### P22 — CONTEXTUAL_TARGET_RANKING

- Stable ID: `IMAF-V02-CONTEXTUAL_TARGET_RANKING` (P22).
- Decision source/prerequisites: D10; current owner refinements: [D19](../OWNER_DECISIONS_17_36.md#d19), [D22](../OWNER_DECISIONS_17_36.md#d22), [D35](../OWNER_DECISIONS_17_36.md#d35)
- Input evidence: P01 original objective, current auction context, session, acquired liquidity, delivery path, candidate proximity/timeframe.
- Earliest evaluation/cutoff: Original bias/objective frozen before later ranking update; new information new assessment.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: Contextual candidate ranking rather than nearest target; preserve original objective/bias and earlier evidence; tie/conflict treatment unspecified.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited P22](../PREDICATE_READINESS_REGISTER_V0.3.md#p22).

### S-DISC — model_discovery_predicate

- Stable ID: IMAF-SESSION-GOVERNANCE-v0.2::model_discovery_predicate.
- Decision source/prerequisites: [D17](../OWNER_DECISIONS_17_36.md#d17)/[D18](../OWNER_DECISIONS_17_36.md#d18)/[D20](../OWNER_DECISIONS_17_36.md#d20)–[D24](../OWNER_DECISIONS_17_36.md#d24)/[D36](../OWNER_DECISIONS_17_36.md#d36)
- Input evidence: Original qualifying event/boundary, actual availability, setup/model/version, exact CT windows
- Earliest evaluation/cutoff: No discovery before qualifying evidence available; window membership at selected discovery event time.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D17](../OWNER_DECISIONS_17_36.md#d17) supplies four exact CT windows; existing helper only outer opening/cutoff. Model-specific qualifying event availability remains undefined; probe discrepancies documented. Scoped helper enforces selected outer constraints, not an independent canonical model.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited S-DISC](../PREDICATE_READINESS_REGISTER_V0.3.md#s-disc).

### S-EXP — model_expiry_predicate

- Stable ID: IMAF-SESSION-GOVERNANCE-v0.2::model_expiry_predicate.
- Decision source/prerequisites: [D17](../OWNER_DECISIONS_17_36.md#d17)/[D18](../OWNER_DECISIONS_17_36.md#d18)/[D36](../OWNER_DECISIONS_17_36.md#d36)
- Input evidence: Original discovery identity, finite absolute bound, rule/authority/version, original cutoff and updates
- Earliest evaluation/cutoff: Original finite bound fixed by selected model rule/source at original setup; never refreshed by later candles.
- Exact rule: `null`; status **UNRESOLVED**. No executable semantics added.
- Missing measurable semantics: [D17](../OWNER_DECISIONS_17_36.md#d17) finite expiry deadline source/maximum lifetime remains explicitly unresolved. Fresh recovery event cannot extend/relabel old identity; historical replay is not a new opportunity. Scoped helper enforces selected outer constraints, not an independent canonical model.
- Failure/tests: common contract above; no positive canonical confirmation. Original full record: [inherited S-EXP](../PREDICATE_READINESS_REGISTER_V0.3.md#s-exp).

## Four separate governance approval slots — unchanged

Source: Trading `research/governance/IMAF-OPERATIONAL-QUESTIONS.json`. `LIQUIDITY_ACCEPTANCE_REJECTION_OPERATIONAL_DEFINITION`, `ACCEPTED_STRUCTURAL_TRANSITION_OPERATIONAL_DEFINITION`, `NARRATIVE_COHERENCE_OPERATIONAL_DEFINITION`, `DISCOVERY_WINDOW_AND_SETUP_EXPIRY_POLICY` each retain `approvedDefinition: null`. These are approval slots, not four additional approved predicates or a second registry. New research geometry cannot activate them. Inputs/prerequisites: owner-approved versioned definitions and evidence required by the corresponding inherited predicates. Earliest evaluation: only after such approval and available evidence. Exact rule: null; UNRESOLVED. Failure: withhold canonical confirmation. Test: static null preservation plus F.

## New engineering/research predicates

These IDs document the new offline boundary; they do not replace canonical P09/P12 or establish selected MSS references. The implementation may use different API names but must crosswalk to these obligations.

| Stable ID | Decision source | Inputs and causal prerequisites | Earliest evaluation | Exact rule / status | Failure behavior | Acceptance tests |
|---|---|---|---|---|---|---|
| ENG-53-IDENTITY | D53 §7 | Instrument, timeframe, source/data version, immutable event payload | On validated event receipt | APPROVED engineering: deterministic event identity binds underlying market event; observation identity additionally binds derivation/spec/version/dependencies. Different labels cannot make one event independent. | INVALID conflicting immutable identity; never silently overwrite | E/G, duplicate and revision adversaries |
| ENG-53-CUTOFF | D53 §§7–10 | UTC event/completion/availability/classification times | Max completed dependency availability | APPROVED engineering: no incomplete/future dependency at cutoff; classification at/after availability; preserve event time separately | Explicit unavailable/unresolved; no historical backdating | A/B/D/G, delayed receipt/lookahead |
| ENG-53-LINEAGE | D53 §§7/10 | Event IDs and observation dependency DAG | Once all referenced dependencies known | APPROVED engineering: retain transitive underlying event set; shared-event observations must disclose overlap, not count as independent confirmation | INVALID unknown/cyclic links; unresolved independence sufficiency | C/E, shared displacement/aggregation |
| GEO-53-3 | D53 §8 | Center plus one completed adjacent candle each side, same instrument/timeframe/source profile | Max three availability times, after right candle completes | APPROVED cardinality only: 3-candle neighborhood, center at index1. No default high/low comparison rule selected | UNRESOLVED_COMPARISON_RULE without explicit research profile; missing bars non-confirming | A, equal/missing/late/out-of-order |
| GEO-53-5 | D53 §8 | Center plus two completed adjacent candles each side | Max five availability times, after second right candle completes | APPROVED cardinality only: 5-candle neighborhood, center at index2. No default comparison selected | UNRESOLVED_COMPARISON_RULE without explicit research profile | B, equal/missing/late/out-of-order |
| GEO-53-STRICT-RESEARCH | D53 §8 permits labeled research configuration | Explicit comparison-rule version; complete 3/5 neighborhood; tick-consistent OHLC | Same as GEO-53-3/5 | APPROVED **research configuration only**: strict high > every neighbor high, strict low < every neighbor low, if caller explicitly selects this hypothesis; equal extremes remain unresolved under unspecified tie policy. Not canon approval. | Default unresolved; no tie winner or tolerance inferred | Strict highs/lows; equality; dual extrema; no default activation |
| GEO-53-OVERLAP | D53 §§7–10 | Same center event and 3/5 observations with lineage | When each geometry separately knowable | APPROVED engineering: retain distinct resolution observations and shared event identity; 5-candle recognition cannot backdate 3-candle state or double confirmation count | Shared provenance label; no independence promotion | C/G |
| STRUCT-53-CONFIRMED-SWING | D23 and D37–41; D53 §9 | Candidate geometry + independent approved contextual confirmation evidence | Only after approved predicate and dependencies available | UNRESOLVED; exact rule null. Geometric completion is not structural confirmation | UNRESOLVED_STRUCTURAL_CONFIRMATION | D/F |
| STRUCT-53-SIGNIFICANCE | D23/24, D37–46 | Structurally confirmed swing, controlling range, external/internal context | Only after independent prior context exists | UNRESOLVED; exact rule null | UNRESOLVED_STRUCTURAL_SIGNIFICANCE | D/F; retrospective reference |
| STRUCT-53-MSS-REFERENCE | D28/29, D37–46 | Prior eligible significant swing and range selection, availability before break | Eligibility fixed before break; no later qualification at historical break | UNRESOLVED; exact rule null; future break cannot prove reference significance | UNRESOLVED_MSS_REFERENCE; no accepted transition | D/F |
| REPLAY-53-DETERMINISM | D53 §10 | Identical immutable events, cutoff schedule, config/spec versions and lineage | At each replay cutoff | APPROVED engineering: equal inputs/versions produce equal IDs, classifications, causal timestamps and reasons; changed dependencies not silently equivalent | Observable replay mismatch/unavailable | G; shuffled receipt/order/restart |
| LIFE-53-NO-REVIVAL | D18/36; D47–49; D53 §§10/11 | Original setup ID, terminal state, historical evidence dependencies | On attempted transition/update | APPROVED boundary: INVALIDATED/EXPIRED never return to live state; renamed identity/reused evidence cannot establish fresh discovery. Actual fresh-discovery sufficiency remains null. | Terminal state persists; new setup unresolved without independent qualification | H |
| SESSION-53-PRESERVE | D17; D53 §11 | Existing session specification and test fixtures | Existing policy cutoff | APPROVED retained boundaries: America/Chicago; [07:30,07:35),[07:50,07:55),[08:10,08:15),[08:30,10:00); morning entry before10:15; fresh afternoon discovery from12:00; flatten15:00; finite nonextending expiry; one/exchange day;48h error pause. No existing implementation changes in this increment. | Missing calendar/account/model proof never grants eligibility; old helper gaps remain explicit | Existing session regressions; no policy-diff assertion |
| AUTH-53-DENY | D53 §§1/12/14 | Every output | Always | APPROVED engineering: execution authorization DENIED; no broker/network/order path introduced | Fail closed; no executable approval | Static imports/safety and offline network denial |

## Prohibited predicates and assumptions

| ID | Decision source / inputs | Prohibited exact rule | Failure and tests |
|---|---|---|---|
| BAN-53-ATTRIBUTION | D53 §3 / OHLC observations | “Price geometry proves actual institutional actor or order flow.” | Never emit attribution confirmation; E/F |
| BAN-53-AUTO-PROMOTION | D53 §§3/9 / pivot,MSS,FVG,displacement | “Observed geometry automatically proves significant swing, accepted transition or narrative.” | Explicit unresolved; D/F |
| BAN-53-HINDSIGHT | D53 §§6/10 / later bars or break | “Later outcome selects prior range/reference/bias or backdates availability.” | Reject or withhold; A/B/D/G |
| BAN-53-DOUBLECOUNT | D53 §7 / repeated observation labels | “Multiple derivations of shared event are independent confirmations.” | Preserve overlap; C/E |
| BAN-53-INTRABAR | D53 §8 / OHLC | “OHLC extrema reveal intrabar event ordering.” | Unknown sequence; adversarial same-bar fixture |
| BAN-53-DEFAULTS | D53 §§4/6/8 / null owner predicates | “Conventional ICT constants, strict/equality tolerances or proposed draft definitions become approved by implementation.” | Null preservation, explicit research config only; F |
| BAN-53-REVIVAL | D53 §§10/11 / terminal setup | “New label or replay revives invalidated/expired setup or refreshes expiry/count.” | Terminal state, H |

Prohibited rules have no valid evaluation timestamp; no amount of available evidence authorizes these inference shortcuts. Approval of a measurable replacement requires a new owner decision, preserved version and tests.

## Explicit dealing-range dependency

Independent prior range candidates → owner-approved controlling-range selection → contextual swing significance → eligible pre-break structural reference → observed break → independent persistence/delivery evidence → accepted transition. Geometric recognition can run without range selection. Contextual selection cannot use the transition it is meant to prove. Range replacement and new context require subsequent evidence and a new classification time, never rewriting prior eligibility. See [dependency review](DEPENDENCY_AND_CIRCULARITY.md).

## Audit completion boundary

Phase 53.1 scoped inventory is complete for this increment before new analytical logic. It records 24 inherited null scoped records, four separate null approval slots, 14 new engineering/research obligations and seven prohibited shortcuts. These are different namespaces and **must not be summed into an approved-strategy count**. Actual runtime implementation and tests remain subject to independent acceptance verification.

## Supplied D37–52 individual-rule crosswalk

The actual owner source `/home/rain/Downloads/IMAF_Decision_Records_37-52.md` is now available; all selections D. This completes source traceability; it does **not** approve unresolved sufficient rules. The following are leaf obligations inside inherited compounds or new blocked engineering transitions; they are not a new approved registry. Every exact sufficient trading rule below remains `null` / UNRESOLVED.

| Decision / leaf | Input evidence / causal prerequisite | Earliest evaluation | Unresolved exact rule / failure | Test obligation |
|---|---|---|---|---|
| D37 reference ranking; STRUCT-53-MSS-REFERENCE | Prior controlling range and confirmed significant swings, selection timestamp | Before evaluated MSS, after prerequisites | Eligible-reference ranking null; no reference confirmation | D/F |
| D38/D40 promotion; STRUCT-53-CONFIRMED-SWING | Geometric candidate plus independent model-specific context | After geometry and contextual evidence | Structural confirmation/significance null; withhold promotion | F |
| D39 geometry; GEO-53-3/5/STRICT-RESEARCH | Complete ordered 3/5 bars | Last right-bar receipt/completion | Default comparison/ties/missing behavior not approved; missing or ties unresolved | A/B/C |
| D41 confirmation-route eligibility; P09/P12 | Pre-outcome model/timeframe/context, displacement/liquidity/departure evidence | Route fixed before outcome, confirmation after evidence | Route eligibility/sufficiency/conflict rule null | D/F/G |
| D42 candidate/control range; P12 | Previously confirmed boundaries, prior objective/accepted context | Selection before range-dependent MSS/PD/OTE | Construction/selection null; no controlling range | D/F |
| D43 competing ranges; P12 | All competing ranges, HTF objective/session/independent delivery | After relevant evidence, no retrospective fit | Comparison/ties null; STAND_ASIDE for range-dependent qualification | Contradictory range/F |
| D44 replacement; P12 | Fresh independent liquidity/structure/delivery, old range retained | At later replacement evidence availability | Replacement/internal evolution null; no replacement | Lookahead/G |
| D45 internal/external; P09/P12 | Pre-established controlling range/references/objective, independent delivery | After causal references/context | Crossing/classification null; qualification withheld | D/F |
| D46 external-significance promotion; P09/P11/P12 | Independent structural acceptance/liquidity/later delivery | Later evidence availability; preserve original internal state | Sufficiency/persistence null; unresolved promotion | D/F/G |
| D47 narrative revision; P13 | Accepted transition/response/participation/independent delivery | After each distinct approved dependency | State-transition sufficiency null; UNRESOLVED, no automatic reversal | F/G |
| D48 invalidation; P08/P13/P17 | Discovery-time narrative snapshot and later contradiction | Contradiction availability before entry | Invalidation dependency sufficiency null; unsupported eligibility withheld, terminal state preserved | H |
| D49 fresh discovery; P16/P17 | Genuinely new independently qualified event under revised narrative | New event availability within existing window | Minimum new evidence/reuse null; no fresh qualification | H |
| D50 provenance; ENG-53-IDENTITY/LINEAGE | Source event/observation/evidence-role/model dependencies | On validated receipt/classification | Engineering lineage allowed; fresh/independence sufficiency still null | C/E/G/H |
| D51 independence; P05/P10 + ENG-53-LINEAGE | Underlying event boundaries and aggregation/dependency graph | After dependencies known, before confirmation | Distinct labels/timeframes insufficient; minimum independence null | C/E/F |
| D52 delivery routes; P10/P11 | Subsequent evidence independent of original break; prior eligible route | Route fixed before outcome; confirmation after later evidence | Continuation/retest/FVG route sufficiency null; no accepted transition | E/F/G |

Shared-event exclusion is an engineering necessary condition, **not** proof that disjoint event IDs alone satisfy canonical evidence independence. D50's proposed fields and D47's TRANSITION_UNDER_REVIEW remain proposals, not approved runtime contract/state changes. D48 does not authorize closing positions.
