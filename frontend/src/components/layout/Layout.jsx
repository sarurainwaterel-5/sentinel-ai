import { useState } from "react";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function Layout({ children, activePage, setActivePage }) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <div className={`app-shell ${collapsed ? "collapsed" : ""}`}>
      <Sidebar
        collapsed={collapsed}
        onToggle={() => setCollapsed(!collapsed)}
        activePage={activePage}
        setActivePage={setActivePage}
      />

      <main className="main-panel">
        <TopBar activePage={activePage} />
        {children}
      </main>
    </div>
  );
}
