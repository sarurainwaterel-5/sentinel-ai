import { UploadCloud } from "lucide-react";

export default function TopBar() {
  return (
    <header className="topbar">
      <div>
        <p className="eyebrow">Bridge Online</p>
        <h1>Bridge</h1>
        <p className="subtitle">Operational intelligence overview</p>
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
