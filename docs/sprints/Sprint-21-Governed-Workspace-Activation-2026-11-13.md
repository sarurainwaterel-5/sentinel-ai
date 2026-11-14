# Governed workspace activation — 2026-11-13

Subsequent status: [rollout verification completed](Sprint-21-Governed-Workspace-Completed-2026-11-13.md). The activation-time account below is historical.

The local source-inspection workspace is activated through the standard local
startup script. Rain retains nine exact authorized scopes. The existing Caddy
administrator login and the governed principal require separate credentials.
Production answering remains disabled; ADR-037 remains Proposed.

All **74 eligible documents and 46,299 chunks** have been copied into the new
private original/chunk stores and transactional catalog. Five archived intents
were preserved atomically. Two unresolved sources remain quarantined. Originals
and the legacy collection were preserved. A fresh full backup includes PostgreSQL,
uploads, cognitive storage and quiesced Qdrant storage; the PostgreSQL backup was
restored and all 12 application tables matched.

**Bulk index reconciliation is still running on the local CPU.** A source becomes
inspectable only after its own current outbox operation receives complete index
readback and acknowledgment. A completed copy is not a completed index. The
[activation receipt](../governance/governed-workspace.activation-20261113.json)
records this distinction. The background final verifier will check every active
full manifest, deny all five archived sources, verify every retained original and
chunk object, compare legacy table digests, and repeat the synthetic HTTP lifecycle.
It records completion only after those checks pass.

The installed model is the hash-verified local all-MiniLM-L6-v2 artifact set, with
384-dimensional cosine vectors in a separate identity-bound collection. No paid
provider calls are involved. A supervised worker handles one document per run,
with a fresh bounded processing window and live lease renewal. Docker restarts it
between documents. New governed OCR/transcription intake is held for derivative
review while retaining the uploaded original. Legacy image/video support remains
available independently.

Initial live authentication, source inspection and synthetic archive/restore/
tombstone verification passed **42 checks**. Backend regression passed
**2,386 tests**, with eight optional checks skipped (seven require a disposable
Qdrant service; one requires Pillow in the host test environment). The running
container's actual model, collection and synthetic lifecycle were checked live.

## Operation and recovery

Private runtime, credentials, backups and logs are under
`outputs/sprint21-governed-rollout/` outside Git. Start the installed release with
its `release/scripts/start_local.sh`. The previous exact API and frontend images
are retained with a private `rollback/` bundle. Recovery stops only the two new
governed services and starts that rollback bundle through its `scripts/start_local.sh`;
it does not remove any source, database or governed volume. Rollback has not been
executed.

The workspace API is `/api/governance/v2` behind the loopback frontend. It supports
exact-scope listing, selected verified source inspection, intake and lifecycle
operations. It uses the dedicated `X-Sentinel-Governed-Authorization` header in
addition to Caddy's outer `Authorization`; outer credentials never substitute
for the governed principal. The existing frontend remains the legacy interface.
See the [verification procedure](Sprint-21-Governed-Rollout-Verification-2026-11-13.md).

This operational rollout does not certify semantic correctness, complete OCR
transcription, statistical model independence or acceptance of unseen generated
answers. Those limits and the production-answer boundary remain in force.
