export default function KnowledgeLayers({ layers }) {
  return (
    <section className="panel">
      <h2>Knowledge Layers</h2>

      <div className="layer-list">
        {Object.entries(layers).map(([layer, count]) => (
          <div className="layer-row" key={layer}>
            <span>{layer}</span>
            <strong>{count}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
