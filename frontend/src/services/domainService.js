import { API_BASE_URL as API } from "./apiConfig";

export async function getDomainModel() {
  const response = await fetch(`${API}/domains`);

  if (!response.ok) {
    throw new Error("Failed to load Domain Model.");
  }

  return response.json();
}

export async function getDomain(domainId) {
  const response = await fetch(`${API}/domains/${domainId}`);

  if (!response.ok) {
    throw new Error(`Failed to load domain '${domainId}'.`);
  }

  return response.json();
}
