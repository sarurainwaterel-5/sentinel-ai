function formatStatus(status) {
  return status.replaceAll("_", " ");
}

export default function DomainValidation({ validation }) {
  const concerns = validation.checks.filter(
    (check) => check.level !== "pass",
  );

  return (
    <section className="panel">
      <p className="eyebrow">Domain Validation</p>
      <h2>{formatStatus(validation.status)}</h2>

      <div className="metric-list">
        <div className="metric-row">
          <span>Passed Checks</span>
          <strong>{validation.passed}</strong>
        </div>

        <div className="metric-row">
          <span>Warnings</span>
          <strong>{validation.warnings}</strong>
        </div>

        <div className="metric-row">
          <span>Errors</span>
          <strong>{validation.errors}</strong>
        </div>
      </div>

      {concerns.length > 0 && (
        <div className="domain-concerns">
          <p className="eyebrow">Open Concerns</p>

          {concerns.map((check) => (
            <p className="muted" key={`${check.domain_id}-${check.name}`}>
              {check.domain_id}: {check.message}
            </p>
          ))}
        </div>
      )}
    </section>
  );
}
