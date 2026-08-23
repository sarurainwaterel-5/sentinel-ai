const API_BASE_URL =
  import.meta.env.VITE_API_URL ??
  "http://127.0.0.1:8000";


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
}) {
  const response = await fetch(
    `${API_BASE_URL}/cognition/reason`,
    {
      method: "POST",
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
  );

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

  return response.json();
}
