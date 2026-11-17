# Conversational memory specification

Conversation context is stored in a separate explicitly created private SQLite file, schema version 1. Existing operational databases are not migrated. Absolute nonsymlink paths, owner-only parent directory and file permissions reuse 22A path validation. One database connection serializes transactions with an RLock. A fresh connection can reopen durable context.

Each record binds tenant, application, issued principal owner and conversation UUID. Message ordering is append-only through expected revision, client turn ID and idempotent replay. Reusing a turn ID with different text fails. Every retrieval and mutation rechecks current authentication and explicit companion policy before and after the transaction. No global supervisor bypass exists.

Defaults: 24-hour fixed retention from creation, 32 conversations per owner/scope and 50 turns per conversation. Configurable ceilings: 30 days, 128 conversations and 100 turns; input 4000 characters. Follow-up context uses the latest six user messages, and only the latest topic is used for short contextual queries. The stored summary describes turn count and a curated topic identifier; it is not operational knowledge.

Deletion removes the record with SQLite secure_delete enabled. Expired records are withheld; list/create purge expired records for the current owner. No background scheduler is added. Offline/backups/filesystem snapshots are outside deletion guarantees. Audit entries preserve opaque scoped IDs and record digests with a hash chain; no conversation text is copied to audit. A privileged filesystem owner can rewrite unanchored hashes or truncate history; this is byte integrity, not protection from administrators.

Conversation statements remain CONTEXT_ONLY. Source-bound records and authorized SRE validation receipts remain distinct from user claims. No persistent personal memory is written, no external conversation imported, and no profiles are read. Common credential-shaped submissions are rejected before persistence; this is a bounded defense, not a guarantee that arbitrary prose contains no personal data. Users should not enter credentials.
