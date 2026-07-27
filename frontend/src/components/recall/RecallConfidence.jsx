export default function RecallConfidence({
  confidence,
  sourceCount = 0,
}) {
  if (!confidence) {
    return null;
  }

  const score = Number(confidence.score ?? 0);
  const percentage = Math.round(score * 100);
  const level = confidence.level ?? "low";
  const label =
    level.charAt(0).toUpperCase() + level.slice(1);

  return (
    <article className="panel recall-confidence-panel">
      <div className="recall-section-heading">
        <div>
          <p className="eyebrow">Evidence Confidence</p>
          <h3>{label}</h3>
        </div>

        <span
          className={`confidence-badge confidence-${level}`}
        >
          {percentage}%
        </span>
      </div>

      <div className="confidence-track">
        <div
          className={`confidence-fill confidence-fill-${level}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      {confidence.basis && (
        <p>{confidence.basis}</p>
      )}

      <p className="muted">
        Supported by {sourceCount} retrieved chunk
        {sourceCount === 1 ? "" : "s"}.
      </p>
    </article>
  );
}
