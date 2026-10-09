import { API_BASE_URL as API_BASE } from "./apiConfig";

export async function getCanonHealth() {
    const response = await fetch(`${API_BASE}/canon/health`);

    if (!response.ok) {
        throw new Error("Unable to load Core Principle Health.");
    }

    return response.json();
}

export async function getCanonManifest() {
    const response = await fetch(`${API_BASE}/canon/manifest`);

    if (!response.ok) {
        throw new Error("Unable to load Core Principle Manifest.");
    }

    return response.json();
}
