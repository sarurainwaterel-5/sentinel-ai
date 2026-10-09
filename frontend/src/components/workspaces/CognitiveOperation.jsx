import { useState } from "react";
import { useDomain } from "../../context/useDomain";
import { workspaceRequest } from "../../services/workspaceApi";
import { Judgment, TextList } from "./WorkspaceParts";

function PlanResult({ result }) {
  const plan = result.planning;
  return (
    <article className="workspace-result" aria-label="Planning result">
      <h3>{plan.status.replaceAll("_", " ")}</h3>
      <p>{plan.strategy ?? "No strategy established."}</p>
      <p className="muted">{plan.strategy_rationale}</p>
      <Judgment
        confidence={plan.confidence}
        coherence={result.coherence}
        faculty="Planning"
      />
      <h3>Evidence basis</h3>
      <p>{plan.reasoning_basis.conclusion ?? "No conclusion established."}</p>
      <p className="muted">
        {plan.reasoning_basis.evidence_source_count} evidence sources ·{" "}
        {plan.reasoning_basis.document_count} documents
      </p>
      <TextList items={plan.reasoning_basis.limitations} />
      <h3>Proposed steps</h3>
      <ol className="workspace-list">
        {plan.steps.map((step) => (
          <li key={step.step_id}>
            <strong>{step.title}</strong>
            <p>{step.description}</p>
            <p className="muted">{step.rationale}</p>
            <TextList items={step.completion_criteria} />
            <small>
              Human approval required:{" "}
              {step.requires_human_approval ? "Yes" : "No"}
            </small>
          </li>
        ))}
      </ol>
      {!plan.steps.length && (
        <p className="muted">
          No executable course of action has been established.
        </p>
      )}
      <h3>Risks</h3>
      {plan.risks.map((risk) => (
        <div key={risk.risk_id}>
          <strong>
            Likelihood: {risk.likelihood} · Impact: {risk.impact}
          </strong>
          <p>{risk.description}</p>
          <p className="muted">
            Mitigation: {risk.mitigation ?? "Unspecified"}
          </p>
        </div>
      ))}
      <div className="workspace-grid">
        <section>
          <h3>Constraints</h3>
          <TextList items={plan.constraints} />
        </section>
        <section>
          <h3>Assumptions</h3>
          <TextList items={plan.assumptions} />
        </section>
      </div>
      <h3>Dependencies</h3>
      {plan.dependencies.map((dependency) => (
        <p key={dependency.dependency_id}>{dependency.description}</p>
      ))}
      <h3>Success criteria</h3>
      <TextList items={plan.success_criteria} />
      <details>
        <summary>Inspect provenance and workflow</summary>
        <TextList items={result.knowledge_sources} />
        <TextList items={result.constitutional_sources} />
        <TextList items={plan.planning_trace} />
      </details>
      <p className="workspace-notice">
        This is a proposed plan. No action has been executed.
      </p>
    </article>
  );
}

function VerificationResult({ result }) {
  const verification = result.verification;
  return (
    <article className="workspace-result" aria-label="Verification result">
      <h3>{verification.status.replaceAll("_", " ")}</h3>
      <p>{verification.subject.objective}</p>
      <Judgment
        faculty="Verification"
        confidence={verification.confidence}
        coherence={result.coherence}
      />
      <p>
        {verification.coverage.passed_count} passed ·{" "}
        {verification.coverage.failed_count} failed ·{" "}
        {verification.coverage.unverifiable_count} unverifiable
      </p>
      <details>
        <summary>Inspect verification standards</summary>
        {verification.standards.map((standard) => (
          <section key={standard.standard_id}>
            <strong>{standard.title}</strong>
            <p>{standard.description}</p>
            <p className="muted">
              {standard.standard_id} · {standard.category} ·{" "}
              {standard.required ? "Required" : "Optional"}
            </p>
          </section>
        ))}
      </details>
      <h3>Checks</h3>
      {verification.checks.map((check) => (
        <details key={check.check_id}>
          <summary>
            {check.category.replaceAll("_", " ")} · {check.outcome}
          </summary>
          <p>{check.observation}</p>
          <p className="muted">
            Standard: {check.standard_id} · Severity: {check.severity}
          </p>
          <TextList items={check.evidence_references} />
          <TextList
            items={check.uncertainty}
            empty="No additional uncertainty recorded."
          />
          <p>{check.recommendation}</p>
        </details>
      ))}
      <h3>Findings</h3>
      {verification.findings.map((finding) => (
        <div key={finding.finding_id}>
          <strong>
            {finding.title} · {finding.severity}
          </strong>
          <p>{finding.description}</p>
          <p>{finding.required_resolution}</p>
        </div>
      ))}
      <h3>Required conditions</h3>
      <TextList items={verification.conditions} />
      <details>
        <summary>Inspect coverage and provenance</summary>
        <TextList items={verification.coverage.completed_categories} />
        <TextList
          items={verification.coverage.skipped_categories}
          empty="No categories skipped."
        />
        <TextList items={result.knowledge_sources} />
        <TextList items={result.constitutional_sources} />
        <TextList items={verification.verification_trace} />
      </details>
      <p className="workspace-notice">
        Verification inspects a newly generated planning result. It does not
        certify a previous plan, approve an action, or execute it.
      </p>
    </article>
  );
}

export default function CognitiveOperation({ kind }) {
  const { activeDomain } = useDomain();
  const [objective, setObjective] = useState("");
  const [constraints, setConstraints] = useState("");
  const [state, setState] = useState({
    pending: false,
    error: null,
    result: null,
  });
  const isPlan = kind === "plan";
  async function submit(event) {
    event.preventDefault();
    if (!objective.trim() || state.pending) return;
    setState({ pending: true, error: null, result: null });
    try {
      const result = await workspaceRequest(
        isPlan ? "/cognition/plan" : "/verification",
        {
          method: "POST",
          body: {
            objective: objective.trim(),
            constraints: constraints
              .split("\n")
              .map((line) => line.trim())
              .filter(Boolean),
            workspace: isPlan ? "intelligence" : "governance",
            module:
              activeDomain?.id && activeDomain.id !== "all"
                ? activeDomain.id
                : null,
          },
        },
      );
      setState({ pending: false, error: null, result });
    } catch (error) {
      setState({ pending: false, error: error.message, result: null });
    }
  }
  return (
    <section className="panel">
      <p className="eyebrow">{isPlan ? "Plan" : "Verify"}</p>
      <h2>
        {isPlan
          ? "Build an evidence-aware plan"
          : "Inspect a proposed course of action"}
      </h2>
      <p className="muted">
        {isPlan
          ? "Turn an objective into a bounded recommendation using the current domain's evidence."
          : "Generate and inspect a plan for structural integrity, traceability, completeness, and constraint compliance."}
      </p>
      <form className="workspace-form" onSubmit={submit}>
        <label>
          Objective
          <textarea
            required
            maxLength={10000}
            value={objective}
            onChange={(event) => setObjective(event.target.value)}
            disabled={state.pending}
          />
        </label>
        <label>
          Constraints, one per line
          <textarea
            maxLength={10000}
            value={constraints}
            onChange={(event) => setConstraints(event.target.value)}
            disabled={state.pending}
          />
        </label>
        <p className="muted">
          Evidence scope: {activeDomain?.name ?? "All Domains"}
        </p>
        <button
          className="primary-action"
          disabled={state.pending || !objective.trim()}
        >
          {state.pending
            ? "Examining evidence…"
            : isPlan
              ? "Propose plan"
              : "Verify proposed plan"}
        </button>
      </form>
      {state.pending && (
        <p role="status">
          Sentinel is coordinating its cognitive faculties. No actions are being
          executed.
        </p>
      )}
      {state.error && (
        <p role="alert" className="workspace-error">
          {state.error}
        </p>
      )}
      {state.result &&
        (isPlan ? (
          <PlanResult result={state.result} />
        ) : (
          <VerificationResult result={state.result} />
        ))}
    </section>
  );
}
