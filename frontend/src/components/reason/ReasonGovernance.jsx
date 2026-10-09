export default function ReasonGovernance({ coherence }) {
  if (!coherence) {
    return null;
  }

  const notEvaluated = coherence.evaluation_status === "not_evaluated";

  const score = Math.round((coherence.constitutional_score ?? 0) * 100);

  const conflictCount = coherence.conflicts?.length ?? 0;

  const articleCount = coherence.articles_consulted?.length ?? 0;

  return (
    <article className="panel reason-governance">
      <p className="eyebrow">Constitutional Coherence</p>

      <div className="reason-instrument-heading">
        <strong className="reason-instrument-value">
          {notEvaluated ? "Unassessed" : `${score}%`}
        </strong>

        <span className="reason-instrument-state">
          {coherence.coherent ? "Coherent" : "Review Required"}
        </span>
      </div>

      {!notEvaluated && (
        <div
          className="reason-meter"
          role="progressbar"
          aria-label="Constitutional coherence"
          aria-valuemin="0"
          aria-valuemax="100"
          aria-valuenow={score}
        >
          <span
            style={{
              width: `${notEvaluated ? "Unassessed" : `${score}%`}`,
            }}
          />
        </div>
      )}

      <p className="reason-instrument-basis">
        {notEvaluated
          ? "Constitutional admissibility has not been evaluated. Review the result before making a decision."
          : coherence.coherent
            ? "No constitutional conflict blocks this reasoning."
            : "Constitutional review identified conflicts requiring attention."}
      </p>

      <div className="reason-instrument-summary">
        <span>
          {articleCount} {articleCount === 1 ? "article" : "articles"}
        </span>

        <span>
          {conflictCount} {conflictCount === 1 ? "conflict" : "conflicts"}
        </span>
      </div>

      {(articleCount > 0 ||
        conflictCount > 0 ||
        coherence.recommendations?.length > 0) && (
        <details className="reason-instrument-details">
          <summary>Inspect governance basis</summary>

          {articleCount > 0 && (
            <section>
              <p className="eyebrow">Articles Consulted</p>

              <ul>
                {coherence.articles_consulted.map((article, index) => (
                  <li key={index}>{article}</li>
                ))}
              </ul>
            </section>
          )}

          {conflictCount > 0 && (
            <section>
              <p className="eyebrow">Conflicts</p>

              <ul>
                {coherence.conflicts.map((conflict, index) => (
                  <li key={index}>{conflict}</li>
                ))}
              </ul>
            </section>
          )}

          {coherence.recommendations?.length > 0 && (
            <section>
              <p className="eyebrow">Governance Recommendations</p>

              <ul>
                {coherence.recommendations.map((recommendation, index) => (
                  <li key={index}>{recommendation}</li>
                ))}
              </ul>
            </section>
          )}
        </details>
      )}
    </article>
  );
}
