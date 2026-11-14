# Governed workspace rollout verification — 2026-11-13

Root executed the verifier against the live installation: **42 checks passed**,
including the isolated synthetic lifecycle. Its six HTTP-mock tests additionally
cover script behavior, including paginated listings and cursor-loop rejection.
The final rerun follows full corpus reconciliation; see the
[activation checkpoint](Sprint-21-Governed-Workspace-Activation-2026-11-13.md).

Run from the repository's `backend` directory with the configured Python:

```bash
python -m scripts.verify_governed_workspace \
  --base-url http://127.0.0.1:8080/api \
  --credentials /absolute/private/verification-credentials.json \
  --output /absolute/private/new-rollout-report.json \
  --execute-synthetic-lifecycle
```

Without the final option it performs only read-only authentication, scope and
answer-gate checks. The credential file must be owned by the executing user,
mode `0600`, and contain exactly `outer`, `governed` and `scopes`. Each credential
record has `username` and `password`; `scopes` is the nine exact reviewed
organization/collection/module/topic dictionaries. Do not put password values
in command-line arguments. The output directory must be owned and mode `0700`;
the report must be a new filename. The script accepts only explicit loopback
URLs, disables environment proxy lookup and does not follow redirects.

## Two independent credential checks

Caddy retains its normal `Authorization` header for the outer local-admin gate.
The configured governed sidecar requires exactly one distinct
`X-Sentinel-Governed-Authorization` header containing governed Basic credentials.
It verifies those credentials and exact scope against the governed catalog.
Missing or duplicate dedicated credentials deny; outer credentials do not serve
as a fallback. No forwarded user/organization header authenticates the actor.
The verifier constructs both secret headers only in memory and records neither
headers nor response bodies. Avoid logging these headers in host/proxy tooling.

Caddy must preserve `/governance/v2` when routing the sidecar: match
`/api/governance/v2/*`, strip only `/api`, then proxy to the reviewed sidecar.
Keep Caddy's outer authentication applied. A `handle_path` that strips the entire
`/api/governance/v2` prefix will not match the sidecar's routes.

## Checks and allowed synthetic writes

The verifier logs in through all nine granted scopes, rejects an ungranted scope,
wrong outer password, wrong governed password, missing dedicated header and
duplicate dedicated header. It verifies the existing answer readiness is disabled
and the answer endpoint still returns `503`; no model call is requested.

With the explicit lifecycle option, it uploads one UUID-marked synthetic TXT
source into the first supplied granted scope, checks the returned original-byte
hash, waits for active acknowledged state, and verifies the exact selected CAS
text through the index-backed inspection endpoint. It tests mismatched-scope
inspection, archives the returned synthetic identity, confirms inspection denies,
restores and re-verifies it, then tombstones that same identity. It does not
modify any migrated/legacy identity or delete any original source bytes.

On a failed check the run stops, preserves a private partial report and does not
silently retry writes. If it has learned a synthetic document ID before failure,
the report sets `synthetic_cleanup_required`; root must inspect and finish cleanup
using that exact identity and its current epochs. A complete successful run
records `completed_tombstoned`.

## Rollout boundaries still requiring independent evidence

Before execution, root verifies backups, exact new schema/collection identities,
model artifact hashes, private storage mounts and the selected migration mapping.
The factory must not adopt a legacy collection or infer grants from scope labels.
The deployed outbox worker must reconcile actual embeddings and full manifest
readback; a live `active` row is not sufficient without the verified inspection.
Synthetic checks complement migration count/hash/reconciliation audits; they do
not establish that every migrated source is semantically correct.

The sidecar workspace is for verified source inspection. Its status and responses
must retain `production_enabled=false`, `release_authorized=false`,
`provider_calls=0` and closed proposition-to-inference. Neither migration nor
this operational verifier completes empirical human acceptance, OCR/source
acceptance or production-answer release authorization.
