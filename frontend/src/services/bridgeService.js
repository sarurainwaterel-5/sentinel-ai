import { API_BASE_URL as API } from "./apiConfig";

export async function getBridgeSummary() {
  const response = await fetch(`${API}/bridge/summary`);

  if (!response.ok) {
    throw new Error("Failed to load Bridge summary.");
  }

  return response.json();
}
