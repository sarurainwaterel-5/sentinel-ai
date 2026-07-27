export default function RecallAnswer({
  answer,
  domainLabel,
}) {
  if (!answer) {
    return null;
  }

  return (
    <article className="panel recall-answer-panel">
      <div className="recall-section-heading">
        <div>
          <p className="eyebrow">Sentinel Response</p>
          <h2>Recall Result</h2>
        </div>

        {domainLabel && (
          <span className="recall-domain-badge">
            {domainLabel}
          </span>
        )}
      </div>

      <div className="recall-answer">
        {answer}
      </div>
    </article>
  );
}
