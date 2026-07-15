import {
  Fingerprint,
  Radar,
  BookOpen,
  Bot,
  Search,
  BarChart3,
  Shield,
  Settings,
  Brain,
  PanelLeftClose,
  PanelLeftOpen
} from "lucide-react";

const navItems = [
  { key: "bridge", label: "Bridge", icon: Radar },
  { key: "identity", label: "Identity", icon: Fingerprint },
  { key: "teach", label: "Teach", icon: BookOpen },
  { key: "recall", label: "Recall", icon: Search },
  { key: "reason", label: "Reason", icon: Brain },
  { key: "intelligence", label: "Intelligence", icon: BarChart3 },
  { key: "governance", label: "Governance", icon: Shield },
  { key: "systems", label: "Systems", icon: Settings },
];

export default function Sidebar({ collapsed, onToggle, activePage, setActivePage }) {
  const ToggleIcon = collapsed ? PanelLeftOpen : PanelLeftClose;

  return (
    <aside className="sidebar">
      <div className="brand">
        <Brain size={26} />

        {!collapsed && (
          <div>
            <h2>SentinelAI</h2>
            <small>Intelligence OS</small>
          </div>
        )}
      </div>

      <button
        type="button"
        className="collapse-button"
        onClick={onToggle}
        aria-label="Toggle Bridge"
      >
        <ToggleIcon size={18} />
        {!collapsed && <span>Collapse Bridge</span>}
      </button>

      <nav className="nav">
        {navItems.map(({ key, label, icon: Icon }) => (
          <button
            type="button"
            className={`nav-item ${activePage === key ? "active" : ""}`}
            key={key}
            title={collapsed ? label : ""}
            onClick={() => setActivePage(key)}
          >
            <Icon size={18} />
            {!collapsed && <span>{label}</span>}
          </button>
        ))}
      </nav>
    </aside>
  );
}
