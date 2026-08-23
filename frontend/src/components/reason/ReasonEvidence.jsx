import ReasonEvidenceSource from "./ReasonEvidenceSource";


export default function ReasonEvidence({
  evidence,
}) {
  if (!evidence) {
    return null;
  }

  return (
    <article className="panel reason-evidence">
      <p className="eyebrow">
        Evidence
      </p>

      <div className="reason-evidence-metrics">
        <div>
          <strong>
            {evidence.source_count ?? 0}
          </strong>
          <span>Sources</span>
        </div>

        <div>
          <strong>
            {evidence.document_count ?? 0}
          </strong>
          <span>Documents</span>
        </div>

        <div>
          <strong>
            {evidence.domain_count ?? 0}
          </strong>
          <span>Domains</span>
        </div>
      </div>

      {evidence.sources?.map(
        (source, index) => (
          <ReasonEvidenceSource
            key={
              `${source.document_id ?? "source"}-${source.chunk_index ?? index}`
            }
            source={source}
          />
        )
      )}

      {evidence.gaps?.length > 0 && (
        <section className="reason-evidence-gaps">
          <p className="eyebrow">
            Evidence Gaps
          </p>

          <ul>
            {evidence.gaps.map(
              (gap, index) => (
                <li key={index}>
                  {gap}
                </li>
              )
            )}
          </ul>
        </section>
      )}
    </article>
  );
}
