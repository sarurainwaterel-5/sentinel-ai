export default function DomainsOverview({ summary }) {
  return (
    <section className="panel">
      <p className="eyebrow">Domains</p>
      <h1>Operational contexts available to SentinelAI.</h1>

      <p className="muted">
        One identity operating through {summary.total_domains} validated
        domains.
      </p>
    </section>
  );
}
