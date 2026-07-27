export default function RecallEvidence({ sources = [] }) {
  if (!sources.length) {
    return (
      <section className="recall-evidence">
        <h3>Evidence</h3>
        <p className="muted">
          No supporting evidence was returned.
        </p>
      </section>
    );
  }

  return (
    <section className="recall-evidence">
      <div className="recall-section-heading">
        <div>
          <p className="eyebrow">Traceability</p>
          <h3>Evidence</h3>
        </div>

        <span className="evidence-count">
          {sources.length} source{sources.length === 1 ? "" : "s"}
        </span>
      </div>

      <div className="evidence-list">
        {sources.map((source, index) => (
          <article
            className="evidence-card"
            key={`${source.document_id ?? source.filename}-${source.chunk_index}-${index}`}
          >
            <div className="evidence-card-header">
  <div>
    <h4>{source.filename}</h4>

    {source.description &&
      source.description.trim().toLowerCase() !== "string" && (
        <p className="muted">
          {source.description}
        </p>
    )}
  </div>

  {(() => {
  const score = Number(source.score ?? 0);

  const level =
    score >= 0.8
      ? "high"
      : score >= 0.6
        ? "moderate"
        : "low";

  return (
    <span
      className={`evidence-score evidence-score-${level}`}
    >
      {(score * 100).toFixed(1)}%
      {" · "}
      {level}
    </span>
  );
})()}
</div>
            <div className="evidence-tags">
              {source.module && (
                <span className="evidence-tag">
                  {source.module}
                </span>
              )}

              {source.topic && (
                <span className="evidence-tag">
                  {source.topic}
                </span>
              )}

              {source.collection && (
                <span className="evidence-tag evidence-domain-tag">
                  {source.collection}
                </span>
              )}
            </div>

            <div className="evidence-meta">
              <span>Chunk {source.chunk_index}</span>
              <span>Status: {source.status ?? "unknown"}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
