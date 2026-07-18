export default function DomainSummary({ summary }) {
  return (
    <section className="panel">
      <p className="eyebrow">Domain Summary</p>
      <h2>{summary.total_domains} available domains</h2>

      <div className="metric-list">
        <div className="metric-row">
          <span>System Domains</span>
          <strong>{summary.system_domains}</strong>
        </div>

        <div className="metric-row">
          <span>User Domains</span>
          <strong>{summary.user_domains}</strong>
        </div>

        <div className="metric-row">
          <span>Active</span>
          <strong>{summary.active_domains}</strong>
        </div>

        <div className="metric-row">
          <span>Developing</span>
          <strong>{summary.developing_domains}</strong>
        </div>

        <div className="metric-row">
          <span>Planned</span>
          <strong>{summary.planned_domains}</strong>
        </div>
      </div>
    </section>
  );
}
