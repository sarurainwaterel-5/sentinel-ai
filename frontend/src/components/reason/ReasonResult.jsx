import ReasonConclusion from "./ReasonConclusion";
import ReasonConfidence from "./ReasonConfidence";
import ReasonEvidence from "./ReasonEvidence";
import ReasonGovernance from "./ReasonGovernance";
import ReasonLimitations from "./ReasonLimitations";
import ReasonNextStep from "./ReasonNextStep";
import ReasonTrace from "./ReasonTrace";


export default function ReasonResult({
  result,
  onNavigate,
}) {
  const reasoning = result?.reasoning;

  if (!reasoning) {
    return null;
  }

  return (
    <section className="reason-report">

      <div className="reason-judgment-zone">
        <ReasonConclusion
          reasoning={reasoning}
        />
      {!reasoning.conclusion && <article className="panel">
        <h2>More evidence is needed</h2>
        <p>Review the mission scope and evidence gaps. You can inspect taught knowledge in Recall, or add a trusted source in Teach.</p>
        <div className="reason-next-actions"><button className="secondary-action" onClick={() => onNavigate?.("recall")}>Inspect Recall</button><button className="secondary-action" onClick={() => onNavigate?.("teach")}>Add evidence in Teach</button></div>
      </article>}
      </div>

      <div className="reason-instrument-grid">
        <ReasonConfidence
          confidence={reasoning.confidence}
          evidence={reasoning.evidence}
        />

        <ReasonGovernance
          coherence={result?.coherence}
        />
      </div>

      <ReasonEvidence
        evidence={reasoning.evidence}
      />

      <ReasonTrace
        trace={reasoning.reasoning_trace}
      />

      <div className="reason-uncertainty-zone">
        <ReasonLimitations
          limitations={reasoning.limitations}
          alternatives={reasoning.alternatives}
          missingInformation={
            reasoning.missing_information
          }
        />
      </div>

      <article className="panel"><p className="muted">Reported outcome: {reasoning.status.replaceAll("_", " ")}. Source status and text reflect this request’s snapshot; Governance controls current retrieval eligibility.</p>
        <button className="secondary-action" onClick={() => onNavigate?.("governance")}>Inspect Governance</button>
      </article>
      <ReasonNextStep
        nextStep={
          reasoning.recommended_next_step
        }
      />

    </section>
  );
}
