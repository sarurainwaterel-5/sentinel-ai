import { UploadCloud } from "lucide-react";

const pageTitles = {
  bridge: {
    eyebrow: "Bridge",
    title: "Bridge",
    subtitle: "Operational intelligence overview",
  },
  teach: {
    eyebrow: "Teaching Session",
    title: "Teach SentinelAI",
    subtitle: "Expand SentinelAI's operational knowledge",
  },
  recall: {
    eyebrow: "Recall",
    title: "Recall Knowledge",
    subtitle: "Ask SentinelAI what it remembers",
  },
  reason: {
    eyebrow: "Reason",
    title: "Reason",
    subtitle: "Analyze evidence and build understanding",
  },
  intelligence: {
    eyebrow: "Intelligence",
    title: "Intelligence",
    subtitle: "Discover patterns across knowledge",
  },
  governance: {
    eyebrow: "Governance",
    title: "Governance",
    subtitle: "Protect SentinelAI's principles and memory",
  },
  systems: {
    eyebrow: "Systems",
    title: "Systems",
    subtitle: "Maintain the platform",
  },
};

export default function TopBar({ activePage }) {
  const page = pageTitles[activePage] || {
    eyebrow: "Workspace",
    title: "Coming Soon",
    subtitle: "This workspace is not active yet",
  };

  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">{page.eyebrow}</p>
        <h1>{page.title}</h1>
        <p className="subtitle">{page.subtitle}</p>
      </div>

      <div className="topbar-actions">
        <button className="primary-action">
          <UploadCloud size={18} />
          <span>Remember Knowledge</span>
        </button>

        <div className="system-status">
          <span className="status-dot"></span>
          <span>System Healthy</span>
        </div>
      </div>
    </header>
  );
}
