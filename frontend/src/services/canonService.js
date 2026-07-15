const API_BASE = "http://127.0.0.1:8000";

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
