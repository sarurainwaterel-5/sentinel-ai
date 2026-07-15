function formatStatus(status) {
  if (!status) return "Unknown";

  const normalized = status.toLowerCase();

  if (normalized === "healthy") return "● Healthy";
  if (normalized === "warning") return "● Needs attention";
  if (normalized === "critical") return "● Critical";

  return status;
}

function formatServiceName(service) {
  const labels = {
    principles: "Core Principles",
    connections: "Connections",
    reflection: "Reflection",
  };

  return labels[service] ?? service;
}

export default function OperationalHealth({ health }) {
  const services = health?.services ?? {};
  const warningCount = health?.warnings ?? 0;

  return (
    <section className="panel operational-health">
      <p className="eyebrow">Operational Health</p>
      <h2>{formatStatus(health?.overall)}</h2>

      <p className="muted">
        SentinelAI&apos;s cognitive systems are being observed through The
        Bridge.
      </p>

      <div className="metric-list">
        <div className="metric-row">
          <span>Warnings</span>
          <strong>
            {warningCount === 0 ? "No warnings" : warningCount}
          </strong>
        </div>

        {Object.entries(services).map(([service, status]) => (
          <div className="metric-row" key={service}>
            <span>{formatServiceName(service)}</span>
            <strong>{formatStatus(status)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
