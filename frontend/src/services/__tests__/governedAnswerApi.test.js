import { vi } from "vitest";
import { getGovernedAnswerReadiness, requestGovernedAnswer } from "../governedAnswerApi";
afterEach(() => vi.unstubAllGlobals());
const readiness = { schema_version: "21.v1", status: "disabled", enabled: false, semantic_grounding_verified: false, proposition_to_inference: "closed", blockers: ["release_disabled"] };
const envelope = { schema_version: "21.v1", outcome: "disabled", answer_text: null, claims: [], evidence: [], question: "Q", scope: { organization_id: "default", module: "engineering", topic: null }, validation: { release_status: "disabled", semantic_grounding_verified: false, rejection_reasons: ["release_disabled"] } };
function response(status, payload) { vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ status, ok: status < 400, json: async () => payload })); }
test("readiness cannot silently enable production", async () => {
  response(200, readiness); expect((await getGovernedAnswerReadiness()).enabled).toBe(false);
  response(200, { ...readiness, enabled: true }); await expect(getGovernedAnswerReadiness()).rejects.toThrow("Unrecognized");
});
test("expected 503 preserves its disabled structured report and scope", async () => {
  response(503, envelope); expect(await requestGovernedAnswer({ question: "Q", module: "engineering" })).toEqual(envelope);
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/cognition/answer"), expect.objectContaining({ method: "POST" }));
});
test.each([200, 403, 500])("unexpected status %s cannot become an answer", async status => {
  response(status, envelope); await expect(requestGovernedAnswer({ question: "Q" })).rejects.toThrow();
});
test("mismatched scope is withheld", async () => {
  response(503, envelope); await expect(requestGovernedAnswer({ question: "Q", module: "trading" })).rejects.toThrow("scope");
});
test("malformed 503 cannot become an answer", async () => {
  response(503, { detail: "unavailable" }); await expect(requestGovernedAnswer({ question: "Q" })).rejects.toThrow("Unrecognized");
});
test("abort preserves cancellation and network errors remain bounded", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new DOMException("Aborted", "AbortError")));
  await expect(getGovernedAnswerReadiness()).rejects.toMatchObject({ name: "AbortError" });
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(Error("private internal payload")));
  await expect(getGovernedAnswerReadiness()).rejects.toThrow("could not be reached");
});
