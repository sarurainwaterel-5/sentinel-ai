function formatStatus(status = "unknown") {
  return status.replaceAll("_", " ");
}

export default function DomainCard({
  domain,
  memory,
  current,
  onSelect,
  onEnter,
}) {
  return (
    <article
      className={`panel domain-card ${current ? "domain-current" : ""}`}
      aria-label={`${domain.name} domain`}
    >
      <div className="domain-card-header">
        <div>
          <p className="eyebrow">
            {domain.kind === "system" ? "System domain" : "User domain"}
          </p>
          <h2>{domain.name}</h2>
        </div>
        <span className={`status-badge status-${domain.status}`}>
          Maturity: {formatStatus(domain.status)}
        </span>
      </div>
      <p className="muted">{domain.description}</p>
      {memory ? (
        <dl className="domain-memory">
          <div>
            <dt>Indexed PDFs</dt>
            <dd>{memory.indexed_documents}</dd>
          </div>
          <div>
            <dt>Indexed chunks</dt>
            <dd>{memory.indexed_chunks}</dd>
          </div>
          <div>
            <dt>Archived PDFs</dt>
            <dd>{memory.archived_documents}</dd>
          </div>
          {memory.other_documents > 0 && (
            <div>
              <dt>Other catalog records</dt>
              <dd>{memory.other_documents}</dd>
            </div>
          )}
        </dl>
      ) : (
        <p className="muted">Memory counts unavailable.</p>
      )}
      {memory?.indexed_documents === 0 && (
        <p className="muted">
          Teach a PDF in this domain to add evidence for Recall.
        </p>
      )}
      <div className="domain-actions">
        <button
          className="primary-action"
          aria-pressed={current}
          onClick={onSelect}
        >
          {current ? "Current domain" : `Select ${domain.name}`}
        </button>
        <button className="secondary-action" onClick={() => onEnter("teach")}>
          Teach
        </button>
        <button className="secondary-action" onClick={() => onEnter("recall")}>
          Recall
        </button>
        <button className="secondary-action" onClick={() => onEnter("reason")}>
          Reason
        </button>
        <button
          className="secondary-action"
          onClick={() => onEnter("governance")}
        >
          Manage memory
        </button>
      </div>
      <details>
        <summary>
          Architecture references ({domain.evidence?.length ?? 0})
        </summary>
        {domain.evidence?.map((reference) => (
          <div className="domain-reference" key={reference.evidence_id}>
            <strong>{reference.title}</strong>
            <p className="muted">{reference.description}</p>
            <small>{reference.source}</small>
          </div>
        ))}
        {!domain.evidence?.length && (
          <p className="muted">No architecture references recorded.</p>
        )}
      </details>
    </article>
  );
}
