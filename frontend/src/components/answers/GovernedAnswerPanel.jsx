import { useId } from "react";

// Offline fixture inspection only. This component is not a production answer entry point.
const outcomes = new Set(["disabled", "insufficient_evidence", "blocked_provenance", "blocked_relationships", "blocked_validation", "rejected", "provider_failure"]);
const strings = value => Array.isArray(value) && value.every(item => typeof item === "string");

function inspectFixture(report) {
  const result = report?.public_response;
  if (report?.execution_source !== "unit_test" || report.empirical_acceptance !== false ||
      result?.schema_version !== "21.v1" || !outcomes.has(result.outcome) || result.answer_text !== null ||
      !Array.isArray(result.claims) || result.claims.length || result.validation?.release_status !== "disabled" ||
      result.validation.semantic_grounding_verified !== false || !strings(result.validation.rejection_reasons) ||
      typeof result.question !== "string" || typeof result.snapshot_id !== "string" ||
      typeof result.scope?.organization_id !== "string" || !Array.isArray(result.evidence) || result.evidence.length > 25 ||
      !strings(result.conflicts) || !strings(result.uncertainty) ||
      !strings(result.limitations ?? []) || !strings(result.missing_information ?? []) || !strings(result.operational_trace ?? [])) return null;
  const ids = result.evidence.map(source => source.evidence_id);
  if (new Set(ids).size !== ids.length || result.evidence.some(source => typeof source.evidence_id !== "string" ||
      typeof source.text !== "string" || typeof source.document_id !== "string" || typeof source.collection !== "string" ||
      !Number.isInteger(source.chunk_index) || source.chunk_index < 0 || source.status !== "indexed" ||
      source.snapshot_id !== result.snapshot_id || source.organization_id !== result.scope.organization_id ||
      (result.scope.module && source.module !== result.scope.module) || (result.scope.topic && source.topic !== result.scope.topic))) return null;
  const claim = report.fixture_claim;
  if (claim && (result.outcome !== "disabled" || result.validation.coverage_status !== "passed" ||
      result.validation.citation_status !== "passed" || claim.kind !== "attributed_synthesis" ||
      typeof claim.statement !== "string" || !claim.statement.trim() || !strings(claim.premise_ids) || claim.premise_ids.length < 2 ||
      !Array.isArray(result.premises) || new Set(claim.premise_ids).size !== result.premises.length ||
      claim.premise_ids.length !== result.premises.length || claim.premise_ids.some(id => !result.premises.some(p => p.premise_id === id)) ||
      !strings(claim.qualifications) || !strings(claim.evidence_ids) ||
      new Set(claim.evidence_ids).size !== ids.length || claim.evidence_ids.length !== ids.length ||
      claim.evidence_ids.some(id => !ids.includes(id)) || claim.validation?.structural_status !== "passed" ||
      claim.validation.statement_status !== "admissible" || claim.validation.semantic_grounding_verified !== false ||
      claim.validation.statement_result?.admissible !== true ||
      claim.validation.statement_result.validation_scope !== "independent_model_semantic_admissibility" ||
      !strings(claim.validation.statement_result.rejection_reasons) || claim.validation.statement_result.rejection_reasons.length)) return null;
  return { result, claim };
}

export default function GovernedAnswerPanel({ report }) {
  const prefix = useId().replaceAll(":", "");
  const inspected = inspectFixture(report);
  if (!inspected) return <article className="panel" role="alert">Unrecognized fixture or unresolved citation. No answer was accepted.</article>;
  const { result, claim } = inspected;
  return <section className="workspace-page governed-answer-fixture" aria-label="Governed answer fixture inspection">
    <article className="panel">
      <p className="eyebrow">Offline fixture · production disabled</p>
      <h2>{result.question}</h2>
      <p>Scope: {result.scope.module || "All Domains"} · {result.scope.topic || "All topics"}</p>
      <p>Outcome: {result.outcome.replaceAll("_", " ")}. Scripted decisions do not establish semantic accuracy or source truth.</p>
      {claim ? <>
        <h3>Attributed synthesis preview</h3><p>{claim.statement}</p>
        <nav aria-label="Claim citations">{result.evidence.map((source, index) =>
          <a key={source.evidence_id} href={`#${prefix}-fixture-source-${index + 1}`} aria-label={`Inspect source ${index + 1}`}>[{index + 1}] </a>)}</nav>
        {claim.qualifications.length > 0 && <><h3>Recorded qualifications</h3><ul>{claim.qualifications.map((text, index) => <li key={index}>{text}</li>)}</ul></>}
        <details><summary>Inspect claim validation</summary><p>Structural gate: passed. Statement assessment: admissible, independent model semantic admissibility.</p>
          <p>Semantic grounding verified: false. No inference or execution is authorized.</p></details>
      </> : <p>No synthesis preview is available. The entire candidate was withheld.</p>}
      <ul>{result.validation.rejection_reasons.map(reason => <li key={reason}>{reason.replaceAll("_", " ")}</li>)}</ul>
    </article>
    <article className="panel"><h3>Source snapshots</h3>
      {result.evidence.map((source, index) => <section id={`${prefix}-fixture-source-${index + 1}`} tabIndex={-1} key={source.evidence_id}>
        <h4>Source {index + 1}: {source.filename || source.document_id}</h4>
        <details><summary>Inspect source {index + 1} provenance and quote</summary>
          <p>Document: {source.document_id} · Collection: {source.collection} · Chunk: {source.chunk_index}</p>
          <p>File hash: {source.file_hash || "Unreported"}</p>
          <p>Exact snapshot text:</p><blockquote>{source.text}</blockquote>
        </details>
      </section>)}
    </article>
    <article className="panel"><h3>Conflicts and uncertainty</h3>
      {result.conflicts.length ? <ul>{result.conflicts.map((text, index) => <li key={index}>{text}</li>)}</ul> : <p>No assessed conflicts reported. This is not proof of agreement.</p>}
      <ul>{result.uncertainty.map((text, index) => <li key={index}>{text}</li>)}</ul>
      <p>Constitutional evaluation: unassessed. Evidence similarity is not answer confidence.</p>
      {(result.limitations ?? []).length > 0 && <><h3>Limitations</h3><ul>{result.limitations.map((text, index) => <li key={index}>{text}</li>)}</ul></>}
      {(result.missing_information ?? []).length > 0 && <><h3>Missing information</h3><ul>{result.missing_information.map((text, index) => <li key={index}>{text}</li>)}</ul></>}
    </article>
    <article className="panel"><h3>Operational stages</h3><p>Recorded stages are not private chain-of-thought.</p><ol>{(result.operational_trace ?? []).map((text, index) => <li key={index}>{text}</li>)}</ol></article>
  </section>;
}
