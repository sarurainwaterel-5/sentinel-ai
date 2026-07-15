export default function IdentityOverview({ canonHealth }) {
  return (
    <section className="panel identity-overview">
      <div>
        <p className="eyebrow">Identity Status</p>
        <h2>{canonHealth.status === "healthy" ? "Healthy" : "Needs Attention"}</h2>
        <p className="muted">
          SentinelAI's permanent identity is present, organized, and ready.
        </p>
      </div>

      <div className="status-badge">
        {canonHealth.status}
      </div>
    </section>
  );
}
