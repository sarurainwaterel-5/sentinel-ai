export function WorkspaceHeader({ title, description, onRefresh, loading }) {
  return (
    <section className="panel workspace-heading">
      <div>
        <p className="eyebrow">Mission</p>
        <h2>{title}</h2>
        <p className="muted">{description}</p>
      </div>
      {onRefresh && (
        <button
          className="secondary-action"
          onClick={onRefresh}
          disabled={loading}
        >
          Refresh observations
        </button>
      )}
    </section>
  );
}

export function ResourceState({ resource, label, children }) {
  if (resource.loading) return <p role="status">Loading {label}…</p>;
  if (resource.error)
    return (
      <div role="alert" className="workspace-error">
        <p>{resource.error}</p>
        <button className="secondary-action" onClick={resource.refresh}>
          Retry {label}
        </button>
      </div>
    );
  return children;
}

export function TextList({ items = [], empty = "None recorded." }) {
  return items.length ? (
    <ul className="workspace-list">
      {items.map((item, index) => (
        <li key={index}>{item}</li>
      ))}
    </ul>
  ) : (
    <p className="muted">{empty}</p>
  );
}

export function Judgment({ confidence, coherence, faculty }) {
  return (
    <div className="workspace-grid">
      <section className="workspace-instrument">
        <h3>{faculty} confidence</h3>
        <p>
          {confidence?.level ?? "Unreported"} ·{" "}
          {Math.round((confidence?.score ?? 0) * 100)}%
        </p>
        <p className="muted">{confidence?.basis}</p>
        <details>
          <summary>Inspect confidence factors</summary>
          {(confidence?.factors ?? []).map((factor, index) => (
            <p key={index}>
              <strong>{factor.name}</strong>: {factor.explanation} (contribution{" "}
              {factor.contribution})
            </p>
          ))}
        </details>
        <TextList
          items={confidence?.uncertainty}
          empty="No additional uncertainty recorded."
        />
      </section>
      <section className="workspace-instrument">
        <h3>Constitutional judgment</h3>
        <p>
          {coherence?.coherent
            ? "Reported coherent"
            : "Not constitutionally verified"}
        </p>
        <TextList
          items={coherence?.conflicts}
          empty="No conflicts reported; this is not permission to execute."
        />
        <p className="muted">
          Confidence and admissibility are independent. Human authorization is
          still required.
        </p>
      </section>
    </div>
  );
}
