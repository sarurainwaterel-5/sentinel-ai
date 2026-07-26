const API_BASE_URL = "http://127.0.0.1:8000";

export async function recallKnowledge({
  question,
  domainId,
  topic = null,
  organizationId = "default",
  limit = 5,
  scoreThreshold = 0.45,
}) {
  if (!question?.trim()) {
    throw new Error("A recall question is required.");
  }

  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: question.trim(),
      module: domainId === "all" ? null : domainId,
      topic,
      organization_id: organizationId,
      limit,
      score_threshold: scoreThreshold,
    }),
  });

  let result;

  try {
    result = await response.json();
  } catch {
    result = null;
  }

  if (!response.ok) {
    const message =
      result?.detail ??
      result?.message ??
      "Sentinel could not recall knowledge.";

    throw new Error(message);
  }

  return result;
}
