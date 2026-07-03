export default function OverviewCards({ overview }) {
  const cards = [
    ["Documents", overview.total_documents],
    ["Indexed", overview.indexed_documents],
    ["Archived", overview.archived_documents],
    ["Domains", overview.knowledge_domains],
    ["Topics", overview.topics],
    ["Collections", overview.collections],
    ["Chunks", overview.indexed_chunks],
  ];

  return (
    <section className="grid">
      {cards.map(([label, value]) => (
        <div className="card" key={label}>
          <p>{label}</p>
          <h2>{value}</h2>
        </div>
      ))}
    </section>
  );
}
