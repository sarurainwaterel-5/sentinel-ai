const API = "http://127.0.0.1:8000";

export async function getBridgeSummary() {
  const response = await fetch(`${API}/bridge/summary`);

  if (!response.ok) {
    throw new Error("Failed to load Bridge summary.");
  }

  return response.json();
}
