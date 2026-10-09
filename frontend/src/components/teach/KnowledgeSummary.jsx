export default function KnowledgeSummary({ mission, onNavigate }) {
  const result = mission?.result;
  return <section className="panel"><h2>Knowledge Summary</h2>
    {mission?.status === "completed" ? <>
      <div className="metric-list"><div className="metric-row"><span>Extracted characters</span><strong>{result.characters}</strong></div><div className="metric-row"><span>Memory chunks</span><strong>{result.chunks}</strong></div><div className="metric-row"><span>Domain</span><strong>{result.module}</strong></div></div>
      <p>{result.learning_event_id ? "Acquisition recorded as a Learning Event." : "Acquisition history requires attention."}</p>
      <p className="muted">Memory was indexed at mission completion. Recall uses currently active catalog entries; Governance manages archive status.</p>
      <button className="secondary-action" onClick={() => onNavigate?.("recall")}>Open Recall</button>
      <details><summary>Inspect source provenance</summary><p>Document: {result.document_id}</p><p className="source-fingerprint">SHA-256: {result.file_hash}</p><p>Embedding model: {result.embedding_model}</p></details>
    </> : <p className="muted">Select a completed mission to inspect its actual memory additions. Duplicate, failed, and interrupted missions do not imply new indexed knowledge.</p>}
  </section>;
}
