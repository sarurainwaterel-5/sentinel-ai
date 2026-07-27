import {
  Brain,
  Search,
  Sparkles,
} from "lucide-react";

export default function RecallQuestion({
  question,
  setQuestion,
  activeDomain,
  isRecalling,
  onSubmit,
  error,
}) {
  return (
    <section className="panel recall-query-panel">
      <div className="recall-query-header">
        <div className="recall-icon">
          <Brain size={24} />
        </div>

        <div>
          <p className="eyebrow">
            Evidence-Based Recall
          </p>

          <h2>
            What do you want Sentinel to remember?
          </h2>

          <p className="muted">
            Sentinel reconstructs answers using evidence
            stored inside the selected workspace.
          </p>
        </div>
      </div>

      <div className="recall-workspace-context">
        <span className="recall-context-label">
          Current Workspace
        </span>

        <strong>
          {activeDomain?.name ?? "All Domains"}
        </strong>
      </div>

      <form
        className="recall-form"
        onSubmit={onSubmit}
      >
        <label htmlFor="recall-question">
          Recall Question
        </label>

        <textarea
          id="recall-question"
          rows={6}
          value={question}
          onChange={(event) =>
            setQuestion(event.target.value)
          }
          placeholder="Ask Sentinel about previously learned knowledge..."
        />

        <div className="recall-form-footer">
          <p className="muted">
            Answers remain grounded in retrieved evidence.
          </p>

          <button
            className="primary-action"
            type="submit"
            disabled={isRecalling}
          >
            {isRecalling ? (
              <Sparkles size={18} />
            ) : (
              <Search size={18} />
            )}

            <span>
              {isRecalling
                ? "Reconstructing Memory..."
                : "Recall Knowledge"}
            </span>
          </button>
        </div>
      </form>

      {error && (
        <div
          className="recall-message recall-message-error"
          role="alert"
        >
          {error}
        </div>
      )}
    </section>
  );
}
