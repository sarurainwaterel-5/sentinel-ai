import { API_BASE_URL } from "./apiConfig";

export async function workspaceRequest(
  path,
  { body, method = "GET", signal } = {},
) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      method,
      signal,
      ...(body
        ? {
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
          }
        : {}),
    });
  } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error(
      "Sentinel could not reach this service. Check Systems, then retry.",
      { cause: error },
    );
  }
  let payload;
  try {
    payload = await response.json();
  } catch {
    payload = null;
  }
  if (!response.ok) {
    const detail = payload?.detail;
    throw new Error(
      typeof detail === "string"
        ? detail
        : `Sentinel returned HTTP ${response.status}. Retry after checking Systems.`,
    );
  }
  if (payload === null)
    throw new Error("Sentinel returned an unreadable response.");
  if (payload.status === "not_found")
    throw new Error(
      "This document is no longer available. Refresh the catalog.",
    );
  return payload;
}
