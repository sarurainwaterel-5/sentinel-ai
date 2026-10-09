import { API_BASE_URL } from "./apiConfig";

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
      `Sentinel could not learn this document. ` +
        `The teaching service returned HTTP ${response.status}.`;

    throw new Error(message);
  }

  return result;
}

export async function submitTeachingMission({ file, domainId, topic = "general", description = "" }) {
  const form = new FormData();
  form.append("file", file);
  form.append("module", domainId);
  form.append("topic", topic || "general");
  form.append("description", description);
  form.append("organization_id", "default");
  let response;
  try { response = await fetch(`${API_BASE_URL}/teach/missions`, { method: "POST", body: form }); }
  catch { throw new Error("Submission could not be confirmed. Refresh mission history before retrying; Sentinel may already have received the PDF."); }
  const payload = await response.json().catch(() => null);
  if (!response.ok) throw new Error(typeof payload?.detail === "string" ? payload.detail : `Teaching submission returned HTTP ${response.status}. Check Systems and retry.`);
  if (!payload?.id) throw new Error("Submission could not be confirmed. Refresh mission history before retrying.");
  return payload;
}
