# Actual corpus runtime inspection

The installed governed workspace verifies source chunks and lifecycle operations. Its `/governance/v2/inspect` endpoint does not generate answers or call providers. The frozen fixture UI continues to accept only its reviewed offline contract.

`evaluation.governed_answers.corpus_runtime_inspection` supplies a separate, explicit operator-run composition for a bounded actual-corpus review. It requires an issued authentication session bound to the exact catalog writer, the runtime's actual reconciler, one active document, two to sixteen explicitly selected chunks, a question, and explicit relationship hypotheses. Every premise is the complete selected chunk text; the adapter cannot silently replace it with an invented summary. Relationships are hypotheses supplied by the operator, assessed by the model, and displayed as hypotheses in the review.

The coordinator verifies the complete current document manifest and index before selecting chunks, captures the SQL authority/version/gate proof, runs the existing generation, statement, and relevance transport with at most three calls, then commits through `InspectionPublicationBarrier`. It returns a publication identifier and the result of a new authorized publication read. A gate, permission, credential, scope catalog, document version, lifecycle, or index acknowledgement change denies publication. A withheld model result never exposes a partial candidate. The original source CAS was verified during migration; this composition verifies chunk bytes and SQL source references, rather than claiming to reread every original file during every provider call.

This module does not construct provider clients, read API keys, install tables, rotate gates, invoke paid calls on import, add a public answer route, authorize release, or alter ADR-037. The operator explicitly initializes the existing inspection tables and sets an evidence gate before an invocation. Gate rotation records evidence identity; it is not an acceptance decision.

`render_checked_inspection` renders a separately labeled standalone review from the checked publication result. The artifact includes the question, candidate, qualifications, exact chunk citations, relationship hypotheses, model configuration and assessments, and publication proof. All text is escaped. Store the result outside Git in an owned private directory, with file mode 0600. Export is a historical private snapshot: later revocation can prevent another live publication read but cannot erase an already exported local file. Production and release remain false; human acceptance is not inferred.

Verification: `tests/test_corpus_runtime_inspection.py` checks byte and relationship validation, escaping, and refusal of unpublished/released reports. With an explicit disposable PostgreSQL database, the same file additionally exercises the full SQL publication path through real SDK HTTP mocks and revocation after the generation call. These tests establish integration behavior, not empirical semantic accuracy.


## Structural contract correction, November 14

The actual-corpus run withheld its second case after generation with
`structure_rejected`. The rejected candidate was not retained, so the precise
missing or duplicated reference cannot be reconstructed. Inspection found a
prompt/validator mismatch: generation requested at least two premise references
and only supplied relationships, while structural validation requires all
premises and all relationships exactly once. The generation prompt now states
that exact contract, preserving direction and relationship kind and distinguishing
hypothesis references from assertions of truth. Structural and semantic rejection
checks are unchanged. The focused transport/inspection suite passed 75 tests.

The owner subsequently approved up to three additional calls. The corrected
single-case recheck used three calls and passed structural, statement and relevance
checks, producing a checked inspection-only publication. Seven calls were attempted
across the original and recheck runs. The original failed record remains intact.
Both actual-corpus cases now have private inspection exports pending human review;
this bounded result does not establish general accuracy or production acceptance.
See `sprint21-runtime-recheck.executed-20261114.json`. Production remains disabled.


## Owner output acceptance, November 15

The owner accepted the exact original successful case 1 and corrected case 2
exports. `sprint21-runtime-output.accepted-20261115.json` binds both JSON/HTML pairs,
the execution receipts and combined review page. Earlier pending-review statements
remain historical. Complete OCR disposition is still pending. This bounded output
acceptance does not approve production presentation, ADR-037, broker access or
execution, and does not resolve deployment/source drift.
