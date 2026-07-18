function formatStatus(status) {
  return status
    .replaceAll("_", " ")
    .replace(/\b\w/g, (character) => character.toUpperCase());
}

export default function DomainCard({ domain }) {
  const evidenceCount = domain.evidence?.length ?? 0;

  return (
    <article className="panel domain-card">
      <div className="domain-card-header">
        <div>
          <p className="eyebrow">
            {domain.kind === "system" ? "System Domain" : "User Domain"}
          </p>
          <h2>{domain.name}</h2>
        </div>

        <span className={`status-badge status-${domain.status}`}>
          {formatStatus(domain.status)}
        </span>
      </div>

      <p className="muted">{domain.description}</p>

      <div className="metric-list">
        <div className="metric-row">
          <span>Evidence Sources</span>
          <strong>{evidenceCount}</strong>
        </div>
      </div>
    </article>
  );
}
