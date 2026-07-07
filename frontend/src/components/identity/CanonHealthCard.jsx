const metrics = [
  ["Version", "version"],
  ["Documents", "documents"],
  ["Knowledge Layers", "layers"],
  ["Architecture Decisions", "architectureDecisions"],
  ["Sprint Records", "sprintRecords"],
];

export default function CanonHealthCard({ canonHealth }) {
  return (
    <section className="panel">
      <h2>Canon Health</h2>

      <div className="metric-list">
        {metrics.map(([label, key]) => (
          <div className="metric-row" key={key}>
            <span>{label}</span>
            <strong>{canonHealth[key]}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
