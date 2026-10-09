import {
  Fingerprint,
  Radar,
  BookOpen,
  Search,
  BarChart3,
  Shield,
  Settings,
  Brain,
  Layers3,
  PanelLeftClose,
  PanelLeftOpen,
} from "lucide-react";

const navItems = [
  { key: "bridge", label: "Bridge", icon: Radar },
  { key: "identity", label: "Identity", icon: Fingerprint },
  { key: "domains", label: "Domains", icon: Layers3 },
  { key: "teach", label: "Teach", icon: BookOpen },
  { key: "recall", label: "Recall", icon: Search },
  { key: "reason", label: "Reason", icon: Brain },
  { key: "intelligence", label: "Intelligence", icon: BarChart3 },
  { key: "governance", label: "Governance", icon: Shield },
  { key: "systems", label: "Systems", icon: Settings },
];

export default function Sidebar({
  collapsed,
  onToggle,
  activePage,
  setActivePage,
}) {
  const ToggleIcon = collapsed ? PanelLeftOpen : PanelLeftClose;

  return (
    <aside className="sidebar">
      <button
        type="button"
        className="brand"
        aria-label="SentinelAI — return to Bridge"
        onClick={() => setActivePage("bridge")}
      >
        <svg className="brand-lockup" viewBox="100 135 1960 435" aria-hidden="true">
          <image href="/brand/sentinel-ai-logo-navy.png" width="2172" height="724" />
        </svg>
        <svg className="brand-mark" viewBox="100 135 510 435" aria-hidden="true">
          <image href="/brand/sentinel-ai-logo-navy.png" width="2172" height="724" />
        </svg>
        {!collapsed && <small>Intelligence OS</small>}
      </button>

      <button
        type="button"
        className="collapse-button"
        onClick={onToggle}
        aria-label={collapsed ? "Expand navigation" : "Collapse navigation"}
        aria-expanded={!collapsed}
      >
        <ToggleIcon size={18} />
        {!collapsed && <span>Collapse navigation</span>}
      </button>

      <nav className="nav">
        {navItems.map(({ key, label, icon: Icon }) => (
          <div key={key}>
            {!collapsed && ["bridge", "teach", "governance"].includes(key) && (
              <p className="nav-group">
                {key === "bridge"
                  ? "Workspace"
                  : key === "teach"
                    ? "Knowledge & intelligence"
                    : "Oversight"}
              </p>
            )}
            <button
              aria-label={label}
              aria-current={activePage === key ? "page" : undefined}
              type="button"
              className={`nav-item ${activePage === key ? "active" : ""}`}
              key={key}
              title={collapsed ? label : ""}
              onClick={() => setActivePage(key)}
            >
              <Icon size={18} />
              {!collapsed && <span>{label}</span>}
            </button>
          </div>
        ))}
      </nav>
    </aside>
  );
}
