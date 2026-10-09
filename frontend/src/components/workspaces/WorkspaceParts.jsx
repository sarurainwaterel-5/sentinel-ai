export function WorkspaceHeader({ title, description, onRefresh, loading }) {
  return (
    <section className="workspace-heading">
      <div>
        <details className="workspace-purpose">
          <summary>Workspace purpose</summary>
          <h2>{title}</h2>
          <p className="muted">{description}</p>
        </details>
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

export function WorkspaceTabs({ tabs, active, onChange }) {
  return (
    <div className="workspace-tabs" role="tablist" aria-label="Workspace tools">
      {tabs.map((tab, index) => (
        <button
          key={tab}
          id={`tab-${tab}`}
          role="tab"
          aria-selected={active === tab}
          aria-controls={`panel-${tab}`}
          tabIndex={active === tab ? 0 : -1}
          onClick={() => onChange(tab)}
          onKeyDown={(event) => {
            let next;
            if (event.key === "ArrowRight") next = (index + 1) % tabs.length;
            if (event.key === "ArrowLeft")
              next = (index + tabs.length - 1) % tabs.length;
            if (event.key === "Home") next = 0;
            if (event.key === "End") next = tabs.length - 1;
            if (next !== undefined) {
              event.preventDefault();
              onChange(tabs[next]);
              document.getElementById(`tab-${tabs[next]}`)?.focus();
            }
          }}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}
export function ToolPanel({ name, active, children }) {
  return (
    <div
      role="tabpanel"
      id={`panel-${name}`}
      aria-labelledby={`tab-${name}`}
      hidden={active !== name}
    >
      {children}
    </div>
  );
}
