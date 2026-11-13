# PostgreSQL authority observation — 2026-11-13

The additive `postgres_authority_reader.py` reads exact principal/scope grants
from the existing standalone disposable PostgreSQL 16 schema. It rejects other
database names and schema names outside the rehearsal UUID namespace. It does
not read application credentials or register routes, create grants or authenticate
a principal. A caller must independently authenticate the supplied principal ID.

Each observation uses a read-only repeatable-read transaction with bounded SQL
statement/lock timeouts. It requires an idle caller-owned connection, so it does
not commit or roll back an existing caller transaction. The exact organization,
collection, module and topic join must yield one enabled principal/grant row.
Strict types, positive permission epoch and nonnegative scope revision are checked.
A recheck accepts only the same handle issued by that reader and requires the
same current SQL values. Failed captures/rechecks terminalize the reader.

The actual five-test integration selection passed against a fresh PostgreSQL 16
container with random ephemeral credentials. Tests covered an ungranted principal,
a different exact scope, forged observation, repeated capture, permission-epoch
change, grant removal, disabled principal, scope revision and caller transaction
preservation. The temporary container/schema were removed. No installed database
was read or changed.

This is observation, not a publication barrier. Every grant/disable writer must
advance the permission epoch transactionally; the standalone DDL does not enforce
that protocol. A tested delete/reinsert of the same grant without an epoch bump
between reads is invisible (ABA). Disabling/re-enabling without advancing an epoch
has the same limitation. Serial rechecks cannot replace an atomic application
publication mechanism. `authenticated_application_principal`, production and
release flags remain false.

The current Caddy Basic Auth protects the local application, but its configuration
does not establish an application-verified principal/grant handoff. A future
implementation must either verify credentials in the application or accept an
explicit authenticated proxy assertion over a protected internal channel, strip
client-supplied identity headers, bind credential/permission versions, and deny
direct untrusted backend access. No forwarded username or organization parameter
may create a grant. The exact deployed mapping still requires owner review.
