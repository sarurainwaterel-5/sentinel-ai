const layerLabels = {
  canon: "Principles",
  identity: "Identity",
  philosophy: "Philosophy",
  architecture: "Architecture",
  engineering: "Engineering",
  design: "Design",
  cognition: "Cognition",
  history: "History",
};

export default function KnowledgeLayers({ layers }) {
  return (
    <section className="panel">
      <h2>Knowledge Layers</h2>

      <div className="layer-list">
        {Object.entries(layers).map(([layer, count]) => (
          <div className="layer-row" key={layer}>
            <span>{layerLabels[layer] ?? layer}</span>
            <strong>{count}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}
