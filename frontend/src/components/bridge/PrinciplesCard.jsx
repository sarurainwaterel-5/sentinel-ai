export default function PrinciplesCard({ canon }) {
  return (
    <section className="panel">
      <p className="eyebrow">Core Principles</p>
      <h2>{canon.health === "healthy" ? "Healthy" : "Needs Attention"}</h2>

      <div className="metric-list">
        <div className="metric-row">
          <span>Principle Documents</span>
          <strong>{canon.documents}</strong>
        </div>
        <div className="metric-row">
          <span>Knowledge Layers</span>
          <strong>{canon.layers}</strong>
        </div>
        <div className="metric-row">
          <span>Warnings</span>
          <strong>{canon.warnings?.length ?? 0}</strong>
        </div>
      </div>
    </section>
  );
}
