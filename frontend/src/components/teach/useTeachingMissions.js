import { useEffect, useState } from "react";
import { workspaceRequest } from "../../services/workspaceApi";

export function useTeachingMissions(domainId) {
  const [selected, setSelected] = useState(() => {
    try { return JSON.parse(sessionStorage.getItem("sentinel.teachingMission") || "null"); }
    catch { return null; }
  });
  const [revision, setRevision] = useState(0);
  const [resource, setResource] = useState({ data: null, error: null, key: null });
  const selectedId = selected?.domainId === domainId ? selected.id : null;
  const key = `${domainId}:${selectedId}:${revision}`;
  useEffect(() => {
    const controller = new AbortController();
    let timer;
    async function load() {
      try {
        const path = `/teach/missions?organization_id=default&domain_id=${encodeURIComponent(domainId)}&limit=20`;
        const [missions, selectedMission] = await Promise.all([
          workspaceRequest(path, { signal: controller.signal }),
          selectedId ? workspaceRequest(`/teach/missions/${encodeURIComponent(selectedId)}?organization_id=default`, { signal: controller.signal }) : Promise.resolve(null),
        ]);
        if (controller.signal.aborted) return;
        const mission = selectedMission ?? missions.find((item) => ["queued", "running"].includes(item.status)) ?? missions[0] ?? null;
        setResource({ data: { missions, mission }, error: null, key });
        if ([mission, ...missions].some((item) => item && ["queued", "running"].includes(item.status))) timer = setTimeout(load, 2000);
      } catch (error) {
        if (!controller.signal.aborted) setResource({ data: null, error: error.message, key });
      }
    }
    load();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [domainId, selectedId, key]);
  return {
    data: resource.key === key ? resource.data : null,
    error: resource.key === key ? resource.error : null,
    loading: resource.key !== key,
    refresh: () => setRevision((value) => value + 1),
    select: (mission) => {
      const selection = { id: mission.id, domainId };
      sessionStorage.setItem("sentinel.teachingMission", JSON.stringify(selection));
      setSelected(selection);
      setRevision((value) => value + 1);
    },
  };
}
