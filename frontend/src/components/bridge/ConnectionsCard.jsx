const relationshipLabels = {
  belongs_to: "Organized under",
  classified_as: "Classified as",
  references: "References",
  extends: "Extends",
  implements: "Implements",
};

export default function ConnectionsCard({ graph }) {
  const relationships = graph?.relationships ?? {};

  return (
    <section className="panel">
      <p className="eyebrow">Connections</p>

      <h2>Mapped</h2>

      <p className="muted">
        SentinelAI has mapped <strong>{graph?.nodes ?? 0}</strong> knowledge
        points across <strong>{graph?.edges ?? 0}</strong> active connections.
      </p>

      <div className="metric-list">
        {Object.entries(relationships).map(([name, count]) => (
          <div className="metric-row" key={name}>
            <span>{relationshipLabels[name] ?? name.replaceAll("_", " ")}</span>
            <strong>{count}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
