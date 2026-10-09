import { Fragment } from "react";
export default function ReasonEvidenceSource({ source }) {
  const score = typeof source?.score === "number" ? `${Math.round(source.score * 100)}% similarity` : "Similarity unreported";
  const label = source?.filename ?? source?.document_id ?? "Unknown source";
  return <article className="reason-evidence-source">
    <header><div><strong>{label}</strong>{source?.description && <p className="muted">{source.description}</p>}</div><span>{score}</span></header>
    <div className="reason-source-meta">{source?.module && <span>{source.module}</span>}{source?.topic && <span>{source.topic}</span>}{source?.collection && <span>{source.collection}</span>}{source?.chunk_index != null && <span>Chunk {source.chunk_index}</span>}</div>
    {source?.text && <p className="reason-evidence-preview">{source.text}</p>}
    <details className="reason-evidence-inspector"><summary>Inspect Evidence</summary><div className="reason-evidence-full">
      <p>{source?.text || "Source text was not reported."}</p>
      <dl className="reason-evidence-provenance">{[["Document ID", source?.document_id], ["File Hash", source?.file_hash], ["Organization", source?.organization_id], ["Status", source?.status]].filter(([, value]) => value).map(([name, value]) => <Fragment key={name}><dt>{name}</dt><dd>{value}</dd></Fragment>)}</dl>
    </div></details>
  </article>;
}
