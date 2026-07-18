import { useState } from "react";
import Layout from "./components/layout/Layout";
import KnowledgeDashboard from "./pages/KnowledgeDashboard";
import TeachSentinel from "./pages/TeachSentinel";
import Identity from "./pages/Identity";
import Bridge from "./pages/Bridge";
import "./App.css";
import Domains from "./pages/Domains";


const Placeholder = ({ title }) => (
  <div className="panel">
    <p className="eyebrow">Workspace</p>
    <h2>{title}</h2>
    <p className="muted">This workspace is currently under construction.</p>
  </div>
);

function App() {
  const [activePage, setActivePage] = useState("bridge");

  const pages = {
  bridge: <Bridge />,
  teach: <TeachSentinel />,
  identity: <Identity />,
 domains: <Domains />,
  recall: <Placeholder title="Recall" />,
  reason: <Placeholder title="Reason" />,
  intelligence: <Placeholder title="Intelligence" />,
  governance: <Placeholder title="Governance" />,
  systems: <Placeholder title="Systems" />,
};

  return (
    <Layout activePage={activePage} setActivePage={setActivePage}>
      {pages[activePage]}
    </Layout>
  );
}

export default App;
