import { UploadCloud } from "lucide-react";
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

export default function TopBar({ activePage }) {
  const page = pageTitles[activePage] || {
    eyebrow: "Workspace",
    title: "Coming Soon",
    subtitle: "This workspace is not active yet",
  };



const {
  activeDomain,
  availableDomains,
  selectDomain,
} = useDomain();


  return (
    <header className="topbar">
      <div className="domain-selector">
  <label htmlFor="active-domain">
    Current Domain
  </label>

  <select
    id="active-domain"
    value={activeDomain?.id ?? "all"}
    onChange={(event) =>
      selectDomain(event.target.value)
    }
  >
    <option value="all">
      All Domains
    </option>

    {availableDomains.map((domain) => (
      <option
        key={domain.id}
        value={domain.id}
      >
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
        <button className="primary-action">
          <UploadCloud size={18} />
          <span>Refresh Knowledge</span>
        </button>

        <div className="system-status">
          <span className="status-dot"></span>
          <span>Operational</span>
        </div>
      </div>
    </header>
  );
}
