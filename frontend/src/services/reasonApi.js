import { API_BASE_URL } from "./apiConfig";


export async function reasonAbout({
  question,
  workspace = "reason",
  module = null,
  topic = null,
  organizationId = "default",
  limit = 5,
  scoreThreshold = 0.45,
  missionId = null,
  sessionId = null,
  signal,
}) {
  let response;
  try { response = await fetch(
    `${API_BASE_URL}/cognition/reason`,
    {
      method: "POST",
      signal,
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        question,
        workspace,
        module,
        topic,
        organization_id: organizationId,
        limit,
        score_threshold: scoreThreshold,
        mission_id: missionId,
        session_id: sessionId,
      }),
    }
  ); } catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("Sentinel could not reach the reasoning service. Check Systems and retry.", { cause: error });
  }

  if (!response.ok) {
    let detail = null;

    try {
      const payload = await response.json();
      detail = payload?.detail;
    } catch {
      // Preserve the stable fallback below.
    }

    throw new Error(
      typeof detail === "string"
        ? detail
        : "Sentinel could not complete reasoning."
    );
  }

  const result = await response.json().catch(() => null);
  if (!result?.reasoning || !result.reasoning.evidence || !result.reasoning.confidence || !result.coherence) {
    throw new Error("The reasoning service returned an incomplete report. Check Systems and retry.");
  }
  return result;
}
