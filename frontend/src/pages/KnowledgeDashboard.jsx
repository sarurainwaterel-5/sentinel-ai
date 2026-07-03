import { useEffect, useState } from "react";
import { getKnowledgeDashboard } from "../services/knowledgeApi";
import OverviewCards from "../components/dashboard/OverviewCards";
import RecentDocuments from "../components/dashboard/RecentDocuments";
import KnowledgeDomains from "../components/dashboard/KnowledgeDomains";

export default function KnowledgeDashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getKnowledgeDashboard()
      .then(setDashboard)
      .catch((err) => setError(err.message));
  }, []);

  if (error) return <div className="page"><p>{error}</p></div>;
  if (!dashboard) return <div className="page"><p>Loading SentinelAI...</p></div>;

  return (
    <div className="page">
      <OverviewCards overview={dashboard.overview} />
      <KnowledgeDomains domains={dashboard.knowledge_domains} />
      <RecentDocuments documents={dashboard.recent_documents} />
    </div>
  );
}
