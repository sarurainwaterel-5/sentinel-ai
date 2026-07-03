const API_BASE_URL = "http://127.0.0.1:8000";

export async function getKnowledgeDashboard() {
  const response = await fetch(`${API_BASE_URL}/knowledge/dashboard`);

  if (!response.ok) {
    throw new Error("Failed to fetch knowledge dashboard");
  }

  return response.json();
}
