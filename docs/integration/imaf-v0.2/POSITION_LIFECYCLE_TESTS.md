# Position lifecycle scenarios A–J — offline results

**DRAFT — NOT APPROVED FOR EXECUTION.**

Source: owner session mission section5. Inputs are explicit synthetic positions,
calendar/count/model assertions, not authentic trades. Prices/liquidity patterns or
broker fills are not independently evaluated by this session interpreter.

| Scenario | Input | Tested result |
|---|---|---|
| A | Position opened10:12, assessed10:15 CT | MAINTAIN_PREDEFINED_PLAN; no cutoff-only close |
| B | Proposed morning entry exactly10:15 | PROHIBITED / MORNING_ENTRY_CLOSED |
| C | Unexpired morning setup at12:05 | PROHIBITED / MORNING_CARRYOVER_PROHIBITED |
| D | New12:05 afternoon event/identity/discovery | CONDITIONAL_RESEARCH_REVIEW only; IMAF/model predicates unverified, authority DENIED |
| E | Morning trade count1, fresh afternoon setup | PROHIBITED / EXCHANGE_DAY_TRADE_ALREADY_USED; noon no reset |
| F | Remaining position exactly15:00 | MANDATORY_FLATTEN_CONDITION; no order sent |
| G | Supplied target event14:45 before deadline | SIMULATED_PLAN_CLOSE / TARGET; no broker fill claim |
| H | Missing authoritative count | INSUFFICIENT_EVIDENCE / AUTHORITATIVE_COUNT_NOT_ESTABLISHED |
| I | Model expiry missing | INSUFFICIENT_EVIDENCE / MODEL_EXPIRY_UNDEFINED; never executable |
| J | Record then separate Node process restart/replay | REPLAY_MATCH under original policy/synthetic calendar/runtime bindings |

Scenario J uses private file IPC in a separate process, not merely two calls in one
process. The original snapshot is archived; changing current input/calendar cannot
change the replay source. Missing/changed historical dependencies return unavailable;
tampered input fails integrity; a rehashed inconsistent result is a replay mismatch.
Duplicates return original archive; same setup/event collisions conflict. No original
record is silently overwritten. This test archive is not a production ledger.

Additional cases: known stop closes before deadline; target unfilled or after15:00
cannot postpone flatten; known earlier target remains a simulated historical close
when reviewed at15:00; unavailable future target evidence cannot establish a close.
A position already present does not require a new entry approval to retain protective
management. Risk controls remain independent, and no quantity/order/action is routed.

## Limits and follow-up

Position state/target/stop are supplied fixture assertions. This increment does not
connect these conditions to actual position reconciliation, protective orders,
working-entry cancellation or mandatory live flatten. Any actual early exchange close
requires verified calendar and operational handling. The isolated offline snapshot
interpreter is not a substitute for those existing platform responsibilities.
No live orders, forced position closes or production risk modifications occurred.
