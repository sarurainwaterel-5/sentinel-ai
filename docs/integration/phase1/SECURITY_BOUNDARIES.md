# Phase 1 security-boundary verification

Executed verification, November 15, 2026; this is a synthetic harness boundary,
not a production security accreditation.

| Boundary | Implemented evidence | Executed check |
|---|---|---|
| No broker/order/data client | Canonical `protocol.mjs` imports only node:crypto and its local schema. Trading adapter imports local fs/path/url/crypto and pinned protocol. | `security.test.mjs` asserts canonical import allowlist; adapter source inspection confirms no execution/control imports. |
| No network during synthetic tests | `deny-network.mjs` blocks sockets, HTTP(S), DNS and fetch before imports. | Security and Trading adapter tests actively attempt socket/fetch and require denial; full new suites pass under preloader. |
| Existing Trading regression offline | Existing `tests/run.js` evaluated under same preloader. | 367 pass, zero fail/skip; no external service dependency needed. |
| No authority bypass | Closed input schema allows exact true advisory_only and false execution/live. Output authority freshly constructed; governance always DENIED. | Numeric and true-authority bypass cases reject; every shared case checks false output authority. Unknown order/authorization fields reject. |
| No risk/IMAF mutation | No ledger/risk-gateway/governance/control imports from runtime; synthetic-only environment required. | Existing risk, execution and IMAF tests included in the 367-test run. Existing entry locks not modified. |
| No production change/secrets | Added isolated files/docs only; no env discovery or configuration changes. Synthetic fixtures contain no credentials/account values. | Git diff/status review; closed schema rejects unknown credential fields. No claim that an arbitrary user identifier could never contain a secret. |
| Dependency integrity | Trading `consumer-pin.json` hashes module, schema and shared tests before dynamic import from explicitly supplied root. | Modified module rejected before import; nonexistent dependency returns UNAVAILABLE. |
| Audit consistency | Immutable copies, event fingerprint deduplication, distinct conflict records and hash chain. | Duplicate/replay/withdrawal, conflicting ID, mutation, reorder and tamper cases pass. |

No HTTP server or remote service was created. `serviceAvailable:false` is a
simulated outage, not a measured remote service incident. A missing/pin-invalid
local module is separately exercised through the actual Trading adapter.

The network preloader is a test guard, not a general-purpose OS sandbox; subprocess
or hostile plugin isolation is not claimed. The runtime imports no subprocess or
plugin capability. The local hash pin trusts the reviewed checkout and filesystem;
it does not establish remote identity or eliminate concurrent hostile file races.

No executable approval object, broker connection, real-data permission, automatic
remediation, production configuration or new secret is produced. The old Sentinel
snapshot evaluator and Trading authorization receipts are not modified or aliased.
