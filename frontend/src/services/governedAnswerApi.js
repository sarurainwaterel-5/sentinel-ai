import { API_BASE_URL } from "./apiConfig";

export function validateReadiness(payload) {
  if (payload?.schema_version !== "21.v1" || payload.status !== "disabled" || payload.enabled !== false ||
      payload.semantic_grounding_verified !== false || payload.proposition_to_inference !== "closed" ||
      !Array.isArray(payload.blockers) || !payload.blockers.every(value => typeof value === "string")) {
    throw new Error("Unrecognized governed answer readiness. Answering remains disabled.");
  }
  return payload;
}

export function validateDisabledAnswer(payload) {
  if (payload?.schema_version !== "21.v1" || payload.outcome !== "disabled" || payload.answer_text !== null ||
      !Array.isArray(payload.claims) || payload.claims.length || !Array.isArray(payload.evidence) || payload.evidence.length ||
      payload.validation?.release_status !== "disabled" || payload.validation.semantic_grounding_verified !== false ||
      !Array.isArray(payload.validation.rejection_reasons) || !payload.validation.rejection_reasons.every(value => typeof value === "string") ||
      typeof payload.question !== "string" || typeof payload.scope?.organization_id !== "string") {
    throw new Error("Unrecognized governed answer response. No answer was accepted.");
  }
  return payload;
}

async function request(path, options) {
  try { return await fetch(`${API_BASE_URL}${path}`, options); }
  catch (error) {
    if (error.name === "AbortError") throw error;
    throw new Error("Governed answer service could not be reached. Answering remains disabled.", { cause: error });
  }
}

export async function getGovernedAnswerReadiness(signal) {
  const response = await request("/cognition/answer/readiness", { signal });
  if (!response.ok) throw new Error("Readiness is unavailable. Answering remains disabled.");
  return validateReadiness(await response.json().catch(() => null));
}

export async function requestGovernedAnswer(body, signal) {
  const response = await request("/cognition/answer", { method: "POST", signal,
    headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  const payload = await response.json().catch(() => null);
  // Expected disabled envelope is preserved even though HTTP status is 503.
  if (response.status === 503) {
    const result = validateDisabledAnswer(payload);
    if (result.question !== body.question.trim() || result.scope.organization_id !== (body.organization_id ?? "default") ||
        (result.scope.module ?? null) !== (body.module ?? null) || (result.scope.topic ?? null) !== (body.topic ?? null)) {
      throw new Error("Governed answer scope does not match this request.");
    }
    return result;
  }
  throw new Error(response.status === 403 ? "Organization is outside the local operator scope." :
    "Governed answering remains disabled; unexpected response was withheld.");
}
