import TeachHero from "../components/teach/TeachHero";
import TeachDropZone from "../components/teach/TeachDropZone";
import MissionTimeline from "../components/teach/MissionTimeline";
import KnowledgeSummary from "../components/teach/KnowledgeSummary";
import RecentMissions from "../components/teach/RecentMissions";

export default function TeachSentinel() {
  return (
    <div className="page">
      <TeachHero />
      <TeachDropZone />
      <MissionTimeline />
      <KnowledgeSummary />
      <RecentMissions />
    </div>
  );
}
