import { useState } from "react";
import Layout from "./components/layout/Layout";
import TeachSentinel from "./pages/TeachSentinel";
import Identity from "./pages/Identity";
import Bridge from "./pages/Bridge";
import "./App.css";
import Domains from "./pages/Domains";
import Recall from "./pages/Recall";
import Reason from "./pages/Reason";
import Intelligence from "./pages/Intelligence";
import Governance from "./pages/Governance";
import Systems from "./pages/Systems";
import "./styles/workspaces.css";

function App() {
  const [activePage, setActivePage] = useState("bridge");

  const pages = {
    bridge: <Bridge onNavigate={setActivePage} />,
    teach: <TeachSentinel />,
    identity: <Identity onNavigate={setActivePage} />,
    domains: <Domains onNavigate={setActivePage} />,
    recall: <Recall />,
    reason: <Reason />,
    intelligence: <Intelligence onTeach={() => setActivePage("teach")} />,
    governance: <Governance onTeach={() => setActivePage("teach")} />,
    systems: <Systems />,
  };

  return (
    <Layout activePage={activePage} setActivePage={setActivePage}>
      {pages[activePage]}
    </Layout>
  );
}

export default App;
