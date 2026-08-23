import { BrainCircuit } from "lucide-react";


export default function ReasonQuestion({
  question,
  setQuestion,
  isReasoning,
  onSubmit,
  error,
}) {
  return (
    <article className="panel reason-mission-card">
      <div className="reason-section-heading">
        <div className="reason-section-icon">
          <BrainCircuit size={20} />
        </div>

        <div>
          <p className="eyebrow">
            Reasoning Mission
          </p>

          <h2>
            What should Sentinel reason about?
          </h2>
        </div>
      </div>

      <p className="muted">
        Sentinel will examine available evidence,
        construct bounded inferences, assess confidence,
        and evaluate constitutional coherence.
      </p>

      <form
        className="reason-question-form"
        onSubmit={onSubmit}
      >
        <textarea
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          placeholder="Ask Sentinel to analyze an evidence-grounded question..."
          disabled={isReasoning}
          rows={5}
        />

        {error && (
          <p
            className="reason-error"
            role="alert"
          >
            {error}
          </p>
        )}

        <div className="reason-question-actions">
          <button
            type="submit"
            className="primary-action"
            disabled={isReasoning}
          >
            <BrainCircuit size={18} />

            <span>
              {isReasoning
                ? "Analyzing Evidence..."
                : "Analyze Evidence"}
            </span>
          </button>
        </div>
      </form>
    </article>
  );
}
