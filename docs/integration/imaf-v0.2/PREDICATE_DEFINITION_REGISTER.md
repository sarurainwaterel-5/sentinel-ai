# Predicate definition register — v0.2

**DRAFT — NOT APPROVED FOR EXECUTION.**

> Session-policy amendment: [SESSION_GOVERNANCE_V0.2.md](SESSION_GOVERNANCE_V0.2.md)
> records the later owner-selected CT cutoffs and model-specific discovery/expiry
> choices. Read [OWNER_DECISION_REGISTER_UPDATED.md](OWNER_DECISION_REGISTER_UPDATED.md)
> for D13–D16 and current remaining questions. Earlier NY-window/D12 questions below
> describe the pre-amendment review; they do not override the later selected policy.
> Null model/canonical predicates remain null and existing runtime behavior unchanged.


Version: 0.2.0-draft. All records are **specification proposals**, not a new
runtime registry. The four existing R approvedDefinition values remain null.
Each record includes the fifteen requested fields plus a literal executable predicate.

Necessary positive/negative conditions below express owner constraints and proposed
engineering obligations; they are not sufficient passing algorithms. Existing P/S
numbers are not adopted. Multi-clause records such as array geometry/context or
narrative category/coherence keep every missing subpredicate null as well; a broad
record does not silently fill an individual missing detector.

Common proposed evidence policy: canonical UTC instants, source/instrument/version,
closed-bar availability, explicit information cutoff and immutable content references.
Unknown, missing, malformed, conflicting or expired inputs cannot establish a pass.
Evidence hashes are consistency checks, not source authentication. Replay preserves
the exact historical input, rule/version/hash, runtime/calendar dependency versions,
cutoff, evaluation time, reason and result; changed dependencies return unavailable,
not a permissive reinterpretation. These documentation obligations do not change
existing runtime formats or import this register into either service.

## P01 — LIQUIDITY_OBJECTIVE_SELECTION

- **Unique identifier:** `IMAF-V02-LIQUIDITY_OBJECTIVE_SELECTION` (P01); owner decision(s): D7/D10.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Known objective candidates, larger-context evidence, session context, already-acquired flags and candidate source times.
- **Observation timeframe:** Approved analysis timeframe and larger objective context; no fallback vote.
- **Information cutoff:** Objective selected before acquisition interpretation; retain original selection time.
- **Evidence requirements:** Candidate levels/context lineage and reasons alternatives remain plausible.
- **Positive conditions:** A preexisting objective supported by larger auction evidence; selection predicate null.
- **Negative conditions:** Objective invented after the move; automatic nearest/highest-timeframe winner.
- **Contradiction conditions:** Competing objectives with unresolved contextual priority.
- **Invalidation conditions:** Selected objective demonstrably acquired/invalidated under an approved rule, still null.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Objective/context expiry requires owner-defined bounds; no indefinite relevance.
- **Replay requirements:** exact common replay policy above plus original P01 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC5/68; P /definitions/2/proposal/requiredRelations/0; S.additional_unresolved; M2 D7/D10.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P02 — LIQUIDITY_ACQUISITION

- **Unique identifier:** `IMAF-V02-LIQUIDITY_ACQUISITION` (P02); owner decision(s): D1/D10.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Pinned objective/boundary, instrument, closed OHLCV, event/availability times.
- **Observation timeframe:** Execution member of approved pair with source objective timeframe retained.
- **Information cutoff:** Boundary known before acquisition; exact onset-vs-close availability rule unresolved.
- **Evidence requirements:** Boundary provenance, excursion/return bars, acquisition identity.
- **Positive conditions:** Observable acquisition of selected liquidity; incidental touch distinction null.
- **Negative conditions:** Using a later-selected level or a missing acquisition as if observed.
- **Contradiction conditions:** Equal/touched boundary vs genuine acquisition; noisy excursion without significance.
- **Invalidation conditions:** Later data correction recorded separately; no original-event rewrite.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Subject to original setup/context expiry once approved.
- **Replay requirements:** exact common replay policy above plus original P02 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC2/2, CC9/72; P /definitions/0/proposal/reference; E STRICT_SWEEP; M2 D1.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P03 — QUALIFYING_DISPLACEMENT

- **Unique identifier:** `IMAF-V02-QUALIFYING_DISPLACEMENT` (P03); owner decision(s): D1/D4.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Closed directional OHLCV, prior-only comparison history, instrument tick metadata.
- **Observation timeframe:** Execution timeframe plus contextual analysis refs.
- **Information cutoff:** Comparison inputs and displacement available by cutoff, no later baseline.
- **Evidence requirements:** Body/range/history records distinct from participation inference.
- **Positive conditions:** Qualifying directional displacement under selected rule; numerical predicate null.
- **Negative conditions:** One large candle treated as institutional identification.
- **Contradiction conditions:** Opposing delivery, range expansion without coherent commitment.
- **Invalidation conditions:** Later evidence can weaken interpretation without erasing original candle fact.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Relevance horizon/context validity unresolved.
- **Replay requirements:** exact common replay policy above plus original P03 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C physical60–62; P /definitions/1/proposal/sequence; S.rules; E RESEARCH_DISPLACEMENT; M2 D1/D4.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P04 — PROVISIONAL_REJECTION

- **Unique identifier:** `IMAF-V02-PROVISIONAL_REJECTION` (P04); owner decision(s): D1.
- **Version:** `0.2.0-draft`.
- **Required inputs:** P02 acquisition, known boundary, qualifying inside return, P03 displacement, timestamps.
- **Observation timeframe:** Execution timeframe and paired larger-context references.
- **Information cutoff:** Each component observable by provisional classification time; same-bar vs later-bar rule unresolved.
- **Evidence requirements:** Separate acquisition, return and displacement lineage; no participant identity claim.
- **Positive conditions:** Owner requires sweep then qualifying inside return with displacement, provisional only.
- **Negative conditions:** Sweep alone, return without qualified displacement, label of confirmed rejection.
- **Contradiction conditions:** Return that immediately reclaims boundary; competing continuation interpretation.
- **Invalidation conditions:** P08 qualifying reclaim plus opposite acceptance; pending exact semantics.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Original finite setup expiry required for any lifecycle use; no invented duration.
- **Replay requirements:** exact common replay policy above plus original P04 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C physical25, CC9/72; P /definitions/0/proposal/rejection; E STRICT_SWEEP; M2 D1.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P05 — CONTEXTUAL_PARTICIPATION

- **Unique identifier:** `IMAF-V02-CONTEXTUAL_PARTICIPATION` (P05); owner decision(s): D4.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Larger objective, liquidity behavior, displacement, subsequent delivery and alternative explanations.
- **Observation timeframe:** Relevant analysis/execution contexts, source interval retained.
- **Information cutoff:** Only observations already available; subsequent evidence changes a later record.
- **Evidence requirements:** Multiple independent informational observations; dependencies/bar overlap disclosed.
- **Positive conditions:** Converging contextual evidence of meaningful participation, never institutional identity.
- **Negative conditions:** Displacement alone, assumed narrative or renamed same-bar FVG counted as proof.
- **Contradiction conditions:** Contradictory follow-through, objective conflict, dependence disguised as convergence.
- **Invalidation conditions:** Approved contradiction rule may withdraw inference in a later assessment; null.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Validity horizon and context-change rule unresolved.
- **Replay requirements:** exact common replay policy above plus original P05 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C physical59–62; P /definitions/2/proposal/participationProposal; S.additional_unresolved; M2 D4.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P06 — LIQUIDITY_ACCEPTANCE

- **Unique identifier:** `IMAF-V02-LIQUIDITY_ACCEPTANCE` (P06); owner decision(s): D2/D3.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Known boundary, acquisition side, directional response, persistence/delivery context.
- **Observation timeframe:** Execution timeframe with paired context.
- **Information cutoff:** Acceptance evidence must precede its use in invalidation or confirmation.
- **Evidence requirements:** Actual beyond-boundary behavior, availability and opposite interpretations.
- **Positive conditions:** Qualifying acceptance through liquidity under selected rule, currently null.
- **Negative conditions:** Temporary crossing or single draft close automatically called acceptance.
- **Contradiction conditions:** Concurrent apparent acceptance/rejection, neutral/equal boundary behavior.
- **Invalidation conditions:** Opposing qualified response; exact reversal/neutral handling unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Finite response/context validity to be selected.
- **Replay requirements:** exact common replay policy above plus original P06 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC5/68, CC9/72; P /definitions/0/proposal/acceptance; R response question; M2 D3.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P07 — REJECTION_CONFIRMATION_ROUTE

- **Unique identifier:** `IMAF-V02-REJECTION_CONFIRMATION_ROUTE` (P07); owner decision(s): D2.
- **Version:** `0.2.0-draft`.
- **Required inputs:** P04 provisional rejection, P05 participation, pre-event larger-context interpretation, structural or persistence evidence.
- **Observation timeframe:** Approved pair with context-specific route eligibility.
- **Information cutoff:** No final narrative/accepted transition from same assessment used as its prerequisite.
- **Evidence requirements:** Route selection rationale and independently observed support/contradictions.
- **Positive conditions:** Eligible structural OR persistence route may suffice; eligibility/sufficiency null.
- **Negative conditions:** Always require both, unconditional OR, or structural line break alone.
- **Contradiction conditions:** Route-eligibility ambiguity; two routes supporting opposite conclusions.
- **Invalidation conditions:** P08 qualified invalidation or contradiction rules once selected.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Cannot confirm at/after original expiry or renew expired context.
- **Replay requirements:** exact common replay policy above plus original P07 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C physical60–62, CC4/67; P /definitions/0–1; R response/transition; M2 D2.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P08 — REJECTION_INVALIDATION

- **Unique identifier:** `IMAF-V02-REJECTION_INVALIDATION` (P08); owner decision(s): D3.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Original rejection identity, qualifying reclaim, P06 opposite acceptance, cutoff.
- **Observation timeframe:** Original execution timeframe with larger-context refs.
- **Information cutoff:** Reclaim and acceptance both available when invalidation is asserted.
- **Evidence requirements:** Distinct boundary crossing and acceptance facts, original record link.
- **Positive conditions:** Owner requires qualifying reclaim accompanied by opposite acceptance.
- **Negative conditions:** Temporary crossing or unqualified single opposite close treated as invalidation.
- **Contradiction conditions:** Reclaim seen but acceptance missing/contradicted; unknown is not confirmation.
- **Invalidation conditions:** This predicate invalidates rejection; revalidation/re-entry semantics remain unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** No resurrection/extension of expired original setup.
- **Replay requirements:** exact common replay policy above plus original P08 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C physical24–26; P /definitions/0/proposal/invalidation; R response; M2 D3.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P09 — STRUCTURAL_PERSISTENCE

- **Unique identifier:** `IMAF-V02-STRUCTURAL_PERSISTENCE` (P09); owner decision(s): D5.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Preknown structure/swing, observed close break, subsequent structural observations.
- **Observation timeframe:** Execution timeframe, preexisting analysis references.
- **Information cutoff:** Pivot selection/confirmation known before event; persistence observable before use.
- **Evidence requirements:** Structural reference, known_at, break and subsequent bar lineage.
- **Positive conditions:** New structural organization persists under rule to be selected.
- **Negative conditions:** MSS or isolated close alone called accepted transition.
- **Contradiction conditions:** Recross/failed follow-through, changed swing chosen to rescue setup.
- **Invalidation conditions:** Qualifying old-structure recovery; exact conditions null.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Finite setup/context horizon applies; number of bars not inferred.
- **Replay requirements:** exact common replay policy above plus original P09 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC4/67; P /definitions/1/proposal; E STRUCTURAL_CLOSE_BREAK; M2 D5.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P10 — PRICE_DELIVERY_CONFIRMATION

- **Unique identifier:** `IMAF-V02-PRICE_DELIVERY_CONFIRMATION` (P10); owner decision(s): D4/D5.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Earlier liquidity event, raw follow-through/delivery observations, alternative paths.
- **Observation timeframe:** Execution timeframe and contextual analysis provenance.
- **Information cutoff:** Delivery observed before transition inference; no completed later narrative prerequisite.
- **Evidence requirements:** Delivery intervals, path and relationship to preceding liquidity/structure.
- **Positive conditions:** Observed delivery consistent with proposed reorganization; sufficiency null.
- **Negative conditions:** FVG presence or chosen trade direction used as sole confirmation.
- **Contradiction conditions:** Opposite delivery/overlap or ambiguous path, without invented numeric cutoffs.
- **Invalidation conditions:** Selected contradictory delivery rule, unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Finite setup/context validity; later bars create later evidence only.
- **Replay requirements:** exact common replay policy above plus original P10 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC5/68, physical60–62; P /definitions/2/proposal/requiredRelations; M2 D4/D5.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P11 — ACCEPTED_STRUCTURAL_TRANSITION

- **Unique identifier:** `IMAF-V02-ACCEPTED_STRUCTURAL_TRANSITION` (P11); owner decision(s): D5.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Preceding liquidity response/participation, P09 persistence AND P10 delivery confirmation.
- **Observation timeframe:** Approved analysis/execution pair.
- **Information cutoff:** All prerequisites available before accepted-transition record.
- **Evidence requirements:** Separate proof lineage for persistence and delivery; no direction-based self-proof.
- **Positive conditions:** Owner conjunction necessary; full sufficient predicate remains null.
- **Negative conditions:** Line break/MSS alone, selected long/short direction, or future delivery.
- **Contradiction conditions:** Persistence supports transition while delivery contradicts it.
- **Invalidation conditions:** Qualified structural/delivery contradiction, exact rule null.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** No confirmation after expired setup/context; expiry rule pending.
- **Replay requirements:** exact common replay policy above plus original P11 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC4/67; P /definitions/1; R transition question; M2 D5.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P12 — HIERARCHICAL_CONTEXT

- **Unique identifier:** `IMAF-V02-HIERARCHICAL_CONTEXT` (P12); owner decision(s): D7.
- **Version:** `0.2.0-draft`.
- **Required inputs:** P01 larger objective, required timeframe contexts, lower movement evidence.
- **Observation timeframe:** Exactly 4H→15M, 1H→5M, 15M→1M or 5M→15S; required larger context set unresolved.
- **Information cutoff:** Larger-context evidence known at its use; freeze interpretation before evaluating lower outcome.
- **Evidence requirements:** Objective-first rationale, timeframe lineage, alternatives and conflicts.
- **Positive conditions:** Lower behavior interpreted within larger objective, no voting; predicate null.
- **Negative conditions:** Majority vote, midpoint substituted for directional bias, omitted contrary context.
- **Contradiction conditions:** Countertrend movement can be retracement/acquisition/reversal/unresolved.
- **Invalidation conditions:** Larger objective/context invalidation in a later record.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Context age/expiry rule unresolved, no assumed continuous validity.
- **Replay requirements:** exact common replay policy above plus original P12 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C physical61, CC5/68; P /definitions/2/proposal/requiredRelations/5 and /definitions/3/proposal/hierarchy; S.hierarchy; M2 D7.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P13 — NARRATIVE_CLASSIFICATION_AND_COHERENCE

- **Unique identifier:** `IMAF-V02-NARRATIVE_CLASSIFICATION_AND_COHERENCE` (P13); owner decision(s): D6.
- **Version:** `0.2.0-draft`.
- **Required inputs:** P01/P05/P06/P07/P11/P12 and delivery evidence, competing explanations, invalidation hypothesis.
- **Observation timeframe:** Approved pair with relevant larger narrative context.
- **Information cutoff:** Synthesis after prerequisite observations; later verification cannot backfill it.
- **Evidence requirements:** Links supporting retracement/acquisition/potential reversal/confirmed transition/unresolved.
- **Positive conditions:** Falsifiable coherent interpretation; category boundaries/sufficiency null.
- **Negative conditions:** FVG alone, countertrend automatically invalid, profitable outcome as proof.
- **Contradiction conditions:** Multiple evidence-consistent categories or contradictory prior stages.
- **Invalidation conditions:** Approved prerequisite invalidation/context loss; preserve earlier assessment.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Narrative validity finite; timing and renewal rule unresolved.
- **Replay requirements:** exact common replay policy above plus original P13 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC5–6/68–69, CC9/72; P /definitions/2; R narrative question; M2 D6.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P14 — PD_ARRAY_GEOMETRY_AND_CONTEXT

- **Unique identifier:** `IMAF-V02-PD_ARRAY_GEOMETRY_AND_CONTEXT` (P14); owner decision(s): D8.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Array type/geometry/version, prior liquidity event, participation, transition, narrative and invalidation.
- **Observation timeframe:** Execution location with registered contextual pair.
- **Information cutoff:** Geometry and context available by use; later retest cannot justify earlier classification.
- **Evidence requirements:** Separate array geometry and contextual-fit evidence; FVG/IFVG/OB/breaker/OTE scopes explicit.
- **Positive conditions:** Array fits preceding auction context; each unapproved geometry/eligibility predicate null.
- **Negative conditions:** Array presence authorizes entry; general IMAF forced through one ICT pattern.
- **Contradiction conditions:** Geometric array exists but contradicts narrative or lacks contextual evidence.
- **Invalidation conditions:** Qualified geometry/context failure; individual rule unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Array relevance cannot outlive original setup/context; exact rule pending.
- **Replay requirements:** exact common replay policy above plus original P14 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC5–6/68–69; P /definitions/2/proposal/requiredRelations/4; E THREE_CLOSED_BAR_FVG/LATER_FVG_OTE_ENTRY; M2 D8.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P15 — OUT_OF_BALANCE_ASSESSMENT

- **Unique identifier:** `IMAF-V02-OUT_OF_BALANCE_ASSESSMENT` (P15); owner decision(s): D9.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Auction evidence, P13 coherence/actionability reasoning, known missing inputs.
- **Observation timeframe:** Relevant paired context, not volatility-only timeframe.
- **Information cutoff:** Classify only from evidence available at cutoff.
- **Evidence requirements:** Reasons coherence absent vs evidence unavailable, alternatives retained.
- **Positive conditions:** Owner coherence-based standaside; measurable classifier null.
- **Negative conditions:** Volatility/range/disagreement alone or supplied false flag establishes balance.
- **Contradiction conditions:** Apparent incoherence explained by coherent retracement or liquidity acquisition.
- **Invalidation conditions:** Recovery requires fresh coherent evidence under approved criteria; unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Stale coherence cannot imply balanced; review horizon null.
- **Replay requirements:** exact common replay policy above plus original P15 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC9/72; P sharedSemantics.missingDataRule; E STAND_ASIDE_OUT_OF_BALANCE; M2 D9.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P16 — WINDOW_AND_DISCOVERY

- **Unique identifier:** `IMAF-V02-WINDOW_AND_DISCOVERY` (P16); owner decision(s): D12.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Versioned explicit NY window/session, acquisition/other selected discovery event and availability.
- **Observation timeframe:** Approved analysis/execution pair and America/New_York wall-clock view.
- **Information cutoff:** Discovery event availability vs event-time selection unresolved; preserve both.
- **Evidence requirements:** Window authority, boundaries, source version, closed/received event.
- **Positive conditions:** Discovery within owner window; exact trigger/endpoints null.
- **Negative conditions:** Confirmation time alone used as discovery, unrestricted post09:30, invented universal cutoff.
- **Contradiction conditions:** Event occurs in window but received later; discovery vs confirmation confused.
- **Invalidation conditions:** False/changed source window; setup consequences require explicit rule.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Window close limits discovery, not automatically setup expiry; P17 must define bound.
- **Replay requirements:** exact common replay policy above plus original P16 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC9/72; P /definitions/3/proposal/discoveryWindow and /discoveryEvent; E EXPLICIT_NY_TRADING_WINDOW; M2 D12.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P17 — SETUP_LIFECYCLE_AND_EXPIRY

- **Unique identifier:** `IMAF-V02-SETUP_LIFECYCLE_AND_EXPIRY` (P17); owner decision(s): D12.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Immutable setup/acquisition IDs, P16 discovery, explicit finite bound, causal update events.
- **Observation timeframe:** Approved pair; absolute UTC expiry retains NY context.
- **Information cutoff:** Expiry committed from approved inputs before continued evaluation; receipt delays cannot extend.
- **Evidence requirements:** Original bound provenance, event lineage, parent/new-acquisition links, state history.
- **Positive conditions:** Owner DISCOVERED→DEVELOPING→CONFIRMED/INVALIDATED/EXPIRED; exact transitions null.
- **Negative conditions:** Nested/relabelled setup/reconnect silently extends life; no finite bound.
- **Contradiction conditions:** Confirmation vs expiry/invalidation same instant; new acquisition overlaps old setup.
- **Invalidation conditions:** Qualifying invalidation or expiry event; terminal precedence/supersession unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Finite nonextending expiry mandatory; duration/formula/source authority null.
- **Replay requirements:** exact common replay policy above plus original P17 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC9/72; P /definitions/3/proposal/expiry and /expiryPropagation; Trading research-expiry.js; M2 D12.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P18 — EXCHANGE_TRADING_DAY_CALENDAR

- **Unique identifier:** `IMAF-V02-EXCHANGE_TRADING_DAY_CALENDAR` (P18); owner decision(s): D11.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Calendar ID/version/source, instrument/product, UTC intervals, exchange day IDs, holiday/exception coverage.
- **Observation timeframe:** Exchange session/trading-day horizon; NY clock is not identity.
- **Information cutoff:** Calendar version/effective coverage known before accounting decision.
- **Evidence requirements:** Reviewed schedule source, rollover/DST/holiday exceptions and pinned revision.
- **Positive conditions:** One unambiguous exchange-aware day assignment; exact calendar policy null.
- **Negative conditions:** Midnight date fallback, adding24h schedules, caller labels certify exchange approval.
- **Contradiction conditions:** Exchange day differs from account day; missing/conflicting exceptions.
- **Invalidation conditions:** Version/effective coverage withdrawn; do not rewrite original accounting record.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Coverage bound explicit; unknown coverage blocks, no invented rollover time.
- **Replay requirements:** exact common replay policy above plus original P18 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC7/70; P /definitions/3/proposal/calendarRule; E ONE_TRADE_PER_NY_DAY; M2 D11.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P19 — TRADING_DAY_AND_ACCOUNT_ALLOWANCE

- **Unique identifier:** `IMAF-V02-TRADING_DAY_AND_ACCOUNT_ALLOWANCE` (P19); owner decision(s): D11.
- **Version:** `0.2.0-draft`.
- **Required inputs:** P18 trading-day ID, strategy/version, account-specific restrictions, authentic entry history.
- **Observation timeframe:** Approved exchange day plus each independently defined account/session horizon.
- **Information cutoff:** Complete historical account events available by decision time.
- **Evidence requirements:** Ledger/account provenance, count-consumption event, partials/retries/revisions.
- **Positive conditions:** Owner one-trade-per-approved-day AND independently binding account limits; counting predicate null.
- **Negative conditions:** Strategy day resets override account limit; unknown count treated zero.
- **Contradiction conditions:** Trade vs entry-attempt/fill definitions differ; account and strategy clocks differ.
- **Invalidation conditions:** Any independently binding restriction fails; exact consumption/correction semantics unresolved.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Every relevant restriction must be current; original day label immutable.
- **Replay requirements:** exact common replay policy above plus original P19 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC7/70; R.boundaries.maxEntriesPerSession; P reviewRequirements; E ONE_TRADE_PER_NY_DAY; M2 D11.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P20 — INDEPENDENT_PROFESSIONAL_RISK_EVIDENCE

- **Unique identifier:** `IMAF-V02-INDEPENDENT_PROFESSIONAL_RISK_EVIDENCE` (P20); owner decision(s): D9/D11 and preserved controls.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Existing hard-limit policy, proposal risk geometry, account/exposure history, error log, operator/operational readiness where required.
- **Observation timeframe:** Proposal cutoff, independent account/session/48-hour-error horizons.
- **Information cutoff:** Only actual available account/human/operational evidence; no guessed attestations.
- **Evidence requirements:** Separate checked arithmetic, account truth, operator unknowns and authoritative policy refs.
- **Positive conditions:** Every required independent existing control evidenced; completeness predicate null.
- **Negative conditions:** Research geometry equals account authorization; model readiness attestation invented.
- **Contradiction conditions:** Stale/missing state, risk or operational failures, conflicting restrictions.
- **Invalidation conditions:** Existing independent denials remain binding; no new invalidation thresholds.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Policy/state validity and existing pause retained; unknown is not satisfied.
- **Replay requirements:** exact common replay policy above plus original P20 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC7/70; R.boundaries; T validateImafEntry; E HARD_RISK_ARITHMETIC/EXECUTION_ERROR_48H_PAUSE; M2 change control.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P21 — PROFESSIONAL_REVIEW_COMPLETENESS

- **Unique identifier:** `IMAF-V02-PROFESSIONAL_REVIEW_COMPLETENESS` (P21); owner decision(s): All decisions, review checkpoint.
- **Version:** `0.2.0-draft`.
- **Required inputs:** Original decision/evidence/cutoff, subsequent outcomes, factual attribution, interpretive process review.
- **Observation timeframe:** Original evaluation and later review horizons, kept separate.
- **Information cutoff:** Outcome used only after its availability; never modifies earlier rationale.
- **Evidence requirements:** Each checkpoint process evidence and explicit unknowns; original planned risk separate from result.
- **Positive conditions:** Honest process review independent of profit/loss; full interpretive predicate null.
- **Negative conditions:** Pretrade outcome fabricated, win proves coherence, loss disproves all observations.
- **Contradiction conditions:** Outcome and process quality disagree; attribution remains uncertain.
- **Invalidation conditions:** Corrections append separately; original assessment not erased.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Review pending if evidence absent; deadline/completeness policy unresolved.
- **Replay requirements:** exact common replay policy above plus original P21 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC8/71; T buildImafReview; G.READINESS; M2 Professional Review.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.

## P22 — CONTEXTUAL_TARGET_RANKING

- **Unique identifier:** `IMAF-V02-CONTEXTUAL_TARGET_RANKING` (P22); owner decision(s): D10.
- **Version:** `0.2.0-draft`.
- **Required inputs:** P01 original objective, current auction context, session, acquired liquidity, delivery path, candidate proximity/timeframe.
- **Observation timeframe:** Analysis context and execution target horizon.
- **Information cutoff:** Original bias/objective frozen before later ranking update; new information new assessment.
- **Evidence requirements:** All candidates and contextual ranking reasons, excluded/acquired flags.
- **Positive conditions:** Owner contextual multi-factor ranking; weights/ties/priority rules null.
- **Negative conditions:** Nearest/highest timeframe automatic priority; winning target retrofits bias.
- **Contradiction conditions:** Two candidates remain plausible; target path conflicts with larger objective.
- **Invalidation conditions:** Target acquired/expired or context invalidated under approved rule.
- **Missing-data behavior:** UNKNOWN/insufficient evidence; STAND_ASIDE for dependent research decisions; never PASS or authority. Preserve distinction between unknown and observed failure.
- **Expiry behavior:** Candidate and narrative expiry explicit; no indefinite target validity.
- **Replay requirements:** exact common replay policy above plus original P22 inputs, dependency IDs/lineage and original expiry; append subsequent evidence, never rewrite history.
- **Source references:** C CC5/68; P /definitions/2/proposal/requiredRelations/0; E KNOWN_OPPOSING_SESSION_TARGET; M2 D10.
- **Owner approval status:** CONCEPT_SELECTED_WHERE_STATED; EXECUTABLE_SEMANTICS_UNAPPROVED.
- **Executable predicate:** `null`.
