import { useDomain } from "../context/useDomain";
import { useWorkspaceData } from "../components/workspaces/useWorkspaceData";
import { ResourceState, TextList, WorkspaceHeader } from "../components/workspaces/WorkspaceParts";

const destinations = [
  ["teach", "Teach", "Add source documents to memory."],
  ["recall", "Recall", "Find evidence in taught knowledge."],
  ["reason", "Reason", "Examine a question against evidence."],
  ["intelligence", "Intelligence", "Inspect connections, reflection, and plans."],
  ["governance", "Governance", "Review integrity and manage memory."],
  ["systems", "Systems", "Inspect storage and capability readiness."],
  ["identity", "Identity", "Read Sentinel’s governing principles."],
  ["domains", "Domains", "Choose your knowledge context."],
];
export default function Bridge({ onNavigate }) {
  const { activeDomain } = useDomain();
  const summary = useWorkspaceData("/bridge/summary");
  const memory = useWorkspaceData("/domains/memory?organization_id=default");
  const activity = useWorkspaceData("/intelligence/learning-events?organization_id=default&limit=5");
  const scope = activeDomain?.id ?? "all";
  const statistics = Object.entries(memory.data?.domains ?? {})
    .filter(([id]) => scope === "all" || id === scope)
    .reduce((total, [, row]) => ({ indexed: total.indexed + row.indexed_documents, archived: total.archived + row.archived_documents, chunks: total.chunks + row.indexed_chunks }), { indexed: 0, archived: 0, chunks: 0 });
  const refresh = () => { summary.refresh(); memory.refresh(); activity.refresh(); };
  const navigate = (id) => onNavigate?.(id);
  return <div className="page workspace-page">
    <WorkspaceHeader title="Awareness before action" description="Observe the platform, memory, and recorded activity before choosing your next workspace." onRefresh={refresh} loading={summary.loading || memory.loading || activity.loading} />
    <section className="panel"><p className="eyebrow">Platform condition</p>
      <ResourceState resource={summary} label="platform observations">
        <h2>{summary.data?.health?.overall === "Ready" ? "Storage ready" : "Attention required"}</h2>
        <p className="muted">Observed {summary.data?.health?.observed_at ? new Date(summary.data.health.observed_at).toLocaleString() : "time unavailable"}. Refresh to check current conditions.</p>
        <div className="metric-list">{Object.entries(summary.data?.health?.services ?? {}).map(([name, status]) => <div className="metric-row" key={name}><span>{name}</span><strong>{status.replaceAll("_", " ")}</strong></div>)}</div>
        <p>{summary.data?.health?.model_features_configured ? "Model credentials configured; provider availability is checked when requested." : "Model credentials required for Recall, Reason, Planning, and Verification."}</p>
        <details><summary>Observations requiring attention</summary><TextList items={summary.data?.health?.observations} empty="No operational warnings recorded." /></details>
        <button className="secondary-action" onClick={() => navigate("systems")}>Inspect Systems</button>
      </ResourceState>
    </section>
    <div className="workspace-grid">
      <section className="panel"><p className="eyebrow">Current context</p><h2>{activeDomain?.name ?? "All Domains"}</h2>
        <p className="muted">Bridge · Local administrator workspace. Your domain selection carries into Teach, Recall, and Reason.</p>
        <ResourceState resource={memory} label="knowledge counts">
          <div className="metric-list"><div className="metric-row"><span>Indexed documents</span><strong>{statistics.indexed}</strong></div><div className="metric-row"><span>Cataloged chunks</span><strong>{statistics.chunks}</strong></div><div className="metric-row"><span>Archived documents</span><strong>{statistics.archived}</strong></div></div>
          <p className="muted">Catalog observations; chunk counts do not verify vector integrity or understanding.</p>
          {!statistics.indexed && <p>No indexed documents in this context. Begin in Teach or choose another domain.</p>}
        </ResourceState>
        <button className="secondary-action" onClick={() => navigate("domains")}>Choose domain</button>
      </section>
      <section className="panel"><p className="eyebrow">Principle integrity</p>
        <ResourceState resource={summary} label="principle observations">
          <h2>Structure: {summary.data?.canon?.health ?? "unavailable"}</h2>
          <p>{summary.data?.canon?.documents} principle documents · {summary.data?.canon?.layers} knowledge layers</p>
          <TextList items={summary.data?.canon?.warnings} empty="No structural warnings recorded." />
          <p className="workspace-notice">Constitutional semantic evaluation: not independently verified. Execution authority remains human.</p>
          <details><summary>Documented connections</summary><p>{summary.data?.graph?.nodes} structural nodes · {summary.data?.graph?.edges} structural connections. These describe document organization, not semantic truth.</p></details>
        </ResourceState>
        <button className="secondary-action" onClick={() => navigate("governance")}>Review Governance</button>
      </section>
    </div>
    <section className="panel"><p className="eyebrow">Recent activity</p><h2>Recorded learning</h2>
      <p className="muted">Latest five recorded Learning Events across your local organization. Imported documents may predate event recording; this is not a complete activity log.</p>
      <ResourceState resource={activity} label="learning activity">{(activity.data ?? []).length ? <ul className="workspace-list">{activity.data.map((event) => <li key={event.learning_event_id}><strong>{event.source || "Recorded acquisition"}</strong><p>{event.summary}</p><p className="muted">{event.learned_at ? new Date(event.learned_at).toLocaleString() : "Time unreported"} · {(event.domain_ids ?? []).join(", ") || "Domain unreported"}</p></li>)}</ul> : <p>No Learning Events recorded yet. Your document catalog remains available above.</p>}</ResourceState>
      <button className="secondary-action" onClick={() => navigate("intelligence")}>Inspect Intelligence</button>
    </section>
    <section className="panel"><p className="eyebrow">Choose your next workspace</p><h2>Continue your work</h2><div className="workspace-grid">{destinations.map(([id, title, detail]) => <div className="workspace-instrument" key={id}><button className="secondary-action" onClick={() => navigate(id)}>{title}</button><p className="muted">{detail}</p></div>)}</div></section>
  </div>;
}
