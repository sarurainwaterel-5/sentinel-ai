import { useEffect, useState } from "react";
import { getBridgeSummary } from "../services/bridgeService";
import BridgeOverview from "../components/bridge/BridgeOverview";
import PrinciplesCard from "../components/bridge/PrinciplesCard";
import ConnectionsCard from "../components/bridge/ConnectionsCard";
import ReflectionSummaryCard from "../components/bridge/ReflectionSummaryCard";
import OperationalHealth from "../components/bridge/OperationalHealth";

export default function Bridge() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadBridge() {
      try {
        const data = await getBridgeSummary();
        setSummary(data);
      } catch (error) {
        console.error(error);
        setError(error.message);
      }
    }

    loadBridge();
  }, []);

  if (error) {
    return <div className="page">Bridge unavailable: {error}</div>;
  }

  if (!summary) {
    return <div className="page">Loading Bridge...</div>;
  }

  return (
  <div className="page">
    <BridgeOverview />

    <div className="identity-grid">
      <PrinciplesCard canon={summary.canon} />
      <ConnectionsCard graph={summary.graph} />
    </div>

    <ReflectionSummaryCard reflection={summary.reflection} />

    <OperationalHealth health={summary.health} />
  </div>

  );
}
