import { useWorkspaceData } from "../components/workspaces/useWorkspaceData";
import {
  ResourceState,
  TextList,
  WorkspaceHeader,
} from "../components/workspaces/WorkspaceParts";

export default function Systems() {
  const status = useWorkspaceData("/systems/status");
  return (
    <div className="page workspace-page">
      <WorkspaceHeader
        title="Observe the platform before beginning a mission"
        description="Measured storage availability and capability configuration, separate from cognitive confidence and constitutional acceptance."
        onRefresh={status.refresh}
        loading={status.loading}
      />
      <section className="panel">
        <h2>Operational condition</h2>
        <ResourceState resource={status} label="system condition">
          <p className="workspace-condition">
            {status.data?.status === "ready"
              ? "Storage ready"
              : "Attention required"}
          </p>
          <p className="muted">
            Observed{" "}
            {status.data?.observed_at &&
              new Date(status.data.observed_at).toLocaleString()}
          </p>
          <div className="workspace-grid">
            {status.data?.services.map((service) => (
              <section className="workspace-instrument" key={service.name}>
                <h3>{service.name}</h3>
                <p>{service.status.replaceAll("_", " ")}</p>
                <p className="muted">{service.detail}</p>
              </section>
            ))}
          </div>
          <h3>Cognitive readiness</h3>
          <p>
            Recall, Reason, Planning, and Verification:{" "}
            {status.data?.model_features_configured
              ? "Credentials configured; provider availability is checked when requested."
              : "Model credentials required."}
          </p>
          <p>Constitutional semantic evaluation: not independently verified</p>
          <p>Semantic proposition grounding: not independently verified</p>
          <p className="workspace-notice">
            Available storage and configured credentials do not establish the
            correctness of a cognitive result.
          </p>
          <h3>Observations requiring attention</h3>
          <TextList items={status.data?.warnings} />
        </ResourceState>
      </section>
      <section className="panel">
        <h2>Operator maintenance</h2>
        <ol className="workspace-list">
          <li>
            Refresh observations to check current availability before a mission.
          </li>
          <li>
            Use Governance to archive or restore operational memory without
            deleting history.
          </li>
          <li>
            If storage is unavailable, restart Sentinel using your
            Start-Sentinel launcher, then check this workspace again.
          </li>
          <li>
            If model credentials are missing or rejected, update the private
            backend environment settings and restart Sentinel.
          </li>
        </ol>
        <p className="muted">
          The local installation preserves its document catalog, vector memory,
          uploads, and cognitive history across restarts.
        </p>
      </section>
    </div>
  );
}
