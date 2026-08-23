export default function ReasonEvidenceSource({
  source,
}) {
  const score = Math.round(
    (source?.score ?? 0) * 100
  );

  const sourceLabel =
    source?.filename ??
    source?.document_id ??
    "Unknown source";

  return (
    <article className="reason-evidence-source">
      <header>
        <div>
          <strong>
            {sourceLabel}
          </strong>

          {source?.description && (
            <p className="muted">
              {source.description}
            </p>
          )}
        </div>

        <span>{score}% relevance</span>
      </header>

      <div className="reason-source-meta">
        {source?.module && (
          <span>{source.module}</span>
        )}

        {source?.topic && (
          <span>{source.topic}</span>
        )}

        {source?.collection && (
          <span>{source.collection}</span>
        )}

        {source?.chunk_index != null && (
          <span>
            Chunk {source.chunk_index}
          </span>
        )}
      </div>

      {source?.text && (
        <>
          <p className="reason-evidence-preview">
            {source.text}
          </p>

          <details className="reason-evidence-inspector">
            <summary>
              Inspect Evidence
            </summary>

            <div className="reason-evidence-full">
              <p>{source.text}</p>

              <dl className="reason-evidence-provenance">
                {source?.document_id && (
                  <>
                    <dt>Document ID</dt>
                    <dd>
                      {source.document_id}
                    </dd>
                  </>
                )}

                {source?.file_hash && (
                  <>
                    <dt>File Hash</dt>
                    <dd>
                      {source.file_hash}
                    </dd>
                  </>
                )}

                {source?.organization_id && (
                  <>
                    <dt>Organization</dt>
                    <dd>
                      {source.organization_id}
                    </dd>
                  </>
                )}

                {source?.status && (
                  <>
                    <dt>Status</dt>
                    <dd>
                      {source.status}
                    </dd>
                  </>
                )}
              </dl>
            </div>
          </details>
        </>
      )}
    </article>
  );
}
