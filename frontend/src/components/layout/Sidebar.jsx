import {
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
  { label: "Bridge", icon: Radar },
  { label: "Knowledge", icon: BookOpen },
  { label: "Sentinel", icon: Bot },
  { label: "Recall", icon: Search },
  { label: "Intelligence", icon: BarChart3 },
  { label: "Governance", icon: Shield },
  { label: "Systems", icon: Settings },
];

export default function Sidebar({ collapsed, onToggle }) {
  const ToggleIcon = collapsed ? PanelLeftOpen : PanelLeftClose;

  return (
    <aside className="sidebar">
      <div className="brand">
        <Brain size={26} />

        {!collapsed && (
          <div>
            <h2>SentinelAI</h2>
            <small>Knowledge OS</small>
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
        {navItems.map(({ label, icon: Icon }) => (
          <button
            type="button"
            className="nav-item"
            key={label}
            title={collapsed ? label : ""}
          >
            <Icon size={18} />
            {!collapsed && <span>{label}</span>}
          </button>
        ))}
      </nav>
    </aside>
  );
}
