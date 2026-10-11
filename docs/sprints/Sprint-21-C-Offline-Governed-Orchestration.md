# Sprint 21-C — Offline governed orchestration

Implemented after approval on the existing Sprint 21 branch, based on 21-B
`c0f19c4`. Production behavior remains disabled. No endpoint, SDK adapter,
credential, frontend, deployment, benchmark policy or inference implementation
was added or changed.

## Implemented flow

`OfflineAnswerCoordinator.evaluate_fixture` takes synthetic source snapshots,
a caller-supplied catalog, explicit scope and assessed fixture relationships.
It does not retrieve, classify relationships through a provider, or construct
clients. Invalid request scope/question is rejected before injected work.

The coordinator builds the 21-B registry and refuses partial provenance when
any source is rejected. It extracts premises with the existing PremiseExtractor,
requires complete evidence lineage and one unambiguous directional relationship
for every selected premise pair, and blocks independent/unresolved or below-0.75
relationships. The unchanged baseline relationship threshold is enforced;
fixture relationship assessments do not establish source truth. Relationship
input is capped at 300 pairs, consistent with the 25-source request bound. No
truncation, scope widening or dropped conflicting source is permitted.

Generation uses the existing injected SemanticPropositionGenerator contract.
Existing PropositionSynthesizer, PropositionGroundingValidator and
FreeFormStatementAdmissibilityValidator are reused without rule changes. No
structural compatibility or exact-report substitute is accepted. The same-object
and same-client separation checks remain active. Provider/generator/validator
errors become bounded blocked outcomes, not fabricated answers or Recall fallback.

All participating premises must survive the existing statement gate. Assessed
conflicts are retained in the public diagnostic ledger even when a candidate is
rejected. A candidate referring only to a favorable subset cannot become a
partial successful answer. Generated metadata never enters the judge request or
controls provenance, validation or release.

A successful fixture gets an AnswerClaim bound to exact statement/qualifications,
complete evidence IDs and a hash of question, scope, sources, premises and
relationships. The deterministic renderer revalidates the claim and source hashes,
checks the entire input binding and complete citation coverage, and copies assessed
text exactly. It cannot introduce model-generated explanation or post-validation
paraphrase. Essential qualifications remain subject to the existing judge's
standalone-statement rule; displaying qualifications separately never repairs a
failed statement.

## Strict offline/public separation

`OfflineAnswerEvaluation.fixture_claim` and `fixture_text` are development previews,
not released answers. The public GovernedAnswer always retains null answer_text,
empty claims, release_status=disabled and semantic_grounding_verified=false.
The evaluation's execution source is fixed to unit_test and empirical acceptance
is fixed false; callers cannot set these constructor fields to certify acceptance.
Blocked diagnostics retain provenance, conflicts and uncertainty without rendering
unsupported generated prose. No proposal reaches InferenceEngine.

The coordinator has no production factory or route. Dependency injection is for
scripted offline fixtures in this milestone; it is not permission to execute a
live generation or semantic provider. The test adapters implement existing raw
provider contracts and exercise the real strict parser and existing judge gate.
No alternate judge, certifying metadata, repaired output or weaker fallback was
introduced. The concrete production generation SDK adapter and its operational
budgets/configuration remain future separately approved work.

## Remaining release dependencies

Question relevance is not established by an admissibility verdict; the existing
judge does not receive the question. Relationship classification is supplied by
fixtures, not measured. Source authenticity, authorized retrieval/catalog
composition and eligibility races remain storage-integration/release gates.
Actual independently configured judge accuracy remains unmeasured. Offline
previews do not satisfy 20.3-G, accept ADR-037 or open Proposition → Inference.

21-D may add disabled API/readiness and inspectable fixture UI only after approval.
Its release gate must execute before constructing or calling any live dependency.
Production acceptance and deployment are not authorized by completing 21-C.

## Validation

- Complete reasoning regression suite: 288 passed, with one existing Qdrant
  server-version compatibility warning in the offline environment.
- Final 21-B/21-C contract and orchestration suite: 54 passed.
- Protected benchmark, ADR-037 and inference files remain unchanged from the
  supplied Sprint 20.3 checkpoint; git diff --check passes.
- Tests are scripted offline enforcement evidence, not empirical acceptance.
