export default function RecallWorkspaceCard({
  activeDomain,
  result,
}) {
  const sources = result?.sources ?? [];

  const documentCount = new Set(
    sources
      .map((source) => source.document_id)
      .filter(Boolean),
  ).size;

  const connectionCount =
    result?.related_knowledge?.length ?? 0;

  return (
    <article className="panel recall-workspace-card">
      <div>
        <p className="eyebrow">
          Current Workspace
        </p>

        <h3>
          {activeDomain?.name ?? "All Domains"}
        </h3>

        <p className="muted">
          Evidence assembled from the current
          operational context.
        </p>
      </div>

      <div className="workspace-card-stats">
        <div>
          <strong>{sources.length}</strong>
          <span>Supporting chunks</span>
        </div>

        <div>
          <strong>{documentCount}</strong>
          <span>Supporting documents</span>
        </div>

        <div>
          <strong>{connectionCount}</strong>
          <span>Knowledge connections</span>
        </div>
      </div>
    </article>
  );
}

