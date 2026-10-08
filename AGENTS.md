# Sentinel development workflow

Use this existing local checkout as the working repository. Perform implementation, review, and validation on the user's computer. Commit completed changes and push the working branch to the configured GitHub origin when authorized by the task.

Preserve local environment files, credentials, uploads, and database state. Never commit secrets or runtime data. Do not reset or overwrite unrelated user changes.

Keep ADR-037 Proposed and the proposition-to-inference boundary closed until the documented independent semantic evaluation and acceptance review pass. Synthetic tests do not establish empirical semantic accuracy.

For the persistent single-admin local installation, run `./scripts/start_local.sh`; stop it with `./scripts/stop_local.sh`. The administrator login is stored privately in `.local/login.txt`.
