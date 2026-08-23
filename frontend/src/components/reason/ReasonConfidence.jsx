function labelFactor(factor) {
  const raw =
    factor?.name ??
    factor?.factor ??
    "Confidence factor";

  return String(raw)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase()
    );
}


export default function ReasonConfidence({
  confidence,
  evidence,
}) {
  if (!confidence) {
    return null;
  }

  const percent = Math.round(
    (confidence.score ?? 0) * 100
  );

  const uncertaintyCount =
    confidence.uncertainty?.length ?? 0;

  return (
    <article className="panel reason-confidence">
      <p className="eyebrow">
        Evidence Confidence
      </p>

      <div className="reason-instrument-heading">
        <strong className="reason-instrument-value">
          {percent}%
        </strong>

        <span className="reason-instrument-state">
          {confidence.level}
        </span>
      </div>

      <div
        className="reason-meter"
        role="progressbar"
        aria-label="Evidence confidence"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow={percent}
      >
        <span
          style={{
            width: `${percent}%`,
          }}
        />
      </div>

      {confidence.basis && (
        <p className="reason-instrument-basis">
          {confidence.basis}
        </p>
      )}

      <div className="reason-instrument-summary">
        <span>
          {evidence?.source_count ?? 0} sources
        </span>

        <span>
          {evidence?.document_count ?? 0} documents
        </span>

        <span>
          {uncertaintyCount}{" "}
          {uncertaintyCount === 1
            ? "uncertainty"
            : "uncertainties"}
        </span>
      </div>

      {(
        confidence.factors?.length > 0 ||
        confidence.uncertainty?.length > 0
      ) && (
        <details className="reason-instrument-details">
          <summary>
            Inspect confidence basis
          </summary>

          {confidence.factors?.length > 0 && (
            <section>
              <p className="eyebrow">
                Contributing Factors
              </p>

              <ul>
                {confidence.factors.map(
                  (factor, index) => (
                    <li key={index}>
                      {labelFactor(factor)}
                    </li>
                  )
                )}
              </ul>
            </section>
          )}

          {confidence.uncertainty?.length > 0 && (
            <section>
              <p className="eyebrow">
                Uncertainty
              </p>

              <ul>
                {confidence.uncertainty.map(
                  (item, index) => (
                    <li key={index}>
                      {item}
                    </li>
                  )
                )}
              </ul>
            </section>
          )}
        </details>
      )}

      <p className="muted reason-confidence-doctrine">
        Confidence measures available evidentiary
        support, not objective certainty.
      </p>
    </article>
  );
}
