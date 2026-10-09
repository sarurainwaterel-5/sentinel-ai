import { useEffect, useState } from "react";
import { workspaceRequest } from "../../services/workspaceApi";

export function useWorkspaceData(path) {
  const [result, setResult] = useState({
    data: null,
    error: null,
    loadedKey: null,
  });
  const [revision, setRevision] = useState(0);
  const key = `${path}:${revision}`;
  useEffect(() => {
    const controller = new AbortController();
    workspaceRequest(path, { signal: controller.signal }).then(
      (data) => {
        if (!controller.signal.aborted)
          setResult({ data, error: null, loadedKey: key });
      },
      (error) => {
        if (!controller.signal.aborted)
          setResult({ data: null, error: error.message, loadedKey: key });
      },
    );
    return () => controller.abort();
  }, [path, key]);
  return {
    data: result.loadedKey === key ? result.data : null,
    error: result.loadedKey === key ? result.error : null,
    loading: result.loadedKey !== key,
    refresh: () => setRevision((value) => value + 1),
  };
}
