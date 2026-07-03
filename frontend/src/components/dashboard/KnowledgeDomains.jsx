export default function KnowledgeDomains({ domains }) {
  return (
    <section className="panel">
      <h2>Knowledge Domains</h2>
      {domains.map((domain) => (
        <div className="row" key={domain.name}>
          <span>{domain.name}</span>
          <strong>{domain.document_count} documents</strong>
        </div>
      ))}
    </section>
  );
}
