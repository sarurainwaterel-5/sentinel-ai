import { UploadCloud } from "lucide-react";
import { useWorkspaceData } from "../workspaces/useWorkspaceData";
import { useDomain } from "../../context/useDomain";

const pageTitles = {
  bridge: {
    eyebrow: "Bridge",
    title: "Bridge",
    subtitle: "Operational Intelligence Overview",
  },
  identity: {
    eyebrow: "Identity",
    title: "SentinelAI Identity",
    subtitle: "Define the principles that shape SentinelAI.",
  },
  teach: {
    eyebrow: "Teaching Session",
    title: "Teach SentinelAI",
    subtitle: "Expand SentinelAI's Operational knowledge",
  },
  recall: {
    eyebrow: "Recall",
    title: "Recall Knowledge",
    subtitle: "Ask SentinelAI what it Remembers",
  },
  reason: {
    eyebrow: "Reason",
    title: "Reason",
    subtitle: "Analyze Evidence and Build Understanding",
  },
  intelligence: {
    eyebrow: "Intelligence",
    title: "Intelligence",
    subtitle: "Discover Patterns Across Knowledge",
  },
  governance: {
    eyebrow: "Governance",
    title: "Governance",
    subtitle: "Protect SentinelAI's Principles and Memory",
  },
  systems: {
    eyebrow: "Systems",
    title: "Systems",
    subtitle: "Maintain the Platform",
  },
};

export default function TopBar({ activePage, setActivePage }) {
  const status = useWorkspaceData("/systems/status");
  const page = pageTitles[activePage] || {
    eyebrow: "Workspace",
    title: "Coming Soon",
    subtitle: "This workspace is not active yet",
  };

  const { activeDomain, availableDomains, selectDomain } = useDomain();

  return (
    <header className="topbar">
      <div className="domain-selector">
        <label htmlFor="active-domain">Current Domain</label>

        <select
          id="active-domain"
          value={activeDomain?.id ?? "all"}
          onChange={(event) => selectDomain(event.target.value)}
        >
          <option value="all">All Domains</option>

          {availableDomains.map((domain) => (
            <option key={domain.id} value={domain.id}>
              {domain.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <p className="eyebrow">{page.eyebrow}</p>
        <h1>{page.title}</h1>
        <p className="subtitle">{page.subtitle}</p>
      </div>

      <div className="topbar-actions">
        <button
          className="primary-action"
          onClick={() => setActivePage("teach")}
        >
          <UploadCloud size={18} />
          <span>Teach Sentinel</span>
        </button>

        <details className="readiness-menu">
          <summary className="system-status">
            <span
              className={`status-dot ${status.loading || status.error || status.data?.status !== "ready" ? "status-attention" : ""}`}
            ></span>
            <span>
              {status.loading
                ? "Checking readiness"
                : status.error
                  ? "Status unavailable"
                  : status.data?.status === "ready"
                    ? "Storage ready"
                    : "Attention required"}
            </span>
          </summary>
          <div className="readiness-details">
            <h2>System observations</h2>
            {status.error && <p role="alert">{status.error}</p>}
            {(status.data?.services ?? []).map((service) => (
              <p key={service.name}>
                <strong>
                  {service.name}: {service.status.replaceAll("_", " ")}
                </strong>
                <br />
                {service.detail}
              </p>
            ))}
            {status.data && (
              <>
                <p>
                  Provider credentials:{" "}
                  {status.data.model_features_configured
                    ? "Configured; availability checked per request"
                    : "Required"}
                </p>
                <p>Constitutional evaluation: not independently verified</p>
              </>
            )}
            <button
              className="secondary-action"
              onClick={status.refresh}
              disabled={status.loading}
            >
              Refresh status
            </button>
            <button
              className="secondary-action"
              onClick={() => setActivePage("systems")}
            >
              Open Systems
            </button>
          </div>
        </details>
      </div>
    </header>
  );
}
