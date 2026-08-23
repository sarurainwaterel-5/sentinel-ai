import ReasonConclusion from "./ReasonConclusion";
import ReasonConfidence from "./ReasonConfidence";
import ReasonEvidence from "./ReasonEvidence";
import ReasonGovernance from "./ReasonGovernance";
import ReasonLimitations from "./ReasonLimitations";
import ReasonNextStep from "./ReasonNextStep";
import ReasonTrace from "./ReasonTrace";


export default function ReasonResult({
  result,
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

      <ReasonNextStep
        nextStep={
          reasoning.recommended_next_step
        }
      />

    </section>
  );
}
