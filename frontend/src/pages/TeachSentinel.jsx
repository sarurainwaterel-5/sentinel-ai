import TeachDropZone from "../components/teach/TeachDropZone";
import MissionTimeline from "../components/teach/MissionTimeline";
import KnowledgeSummary from "../components/teach/KnowledgeSummary";
import RecentMissions from "../components/teach/RecentMissions";
import { useTeachingMissions } from "../components/teach/useTeachingMissions";
import { useDomain } from "../context/useDomain";
import { ResourceState, WorkspaceHeader } from "../components/workspaces/WorkspaceParts";

export default function TeachSentinel({ onNavigate }) {
  const { activeDomain } = useDomain();
  const missions = useTeachingMissions(activeDomain?.id ?? "all");
  return <div className="page workspace-page">
    <WorkspaceHeader title="Preserve trusted evidence in memory" description="Teach through text-based PDFs. Observe actual ingestion progress and inspect recorded source provenance; acquisition does not establish understanding." onRefresh={missions.refresh} loading={missions.loading} />
    <TeachDropZone onAccepted={missions.select} />
    <ResourceState resource={missions} label="teaching missions">
      <MissionTimeline mission={missions.data?.mission} />
      <KnowledgeSummary mission={missions.data?.mission} onNavigate={onNavigate} />
      <RecentMissions missions={missions.data?.missions} onSelect={missions.select} />
    </ResourceState>
  </div>;
}
