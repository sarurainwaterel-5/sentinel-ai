# Human review packet — no executable approval

Status: DRAFT / UNRESOLVED. This packet adds no numerical thresholds. Reuse Trading's
existing `research/governance/proposals/imaf-operational-v0.1.json` for its explicitly
labeled proposed acceptance/transition/narrative/expiry definitions; do not create a
parallel approved doctrine or silently activate that draft's numbers.

For each definition below the proposed approval shape is:

`{id, status:DRAFT_FOR_OWNER_REVIEW, predicate:null, required_inputs, availability_rule,
 contradiction_rule:null, invalidation_rule:null, scope, source_references}`.

A null predicate cannot pass. Owner review must select and version actual semantics,
then implementation and negative tests must follow. Reviewing this report is not
sufficient to clear Trading's registry/entry lock.

| Required definition | Proposed non-numerical structure for owner decision |
|---|---|
| Liquidity acceptance/rejection | Pin known boundary/acquisition and information cutoff; choose observable follow-through, persistence, contradiction and invalidation predicates. Decide whether existing draft semantics match canon. |
| Accepted structural transition | Pin the prior known structure and acquisition response; distinguish a research close break from accepted auction change. Select confirmation/invalidation semantics; no confirmation count invented here. |
| Narrative coherence | Pin objective, response, structural transition, participation observations, array, invalidation and required higher contexts. Define conflict resolution and independent participation evidence; forbid relabeling the same candles as independent evidence. |
| Discovery/expiry | Resolve early mission windows vs existing draft, acquisition availability vs decision time, post-09:30 explicit cutoff, setup identity and nonextending expiry propagation. No default later cutoff is supplied by this implementation. |
| HTF directional bias | Select the versioned directional predicate and required context set, range selection and conflict/neutral handling. Midpoint location alone must not become directional conviction. |
| PD-array / price-delivery alignment | Decide which computed arrays are eligible and how they depend on preceding auction evidence; define invalidation and competing-array treatment. Presence alone cannot authorize entry. |
| Market out of balance | Define observable source inputs, horizon, predicate, unknown state and recovery/invalidation. No volatility, range or imbalance threshold is invented. |
| Liquidity significance/target ranking | Define source calendars and eligible pool sets, equal-level treatment, objective ranking, availability and expiry. Current explicit-window extrema are research observations only. |
| Trading day/calendar | Resolve NY calendar date vs exchange session/rollover, holidays and clock policy. Current daily counter check is an explicit synthetic NY-date convention, not verified exchange coverage. |

The source registry's four approvedDefinition values remain null. Additional gaps
are listed in the pinned research specification. Future accepted definitions require
new versioned specification/evaluator artifacts; immutable historical records must
retain their original hashes and replay context. There is no caller-provided
approved:true or rules override that clears this boundary.
