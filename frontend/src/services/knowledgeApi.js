const API_BASE_URL = "http://127.0.0.1:8000";

export async function getKnowledgeDashboard() {
  const response = await fetch(
    `${API_BASE_URL}/knowledge/dashboard`,
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch knowledge dashboard.",
    );
  }

  return response.json();
}

export async function uploadKnowledge({
  file,
  domainId,
  topic = "general",
  description = "",
  organizationId = "default",
}) {
  if (!file) {
    throw new Error(
      "Knowledge file is required.",
    );
  }

  if (!domainId || domainId === "all") {
    throw new Error(
      "Select one specific domain before teaching Sentinel.",
    );
  }

  const formData = new FormData();

  formData.append("file", file);
  formData.append("module", domainId);
  formData.append("topic", topic || "general");
  formData.append("collection", domainId);
  formData.append("description", description);
  formData.append(
    "organization_id",
    organizationId,
  );

  let response;

  try {
    response = await fetch(
      `${API_BASE_URL}/upload`,
      {
        method: "POST",
        body: formData,
      },
    );
  } catch (error) {
    throw new Error(
      "Sentinel could not reach the teaching service. " +
        "Confirm the backend is running and inspect " +
        "its terminal for an upload error.",
      {
        cause: error,
      },
    );
  }

  let result = null;

  try {
    result = await response.json();
  } catch {
    result = null;
  }

  if (!response.ok) {
    const message =
      result?.detail ??
      result?.message ??
      `Sentinel could not learn this document. ` +
        `The teaching service returned HTTP ${response.status}.`;

    throw new Error(message);
  }

  return result;
}
