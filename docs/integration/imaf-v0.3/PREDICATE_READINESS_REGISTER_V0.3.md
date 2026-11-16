# Predicate readiness register v0.3

**DRAFT — NOT APPROVED FOR EXECUTION.**

## Observed inventory and counting convention

Inspected actual files at Sentinel52d881d and Tradinga726709:

| Inventory | Observed count | Null status | Counting treatment |
|---|---:|---|---|
| v0.2 PREDICATE_DEFINITION_REGISTER.md explicit P01–P22 |22|22 literal executable predicates null|Canonical proposed records reviewed below; compound records are not proven atomic algorithms |
| session_governance_v02/specification.json model_discovery_predicate/model_expiry_predicate |2|2 null|Separately scoped executable hooks, reviewed as S-DISC/S-EXP; overlap P16/P17 conceptually |
| Trading IMAF-OPERATIONAL-QUESTIONS.json approvedDefinition |4|4 null|Approval slots cross-mapped below, not four additional distinct predicate algorithms |
| Phase3 specification unresolved + additional_unresolved |4+6|Unresolved obligations|References/requirements, not ten new executable-definition records |
| Session morning_opens_at |1|null parameter|Not a predicate; [D17](OWNER_DECISIONS_17_36.md#d17) now specifies four model windows in doctrine, existing JSON unchanged |

**24 scoped predicate-definition records reviewed; all24 still null.** This counts
22 canonical records plus2 scoped hooks, not24 distinct conceptual algorithms.
Four separate governance approval slots remain null. No registry file is activated,
renumbered or replaced. Newly clarified leaf distinctions remain obligations mapped
to these records, not silently fabricated implementations or an approved registry.

Version of this audit:0.3.0-draft. Current versions below describe inspected artifacts,
not an executable v0.3 release. Positive/negative evidence lists are necessary
constraints and research observations, never sufficient executable predicates.

Shared replay obligations referenced in each record: preserve the exact original
input/evidence snapshot, source and availability timestamps, information cutoff and
evaluation time, specification/evaluator/model versions and hashes, calendar identity/
version, original finite expiry and assessment/reasons. Replay may not add future
candles or current-policy assumptions. Missing required historical dependencies means
unavailable; contradiction is separately recorded, never an overwrite. These are
nonexecuting specification obligations, not changes to the existing receipt schema.

<a id="p01"></a>

## P01 — LIQUIDITY_OBJECTIVE_SELECTION

- **Predicate identifier:** `IMAF-V02-LIQUIDITY_OBJECTIVE_SELECTION` (P01)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC5/68; P /definitions/2/proposal/requiredRelations/0; S.additional_unresolved; M2 D7/D10. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D7/D10; current owner refinements: [D19](OWNER_DECISIONS_17_36.md#d19), [D22](OWNER_DECISIONS_17_36.md#d22), [D24](OWNER_DECISIONS_17_36.md#d24)
- **Required inputs:** Known objective candidates, larger-context evidence, session context, already-acquired flags and candidate source times.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Approved analysis timeframe and larger objective context; no fallback vote.
- **Information cutoff:** Objective selected before acquisition interpretation; retain original selection time.
- **Positive evidence:** A preexisting objective supported by larger auction evidence; selection predicate null.
- **Negative evidence:** Objective invented after the move; automatic nearest/highest-timeframe winner.
- **Contradictory evidence:** Competing objectives with unresolved contextual priority.
- **Invalidation behavior:** Selected objective demonstrably acquired/invalidated under an approved rule, still null.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Objective/context expiry requires owner-defined bounds; no indefinite relevance.
- **Replay requirements:** exact common replay policy above plus original P01 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** Controlling objective/significance must not depend on the bias it is used to prove; distinguish initial candidates from later contextual ranking.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** BLOCKED_BY_DEPENDENCY. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p02"></a>

## P02 — LIQUIDITY_ACQUISITION

- **Predicate identifier:** `IMAF-V02-LIQUIDITY_ACQUISITION` (P02)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC2/2, CC9/72; P /definitions/0/proposal/reference; E STRICT_SWEEP; M2 D1. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D1/D10; current owner refinements: [D17](OWNER_DECISIONS_17_36.md#d17), [D20](OWNER_DECISIONS_17_36.md#d20), [D21](OWNER_DECISIONS_17_36.md#d21), [D22](OWNER_DECISIONS_17_36.md#d22), [D23](OWNER_DECISIONS_17_36.md#d23)
- **Required inputs:** Pinned objective/boundary, instrument, closed OHLCV, event/availability times.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Execution member of approved pair with source objective timeframe retained.
- **Information cutoff:** Boundary known before acquisition; exact onset-vs-close availability rule unresolved.
- **Positive evidence:** Observable acquisition of selected liquidity; incidental touch distinction null.
- **Negative evidence:** Using a later-selected level or a missing acquisition as if observed.
- **Contradictory evidence:** Equal/touched boundary vs genuine acquisition; noisy excursion without significance.
- **Invalidation behavior:** Later data correction recorded separately; no original-event rewrite.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Subject to original setup/context expiry once approved.
- **Replay requirements:** exact common replay policy above plus original P02 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D20](OWNER_DECISIONS_17_36.md#d20)/[D21](OWNER_DECISIONS_17_36.md#d21) now separate penetration facts from significant acquisition/return/confirmation. Boundary provenance/tick/causal interaction profile still not approved.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p03"></a>

## P03 — QUALIFYING_DISPLACEMENT

- **Predicate identifier:** `IMAF-V02-QUALIFYING_DISPLACEMENT` (P03)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C physical60–62; P /definitions/1/proposal/sequence; S.rules; E RESEARCH_DISPLACEMENT; M2 D1/D4. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D1/D4; current owner refinements: [D27](OWNER_DECISIONS_17_36.md#d27), [D29](OWNER_DECISIONS_17_36.md#d29), [D32](OWNER_DECISIONS_17_36.md#d32)
- **Required inputs:** Closed directional OHLCV, prior-only comparison history, instrument tick metadata.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Execution timeframe plus contextual analysis refs.
- **Information cutoff:** Comparison inputs and displacement available by cutoff, no later baseline.
- **Positive evidence:** Qualifying directional displacement under selected rule; numerical predicate null.
- **Negative evidence:** One large candle treated as institutional identification.
- **Contradictory evidence:** Opposing delivery, range expansion without coherent commitment.
- **Invalidation behavior:** Later evidence can weaken interpretation without erasing original candle fact.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Relevance horizon/context validity unresolved.
- **Replay requirements:** exact common replay policy above plus original P03 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D27](OWNER_DECISIONS_17_36.md#d27) gives context dimensions, not body/range/baseline thresholds. Same candle may support MSS but is not additional independent confirmation.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p04"></a>

## P04 — PROVISIONAL_REJECTION

- **Predicate identifier:** `IMAF-V02-PROVISIONAL_REJECTION` (P04)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C physical25, CC9/72; P /definitions/0/proposal/rejection; E STRICT_SWEEP; M2 D1. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D1; current owner refinements: [D17](OWNER_DECISIONS_17_36.md#d17), [D20](OWNER_DECISIONS_17_36.md#d20), [D33](OWNER_DECISIONS_17_36.md#d33)
- **Required inputs:** P02 acquisition, known boundary, qualifying inside return, P03 displacement, timestamps.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Execution timeframe and paired larger-context references.
- **Information cutoff:** Each component observable by provisional classification time; same-bar vs later-bar rule unresolved.
- **Positive evidence:** Owner requires sweep then qualifying inside return with displacement, provisional only.
- **Negative evidence:** Sweep alone, return without qualified displacement, label of confirmed rejection.
- **Contradictory evidence:** Return that immediately reclaims boundary; competing continuation interpretation.
- **Invalidation behavior:** P08 qualifying reclaim plus opposite acceptance; pending exact semantics.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Original finite setup expiry required for any lifecycle use; no invented duration.
- **Replay requirements:** exact common replay policy above plus original P04 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** Prior D1 return+displacement is provisional; [D17](OWNER_DECISIONS_17_36.md#d17)/[D20](OWNER_DECISIONS_17_36.md#d20) discovery is earlier acquisition, not the same response conclusion.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** BLOCKED_BY_DEPENDENCY. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p05"></a>

## P05 — CONTEXTUAL_PARTICIPATION

- **Predicate identifier:** `IMAF-V02-CONTEXTUAL_PARTICIPATION` (P05)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C physical59–62; P /definitions/2/proposal/participationProposal; S.additional_unresolved; M2 D4. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D4; current owner refinements: [D26](OWNER_DECISIONS_17_36.md#d26), [D27](OWNER_DECISIONS_17_36.md#d27), [D32](OWNER_DECISIONS_17_36.md#d32)
- **Required inputs:** Larger objective, liquidity behavior, displacement, subsequent delivery and alternative explanations.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Relevant analysis/execution contexts, source interval retained.
- **Information cutoff:** Only observations already available; subsequent evidence changes a later record.
- **Positive evidence:** Converging contextual evidence of meaningful participation, never institutional identity.
- **Negative evidence:** Displacement alone, assumed narrative or renamed same-bar FVG counted as proof.
- **Contradictory evidence:** Contradictory follow-through, objective conflict, dependence disguised as convergence.
- **Invalidation behavior:** Approved contradiction rule may withdraw inference in a later assessment; null.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Validity horizon and context-change rule unresolved.
- **Replay requirements:** exact common replay policy above plus original P05 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D32](OWNER_DECISIONS_17_36.md#d32) needs dependency-aware independent evidence and source applicability; optional volume/orderflow cannot be fabricated or silently made universally mandatory.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p06"></a>

## P06 — LIQUIDITY_ACCEPTANCE

- **Predicate identifier:** `IMAF-V02-LIQUIDITY_ACCEPTANCE` (P06)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC5/68, CC9/72; P /definitions/0/proposal/acceptance; R response question; M2 D3. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D2/D3; current owner refinements: [D20](OWNER_DECISIONS_17_36.md#d20), [D34](OWNER_DECISIONS_17_36.md#d34)
- **Required inputs:** Known boundary, acquisition side, directional response, persistence/delivery context.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Execution timeframe with paired context.
- **Information cutoff:** Acceptance evidence must precede its use in invalidation or confirmation.
- **Positive evidence:** Qualifying acceptance through liquidity under selected rule, currently null.
- **Negative evidence:** Temporary crossing or single draft close automatically called acceptance.
- **Contradictory evidence:** Concurrent apparent acceptance/rejection, neutral/equal boundary behavior.
- **Invalidation behavior:** Opposing qualified response; exact reversal/neutral handling unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Finite response/context validity to be selected.
- **Replay requirements:** exact common replay policy above plus original P06 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D34](OWNER_DECISIONS_17_36.md#d34) requires contextual response evidence; no selected count, retest sufficiency or conjunction/alternative rule.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p07"></a>

## P07 — REJECTION_CONFIRMATION_ROUTE

- **Predicate identifier:** `IMAF-V02-REJECTION_CONFIRMATION_ROUTE` (P07)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C physical60–62, CC4/67; P /definitions/0 and /definitions/1; R response/transition; M2 D2. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D2; current owner refinements: [D33](OWNER_DECISIONS_17_36.md#d33)
- **Required inputs:** P04 provisional rejection, P05 participation, pre-event larger-context interpretation, structural or persistence evidence.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Approved pair with context-specific route eligibility.
- **Information cutoff:** No final narrative/accepted transition from same assessment used as its prerequisite.
- **Positive evidence:** Eligible structural OR persistence route may suffice; eligibility/sufficiency null.
- **Negative evidence:** Always require both, unconditional OR, or structural line break alone.
- **Contradictory evidence:** Route-eligibility ambiguity; two routes supporting opposite conclusions.
- **Invalidation behavior:** P08 qualified invalidation or contradiction rules once selected.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Cannot confirm at/after original expiry or renew expired context.
- **Replay requirements:** exact common replay policy above plus original P07 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D33](OWNER_DECISIONS_17_36.md#d33) eligibility must be pinned prospectively; structural route must not require the same accepted transition that requires its own confirmed response.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** BLOCKED_BY_DEPENDENCY. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p08"></a>

## P08 — REJECTION_INVALIDATION

- **Predicate identifier:** `IMAF-V02-REJECTION_INVALIDATION` (P08)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C physical24–26; P /definitions/0/proposal/invalidation; R response; M2 D3. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D3; current owner refinements: [D18](OWNER_DECISIONS_17_36.md#d18), [D33](OWNER_DECISIONS_17_36.md#d33), [D34](OWNER_DECISIONS_17_36.md#d34)
- **Required inputs:** Original rejection identity, qualifying reclaim, P06 opposite acceptance, cutoff.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Original execution timeframe with larger-context refs.
- **Information cutoff:** Reclaim and acceptance both available when invalidation is asserted.
- **Positive evidence:** Owner requires qualifying reclaim accompanied by opposite acceptance.
- **Negative evidence:** Temporary crossing or unqualified single opposite close treated as invalidation.
- **Contradictory evidence:** Reclaim seen but acceptance missing/contradicted; unknown is not confirmation.
- **Invalidation behavior:** This predicate invalidates rejection; revalidation/re-entry semantics remain unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** No resurrection/extension of expired original setup.
- **Replay requirements:** exact common replay policy above plus original P08 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D18](OWNER_DECISIONS_17_36.md#d18) invalidation requires approved contradiction; prior D3 reclaim+opposite acceptance not a single contrary close; same-instant conflict unresolved.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** BLOCKED_BY_DEPENDENCY. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p09"></a>

## P09 — STRUCTURAL_PERSISTENCE

- **Predicate identifier:** `IMAF-V02-STRUCTURAL_PERSISTENCE` (P09)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC4/67; P /definitions/1/proposal; E STRUCTURAL_CLOSE_BREAK; M2 D5. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D5; current owner refinements: [D22](OWNER_DECISIONS_17_36.md#d22), [D23](OWNER_DECISIONS_17_36.md#d23), [D28](OWNER_DECISIONS_17_36.md#d28), [D29](OWNER_DECISIONS_17_36.md#d29), [D30](OWNER_DECISIONS_17_36.md#d30)
- **Required inputs:** Preknown structure/swing, observed close break, subsequent structural observations.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Execution timeframe, preexisting analysis references.
- **Information cutoff:** Pivot selection/confirmation known before event; persistence observable before use.
- **Positive evidence:** New structural organization persists under rule to be selected.
- **Negative evidence:** MSS or isolated close alone called accepted transition.
- **Contradictory evidence:** Recross/failed follow-through, changed swing chosen to rescue setup.
- **Invalidation behavior:** Qualifying old-structure recovery; exact conditions null.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Finite setup/context horizon applies; number of bars not inferred.
- **Replay requirements:** exact common replay policy above plus original P09 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D23](OWNER_DECISIONS_17_36.md#d23)/[D28](OWNER_DECISIONS_17_36.md#d28)–[D30](OWNER_DECISIONS_17_36.md#d30) require candidate/confirmed/significant distinction, break classification and persistence. Research pivot geometry alone supplies no canonical significance.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p10"></a>

## P10 — PRICE_DELIVERY_CONFIRMATION

- **Predicate identifier:** `IMAF-V02-PRICE_DELIVERY_CONFIRMATION` (P10)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC5/68, physical60–62; P /definitions/2/proposal/requiredRelations; M2 D4/D5. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D4/D5; current owner refinements: [D26](OWNER_DECISIONS_17_36.md#d26), [D27](OWNER_DECISIONS_17_36.md#d27), [D31](OWNER_DECISIONS_17_36.md#d31), [D32](OWNER_DECISIONS_17_36.md#d32)
- **Required inputs:** Earlier liquidity event, raw follow-through/delivery observations, alternative paths.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Execution timeframe and contextual analysis provenance.
- **Information cutoff:** Delivery observed before transition inference; no completed later narrative prerequisite.
- **Positive evidence:** Observed delivery consistent with proposed reorganization; sufficiency null.
- **Negative evidence:** FVG presence or chosen trade direction used as sole confirmation.
- **Contradictory evidence:** Opposite delivery/overlap or ambiguous path, without invented numeric cutoffs.
- **Invalidation behavior:** Selected contradictory delivery rule, unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Finite setup/context validity; later bars create later evidence only.
- **Replay requirements:** exact common replay policy above plus original P10 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D31](OWNER_DECISIONS_17_36.md#d31) later delivery cannot be satisfied solely by original MSS candle; independent additional information and sufficient progress/contradiction remain undefined.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p11"></a>

## P11 — ACCEPTED_STRUCTURAL_TRANSITION

- **Predicate identifier:** `IMAF-V02-ACCEPTED_STRUCTURAL_TRANSITION` (P11)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC4/67; P /definitions/1; R transition question; M2 D5. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D5; current owner refinements: [D18](OWNER_DECISIONS_17_36.md#d18), [D28](OWNER_DECISIONS_17_36.md#d28), [D29](OWNER_DECISIONS_17_36.md#d29), [D30](OWNER_DECISIONS_17_36.md#d30), [D31](OWNER_DECISIONS_17_36.md#d31), [D34](OWNER_DECISIONS_17_36.md#d34)
- **Required inputs:** Preceding liquidity response/participation, P09 persistence AND P10 delivery confirmation.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Approved analysis/execution pair.
- **Information cutoff:** All prerequisites available before accepted-transition record.
- **Positive evidence:** Owner conjunction necessary; full sufficient predicate remains null.
- **Negative evidence:** Line break/MSS alone, selected long/short direction, or future delivery.
- **Contradictory evidence:** Persistence supports transition while delivery contradicts it.
- **Invalidation behavior:** Qualified structural/delivery contradiction, exact rule null.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** No confirmation after expired setup/context; expiry rule pending.
- **Replay requirements:** exact common replay policy above plus original P11 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** Persistence AND independent delivery necessary, not sufficient by labeling. Pre-response participation/response dependencies must be noncircular.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** BLOCKED_BY_DEPENDENCY. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p12"></a>

## P12 — HIERARCHICAL_CONTEXT

- **Predicate identifier:** `IMAF-V02-HIERARCHICAL_CONTEXT` (P12)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C physical61, CC5/68; P /definitions/2/proposal/requiredRelations/5 and /definitions/3/proposal/hierarchy; S.hierarchy; M2 D7. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D7; current owner refinements: [D19](OWNER_DECISIONS_17_36.md#d19), [D22](OWNER_DECISIONS_17_36.md#d22), [D23](OWNER_DECISIONS_17_36.md#d23), [D24](OWNER_DECISIONS_17_36.md#d24), [D25](OWNER_DECISIONS_17_36.md#d25), [D28](OWNER_DECISIONS_17_36.md#d28), [D35](OWNER_DECISIONS_17_36.md#d35)
- **Required inputs:** P01 larger objective, required timeframe contexts, lower movement evidence.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Exactly 4H→15M, 1H→5M, 15M→1M or 5M→15S; required larger context set unresolved.
- **Information cutoff:** Larger-context evidence known at its use; freeze interpretation before evaluating lower outcome.
- **Positive evidence:** Lower behavior interpreted within larger objective, no voting; predicate null.
- **Negative evidence:** Majority vote, midpoint substituted for directional bias, omitted contrary context.
- **Contradictory evidence:** Countertrend movement can be retracement/acquisition/reversal/unresolved.
- **Invalidation behavior:** Larger objective/context invalidation in a later record.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Context age/expiry rule unresolved, no assumed continuous validity.
- **Replay requirements:** exact common replay policy above plus original P12 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D19](OWNER_DECISIONS_17_36.md#d19)/[D24](OWNER_DECISIONS_17_36.md#d24) hierarchy/range anchors and update rules cannot be fitted to OTE or favorable target; exact mappings selected but context producer incomplete.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p13"></a>

## P13 — NARRATIVE_CLASSIFICATION_AND_COHERENCE

- **Predicate identifier:** `IMAF-V02-NARRATIVE_CLASSIFICATION_AND_COHERENCE` (P13)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC5–6/68–69, CC9/72; P /definitions/2; R narrative question; M2 D6. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D6; current owner refinements: [D18](OWNER_DECISIONS_17_36.md#d18), [D26](OWNER_DECISIONS_17_36.md#d26), [D35](OWNER_DECISIONS_17_36.md#d35), [D36](OWNER_DECISIONS_17_36.md#d36)
- **Required inputs:** P01/P05/P06/P07/P11/P12 and delivery evidence, competing explanations, invalidation hypothesis.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Approved pair with relevant larger narrative context.
- **Information cutoff:** Synthesis after prerequisite observations; later verification cannot backfill it.
- **Positive evidence:** Falsifiable coherent interpretation; category boundaries/sufficiency null.
- **Negative evidence:** FVG alone, countertrend automatically invalid, profitable outcome as proof.
- **Contradictory evidence:** Multiple evidence-consistent categories or contradictory prior stages.
- **Invalidation behavior:** Approved prerequisite invalidation/context loss; preserve earlier assessment.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Narrative validity finite; timing and renewal rule unresolved.
- **Replay requirements:** exact common replay policy above plus original P13 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D35](OWNER_DECISIONS_17_36.md#d35) taxonomy now names confirmed reversal; earlier confirmed directional transition is not silently treated as identical operational state.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** BLOCKED_BY_DEPENDENCY. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p14"></a>

## P14 — PD_ARRAY_GEOMETRY_AND_CONTEXT

- **Predicate identifier:** `IMAF-V02-PD_ARRAY_GEOMETRY_AND_CONTEXT` (P14)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC5–6/68–69; P /definitions/2/proposal/requiredRelations/4; E THREE_CLOSED_BAR_FVG/LATER_FVG_OTE_ENTRY; M2 D8. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D8; current owner refinements: [D24](OWNER_DECISIONS_17_36.md#d24), [D25](OWNER_DECISIONS_17_36.md#d25), [D26](OWNER_DECISIONS_17_36.md#d26), [D31](OWNER_DECISIONS_17_36.md#d31)
- **Required inputs:** Array type/geometry/version, prior liquidity event, participation, transition, narrative and invalidation.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Execution location with registered contextual pair.
- **Information cutoff:** Geometry and context available by use; later retest cannot justify earlier classification.
- **Positive evidence:** Array fits preceding auction context; each unapproved geometry/eligibility predicate null.
- **Negative evidence:** Array presence authorizes entry; general IMAF forced through one ICT pattern.
- **Contradictory evidence:** Geometric array exists but contradicts narrative or lacks contextual evidence.
- **Invalidation behavior:** Qualified geometry/context failure; individual rule unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Array relevance cannot outlive original setup/context; exact rule pending.
- **Replay requirements:** exact common replay policy above plus original P14 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D25](OWNER_DECISIONS_17_36.md#d25) 78.6 is contextual precision only; [D26](OWNER_DECISIONS_17_36.md#d26) geometric/relevant/setup-qualified FVG distinct. Exact geometry profile/range/tick convention and model qualification remain incomplete.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p15"></a>

## P15 — OUT_OF_BALANCE_ASSESSMENT

- **Predicate identifier:** `IMAF-V02-OUT_OF_BALANCE_ASSESSMENT` (P15)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC9/72; P sharedSemantics.missingDataRule; E STAND_ASIDE_OUT_OF_BALANCE; M2 D9. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D9; current owner refinements: [D35](OWNER_DECISIONS_17_36.md#d35), [D36](OWNER_DECISIONS_17_36.md#d36)
- **Required inputs:** Auction evidence, P13 coherence/actionability reasoning, known missing inputs.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Relevant paired context, not volatility-only timeframe.
- **Information cutoff:** Classify only from evidence available at cutoff.
- **Positive evidence:** Owner coherence-based standaside; measurable classifier null.
- **Negative evidence:** Volatility/range/disagreement alone or supplied false flag establishes balance.
- **Contradictory evidence:** Apparent incoherence explained by coherent retracement or liquidity acquisition.
- **Invalidation behavior:** Recovery requires fresh coherent evidence under approved criteria; unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Stale coherence cannot imply balanced; review horizon null.
- **Replay requirements:** exact common replay policy above plus original P15 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** Reuse approved narrative coherence when available; [D36](OWNER_DECISIONS_17_36.md#d36) fresh evidence/recovery cannot revive old setup or manufacture balance from a supplied false flag.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** BLOCKED_BY_DEPENDENCY. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p16"></a>

## P16 — WINDOW_AND_DISCOVERY

- **Predicate identifier:** `IMAF-V02-WINDOW_AND_DISCOVERY` (P16)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC9/72; P /definitions/3/proposal/discoveryWindow and /discoveryEvent; E EXPLICIT_NY_TRADING_WINDOW; M2 D12. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D12; current owner refinements: [D17](OWNER_DECISIONS_17_36.md#d17)
- **Required inputs:** Versioned explicit NY window/session, acquisition/other selected discovery event and availability.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Approved analysis/execution pair and America/New_York wall-clock view.
- **Information cutoff:** Discovery event availability vs event-time selection unresolved; preserve both.
- **Positive evidence:** Discovery within owner window; exact trigger/endpoints null.
- **Negative evidence:** Confirmation time alone used as discovery, unrestricted post09:30, invented universal cutoff.
- **Contradictory evidence:** Event occurs in window but received later; discovery vs confirmation confused.
- **Invalidation behavior:** False/changed source window; setup consequences require explicit rule.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Window close limits discovery, not automatically setup expiry; P17 must define bound.
- **Replay requirements:** exact common replay policy above plus original P16 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D17](OWNER_DECISIONS_17_36.md#d17) supplies four exact CT windows; existing helper only outer opening/cutoff. Model-specific qualifying event availability remains undefined; probe discrepancies documented.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p17"></a>

## P17 — SETUP_LIFECYCLE_AND_EXPIRY

- **Predicate identifier:** `IMAF-V02-SETUP_LIFECYCLE_AND_EXPIRY` (P17)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC9/72; P /definitions/3/proposal/expiry and /expiryPropagation; Trading research-expiry.js; M2 D12. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D12; current owner refinements: [D17](OWNER_DECISIONS_17_36.md#d17), [D18](OWNER_DECISIONS_17_36.md#d18), [D36](OWNER_DECISIONS_17_36.md#d36)
- **Required inputs:** Immutable setup/acquisition IDs, P16 discovery, explicit finite bound, causal update events.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Approved pair; absolute UTC expiry retains NY context.
- **Information cutoff:** Expiry committed from approved inputs before continued evaluation; receipt delays cannot extend.
- **Positive evidence:** Owner DISCOVERED→DEVELOPING→CONFIRMED/INVALIDATED/EXPIRED; exact transitions null.
- **Negative evidence:** Nested/relabelled setup/reconnect silently extends life; no finite bound.
- **Contradictory evidence:** Confirmation vs expiry/invalidation same instant; new acquisition overlaps old setup.
- **Invalidation behavior:** Qualifying invalidation or expiry event; terminal precedence/supersession unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Finite nonextending expiry mandatory; duration/formula/source authority null.
- **Replay requirements:** exact common replay policy above plus original P17 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** [D17](OWNER_DECISIONS_17_36.md#d17) finite expiry deadline source/maximum lifetime remains explicitly unresolved. Fresh recovery event cannot extend/relabel old identity; historical replay is not a new opportunity.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p18"></a>

## P18 — EXCHANGE_TRADING_DAY_CALENDAR

- **Predicate identifier:** `IMAF-V02-EXCHANGE_TRADING_DAY_CALENDAR` (P18)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC7/70; P /definitions/3/proposal/calendarRule; E ONE_TRADE_PER_NY_DAY; M2 D11. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D11; current owner refinements: [D17](OWNER_DECISIONS_17_36.md#d17), [D22](OWNER_DECISIONS_17_36.md#d22), [D36](OWNER_DECISIONS_17_36.md#d36)
- **Required inputs:** Calendar ID/version/source, instrument/product, UTC intervals, exchange day IDs, holiday/exception coverage.
- **Authoritative data source:** Existing Trading market-calendar/sessionEligibility and validateCalendarManifests validate supplied reviewed inputs; actual authoritative exchange schedule/coverage not independently verified.
- **Evaluation timeframe:** Exchange session/trading-day horizon; NY clock is not identity.
- **Information cutoff:** Calendar version/effective coverage known before accounting decision.
- **Positive evidence:** One unambiguous exchange-aware day assignment; exact calendar policy null.
- **Negative evidence:** Midnight date fallback, adding24h schedules, caller labels certify exchange approval.
- **Contradictory evidence:** Exchange day differs from account day; missing/conflicting exceptions.
- **Invalidation behavior:** Version/effective coverage withdrawn; do not rewrite original accounting record.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Coverage bound explicit; unknown coverage blocks, no invented rollover time.
- **Replay requirements:** exact common replay policy above plus original P18 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** Existing Trading calendar/manifest validators can be reused; no authoritative covered calendar data demonstrated in this audit.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_DATA_SOURCE. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p19"></a>

## P19 — TRADING_DAY_AND_ACCOUNT_ALLOWANCE

- **Predicate identifier:** `IMAF-V02-TRADING_DAY_AND_ACCOUNT_ALLOWANCE` (P19)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC7/70; R.boundaries.maxEntriesPerSession; P reviewRequirements; E ONE_TRADE_PER_NY_DAY; M2 D11. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D11; current owner refinements: [D17](OWNER_DECISIONS_17_36.md#d17), [D36](OWNER_DECISIONS_17_36.md#d36)
- **Required inputs:** P18 trading-day ID, strategy/version, account-specific restrictions, authentic entry history.
- **Authoritative data source:** Existing independent account/ledger boundary plus covered calendar needed; current supervisory synthetic state and caller trade counts are not authenticated account truth.
- **Evaluation timeframe:** Approved exchange day plus each independently defined account/session horizon.
- **Information cutoff:** Complete historical account events available by decision time.
- **Positive evidence:** Owner one-trade-per-approved-day AND independently binding account limits; counting predicate null.
- **Negative evidence:** Strategy day resets override account limit; unknown count treated zero.
- **Contradictory evidence:** Trade vs entry-attempt/fill definitions differ; account and strategy clocks differ.
- **Invalidation behavior:** Any independently binding restriction fails; exact consumption/correction semantics unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Every relevant restriction must be current; original day label immutable.
- **Replay requirements:** exact common replay policy above plus original P19 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** Trade/attempt/fill consumption identity, authenticated current account history, day/version binding and independent account restrictions unresolved.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_DATA_SOURCE. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p20"></a>

## P20 — INDEPENDENT_PROFESSIONAL_RISK_EVIDENCE

- **Predicate identifier:** `IMAF-V02-INDEPENDENT_PROFESSIONAL_RISK_EVIDENCE` (P20)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC7/70; R.boundaries; T validateImafEntry; E HARD_RISK_ARITHMETIC/EXECUTION_ERROR_48H_PAUSE; M2 change control. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D9/D11 and preserved controls; current owner refinements: [D17](OWNER_DECISIONS_17_36.md#d17), [D36](OWNER_DECISIONS_17_36.md#d36)
- **Required inputs:** Existing hard-limit policy, proposal risk geometry, account/exposure history, error log, operator/operational readiness where required.
- **Authoritative data source:** Existing risk-gateway policy/transaction controls; authentic quotes/account/operational and applicable human attestations remain source-specific prerequisites.
- **Evaluation timeframe:** Proposal cutoff, independent account/session/48-hour-error horizons.
- **Information cutoff:** Only actual available account/human/operational evidence; no guessed attestations.
- **Positive evidence:** Every required independent existing control evidenced; completeness predicate null.
- **Negative evidence:** Research geometry equals account authorization; model readiness attestation invented.
- **Contradictory evidence:** Stale/missing state, risk or operational failures, conflicting restrictions.
- **Invalidation behavior:** Existing independent denials remain binding; no new invalidation thresholds.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Policy/state validity and existing pause retained; unknown is not satisfied.
- **Replay requirements:** exact common replay policy above plus original P20 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** Pure risk/ledger controls exist but genuine source/account/operator truth not established; backup/recovery and live authority not implied by arithmetic.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_DATA_SOURCE. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p21"></a>

## P21 — PROFESSIONAL_REVIEW_COMPLETENESS

- **Predicate identifier:** `IMAF-V02-PROFESSIONAL_REVIEW_COMPLETENESS` (P21)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC8/71; T buildImafReview; G.READINESS; M2 Professional Review. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** All decisions, review checkpoint; current owner refinements: [D36](OWNER_DECISIONS_17_36.md#d36)
- **Required inputs:** Original decision/evidence/cutoff, subsequent outcomes, factual attribution, interpretive process review.
- **Authoritative data source:** Original assessment, factual platform lifecycle records and separately reviewed process evidence; no synthetic outcome is genuine forward evidence.
- **Evaluation timeframe:** Original evaluation and later review horizons, kept separate.
- **Information cutoff:** Outcome used only after its availability; never modifies earlier rationale.
- **Positive evidence:** Honest process review independent of profit/loss; full interpretive predicate null.
- **Negative evidence:** Pretrade outcome fabricated, win proves coherence, loss disproves all observations.
- **Contradictory evidence:** Outcome and process quality disagree; attribution remains uncertain.
- **Invalidation behavior:** Corrections append separately; original assessment not erased.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Review pending if evidence absent; deadline/completeness policy unresolved.
- **Replay requirements:** exact common replay policy above plus original P21 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** Factual outcome receipt exists in Trading; independent interpretive process-completeness/attribution and genuine reviewed outcomes not established.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** NOT_READY. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="p22"></a>

## P22 — CONTEXTUAL_TARGET_RANKING

- **Predicate identifier:** `IMAF-V02-CONTEXTUAL_TARGET_RANKING` (P22)
- **Current version:** `0.2.0-draft`.
- **Canonical source:** C CC5/68; P /definitions/2/proposal/requiredRelations/0; E KNOWN_OPPOSING_SESSION_TARGET; M2 D10. See source catalog for exact manuscript sections; reviewed semantics supplemented by M4 decisions.
- **Owner decision dependencies:** D10; current owner refinements: [D19](OWNER_DECISIONS_17_36.md#d19), [D22](OWNER_DECISIONS_17_36.md#d22), [D35](OWNER_DECISIONS_17_36.md#d35)
- **Required inputs:** P01 original objective, current auction context, session, acquired liquidity, delivery path, candidate proximity/timeframe.
- **Authoritative data source:** No authoritative production source established; exact source bars/instrument metadata and provenance required; current tested inputs synthetic.
- **Evaluation timeframe:** Analysis context and execution target horizon.
- **Information cutoff:** Original bias/objective frozen before later ranking update; new information new assessment.
- **Positive evidence:** Owner contextual multi-factor ranking; weights/ties/priority rules null.
- **Negative evidence:** Nearest/highest timeframe automatic priority; winning target retrofits bias.
- **Contradictory evidence:** Two candidates remain plausible; target path conflicts with larger objective.
- **Invalidation behavior:** Target acquired/expired or context invalidated under approved rule.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Candidate and narrative expiry explicit; no indefinite target validity.
- **Replay requirements:** exact common replay policy above plus original P22 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Remaining ambiguities:** Contextual candidate ranking rather than nearest target; preserve original objective/bias and earlier evidence; tie/conflict treatment unspecified.
- **Approval status:** Concepts selected where stated; no executable sufficiency approved. Executable definition: `null`.
- **Implementation readiness:** REQUIRES_MEASURABLE_DEFINITION. Existing research observations can be tested in their own versions; canonical predicate cannot execute.

<a id="s-disc"></a>

## S-DISC — model_discovery_predicate

- **Predicate identifier:** IMAF-SESSION-GOVERNANCE-v0.2::model_discovery_predicate
- **Current version:** 0.2.0-session-draft.1
- **Canonical source:** C-TIME and C-WORK; M3 discovery/expiry selection, M4 [D17](OWNER_DECISIONS_17_36.md#d17)/[D36](OWNER_DECISIONS_17_36.md#d36); parent P16.
- **Owner decision dependencies:** [D17](OWNER_DECISIONS_17_36.md#d17)/[D18](OWNER_DECISIONS_17_36.md#d18)/[D20](OWNER_DECISIONS_17_36.md#d20)–[D24](OWNER_DECISIONS_17_36.md#d24)/[D36](OWNER_DECISIONS_17_36.md#d36)
- **Required inputs:** Original qualifying event/boundary, actual availability, setup/model/version, exact CT windows
- **Authoritative data source:** Not established; source SYNTHETIC_FIXTURE and evidence refs are test assertions only.
- **Evaluation timeframe:** Approved four model pairs; policy America/Chicago; UTC evidence instants.
- **Information cutoff:** No discovery before qualifying evidence available; window membership at selected discovery event time.
- **Positive evidence:** Qualifying liquidity sweep with timestamped boundary and tick-valid penetration; contextual confirmation separate.
- **Negative evidence:** A supplied string ref or CONFIRMED state substituted for actual qualification.
- **Contradictory evidence:** Morning event reclassified afternoon; discovery in a closed window.
- **Invalidation behavior:** Approved contextual contradictory evidence terminates original setup; predicate unresolved.
- **Missing-data behavior:** Insufficient evidence; no executable eligibility or guessed model predicate.
- **Expiry behavior:** Must also satisfy original finite bound; actual deadline policy unresolved.
- **Replay requirements:** Retain exact original policy/calendar/runtime hashes, event availability, identity, cutoff, result; dependency mismatch unavailable.
- **Remaining ambiguities:** [D17](OWNER_DECISIONS_17_36.md#d17) supplies four exact CT windows; existing helper only outer opening/cutoff. Model-specific qualifying event availability remains undefined; probe discrepancies documented. Scoped helper enforces selected outer constraints, not an independent canonical model.
- **Approval status:** Executable definition: `null`; conceptual type selected, no executable algorithm approved.
- **Implementation readiness:** BLOCKED_BY_DEPENDENCY. Requires parent P16 operational selection and authentic source integration for authoritative claims.

<a id="s-exp"></a>

## S-EXP — model_expiry_predicate

- **Predicate identifier:** IMAF-SESSION-GOVERNANCE-v0.2::model_expiry_predicate
- **Current version:** 0.2.0-session-draft.1
- **Canonical source:** C-TIME and C-WORK; M3 discovery/expiry selection, M4 [D17](OWNER_DECISIONS_17_36.md#d17)/[D36](OWNER_DECISIONS_17_36.md#d36); parent P17.
- **Owner decision dependencies:** [D17](OWNER_DECISIONS_17_36.md#d17)/[D18](OWNER_DECISIONS_17_36.md#d18)/[D36](OWNER_DECISIONS_17_36.md#d36)
- **Required inputs:** Original discovery identity, finite absolute bound, rule/authority/version, original cutoff and updates
- **Authoritative data source:** Not established; source SYNTHETIC_FIXTURE and evidence refs are test assertions only.
- **Evaluation timeframe:** Approved four model pairs; policy America/Chicago; UTC evidence instants.
- **Information cutoff:** Original finite bound fixed by selected model rule/source at original setup; never refreshed by later candles.
- **Positive evidence:** Finite model-bound deadline with evidence; no extension or terminal resurrection.
- **Negative evidence:** Missing/nonfinite bound, invented universal duration, renamed identity extends time.
- **Contradictory evidence:** Later source/new identity alters the old bound; expiry preceded discovery.
- **Invalidation behavior:** At original expiry, no new-entry eligibility; exact model invalidation independent.
- **Missing-data behavior:** Insufficient evidence; no executable eligibility or guessed model predicate.
- **Expiry behavior:** Must also satisfy original finite bound; actual deadline policy unresolved.
- **Replay requirements:** Retain exact original policy/calendar/runtime hashes, event availability, identity, cutoff, result; dependency mismatch unavailable.
- **Remaining ambiguities:** [D17](OWNER_DECISIONS_17_36.md#d17) finite expiry deadline source/maximum lifetime remains explicitly unresolved. Fresh recovery event cannot extend/relabel old identity; historical replay is not a new opportunity. Scoped helper enforces selected outer constraints, not an independent canonical model.
- **Approval status:** Executable definition: `null`; conceptual type selected, no executable algorithm approved.
- **Implementation readiness:** BLOCKED_BY_DEPENDENCY. Requires parent P17 operational selection and authentic source integration for authoritative claims.

## Registry crosswalk and unimplemented leaf obligations

R response question→P04/P06/P07/P08; accepted-transition question→P09/P10/P11;
narrative question→P01/P05/P12/P13/P14/P15/P22; discovery/expiry question→P16/P17,
S-DISC/S-EXP and calendar P18. All four approvedDefinition slots stay null.

[D22](OWNER_DECISIONS_17_36.md#d22) boundary-family construction/equal-level geometry, [D23](OWNER_DECISIONS_17_36.md#d23) structurally significant
swing, [D24](OWNER_DECISIONS_17_36.md#d24) controlling-range selection, [D28](OWNER_DECISIONS_17_36.md#d28)/29 break-state classification, [D26](OWNER_DECISIONS_17_36.md#d26) geometric/
relevant/setup-qualified FVG and [D32](OWNER_DECISIONS_17_36.md#d32) evidence-modality sufficiency are incomplete
leaf requirements within existing compound records. No claim of complete atomic
predicate coverage is made. They require finer versioned definitions before code;
adding terminology alone must not inflate the ready/executable count.

Statuses are readiness classifications, not new supervisory outcomes. No null is
filled by an old research close count, numerical threshold, supplied flag or model
confidence. Execution remains DENIED for all records.

Operational/source blockers: [top-five blocker groups and owner queue](IMPLEMENTATION_READINESS_V0.3.md#top-five-blocker-groups). Null definitions do not bypass these requirements.
