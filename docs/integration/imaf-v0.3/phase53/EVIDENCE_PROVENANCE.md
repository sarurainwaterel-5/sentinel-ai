# Decision 53 — evidence provenance and geometry boundary

**DRAFT — NOT APPROVED FOR EXECUTION. Execution authorization: DENIED.**

This additive offline research representation implements observation bookkeeping, not accepted structural transitions, institutional attribution, strategy authorization or a replacement governance registry. Existing source doctrine remains in `docs/architecture/ADR-005-imaf-governance.md` in the Trading repository. Decisions 39–41 and 50–53 support research geometry and causal provenance; exact strict comparisons remain an explicitly selected research profile.

## Closed snapshot contract

`services/structure-research/pivots.mjs` exports `evaluatePivots(input)`, `VERSION` (`imaf.structure.snapshot.v1`) and `SPEC_VERSION` (`imaf.structure.research.v1`). Input fields are exactly `version`, `instrument`, `source`, `timeframe_ms`, `candles`, `as_of`, and `comparison_rule`. An instrument string must use an explicit `symbol:YYYY-MM` research namespace with a valid 01–12 month, for example `MNQ:2026-12`; the helper does not resolve continuous symbols, exchange calendars, tick economics or contract rolls. `source` contains exactly nonempty bounded `id` and `version`; these are caller-declared research provenance, not proof of source authenticity.

Each candle contains `timestamp` (UTC open), `available_at` (actual receipt/availability, never before its close), integer positive `open/high/low/close`, nonnegative integer `volume`, `underlying_event_ids`, `high_event_id` and `low_event_id`. Both extremum IDs must occur in the explicit raw ancestry. Aggregated candles must preserve the true constituent ancestry and actual availability; the component never creates higher-timeframe bars from incomplete lower bars. An explicit source event ID is a declared identity, not independently verified market-data authority.

All timestamps use exact UTC millisecond ISO strings. Known candles must be aligned, unique, ordered and contiguous. Gaps, malformed values, unsupported fields and contradictory source/extremum identity fail closed. An envelope is bounded to 512 candles and 64 ancestry IDs per candle. Future rows' time metadata is inspected only to decide visibility; their OHLC and ancestry cannot affect historical classifications. Visible rows are evaluated in supplied order; the helper does not sort or repair histories. Missing future right support remains a candidate; an observed gap is invalid, never fabricated support.

## Identity and immutable relationships

`evidence.mjs` provides canonical sorted JSON, SHA-256 content identities, recursive immutability and conservative ancestry grouping. Objects use five separate categories:

| Category | Meaning / initial scope |
|---|---|
| `MARKET_EVENT` | A source-scoped raw extremum event underlying one or more observations |
| `OBSERVATION` | Measurable three-/five-candle geometry and its actual supporting candles |
| `INTERPRETATION` | Structural meaning; unresolved in this component |
| `CONFIRMATION` | Approved evidentiary sufficiency; unresolved in this component |
| `AUTHORIZATION` | Permission for downstream action; always DENIED |

A `market_event_id` binds instrument, source identity/version, high/low kind and the explicit underlying extremum event ID. It excludes observation resolution and candle timeframe. Thus the same declared raw extremum represented in several geometries or aggregated views retains the same event ID. High and low claims remain separate kinds; their shared raw ancestry is retained. Changed source versions are separate source scopes and cannot silently rewrite an old event.

A `candidate_id` additionally binds timeframe, center candle, pattern resolution, kind and research comparison profile. It tracks a candidate across replay cutoffs. An `observation_id` content-hashes the candidate's visible supporting evidence and resulting geometry state. It excludes the arbitrary evaluation cutoff, but includes evidence-state changes; historical candidate and completed-observation records are therefore not overwritten or falsely treated as identical records. Re-evaluation at a later cutoff records a new `classification_at` even when its underlying observation ID is unchanged.

The raw event record deliberately retains `event_timestamp: null`, `available_at: null` and `raw_event_time: UNRESOLVED`: OHLC does not reveal the actual intrabar extremum time or raw-event receipt. Its immutable payload is identical across timeframe representations. Source candle open (`pivot_timestamp`) and receipt (`source_bar_available_at`) belong to each observation rather than being falsely assigned to the shared raw event. Each observation also retains resolution, candle IDs, evidence dependencies, underlying raw ancestry, source/version, model/spec version and runtime Node/ICU/tz versions. `geometric_recognition_at` is null before complete support; on completion it equals the maximum actual availability across the full supporting window. A delayed left bar also delays recognition. No price inside an unfinished or unavailable bar can establish a pivot. No intrabar high/low ordering is inferred from OHLC.

## Duplicate observations and evidentiary independence

Exact duplicate candles are invalid, rather than counted twice. Shared `market_event_id` identifies the same underlying pivot across three/five geometries; all supporting ancestry remains available for dependency review. `analyzeIndependence` forms conservative connected components when observations share raw source ancestry. Output `market_event_count` and `evidence_disjoint_group_count` are bookkeeping counts only. `independent_confirmation_count` is null and `independence_sufficiency` is `UNRESOLVED`. Disjoint declared ancestry does not prove statistical, informational or canonical independence. Overlapping windows may conservatively group distinct market events; the count never authorizes a conclusion.

## Geometry and promotion boundary

The comparison-rule field is mandatory; omitted/unsupported values are INVALID, and there is no hidden strict-comparison default. With `comparison_rule: UNRESOLVED`, all geometrically complete cases remain unresolved. `STRICT_RESEARCH_V1` is an explicit research-only comparison: center high strictly exceeds all peer highs, or center low strictly undercuts all peer lows. Center equality against any relevant peer yields unresolved, not an invented tie-breaker. Three candles require one closed known candle on each side; five require two. Geometric completion is distinct from structural confirmation, significance and MSS reference selection: all latter fields remain `UNRESOLVED`, even after favorable subsequent price action. Event categorization does not establish actual institutional order attribution.

Output is recursively frozen; no result grants an executable approval. Replay must retain exact input, evaluation cutoff, spec and implementation source hashes, and runtime provenance. Hashes identify supplied content; they do not authenticate the feed. Later source revisions require a new source version and a new archive rather than altering historical evidence.
