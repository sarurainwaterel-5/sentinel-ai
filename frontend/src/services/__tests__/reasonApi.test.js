import { vi } from "vitest";
import { reasonAbout } from "../reasonApi";
afterEach(() => vi.unstubAllGlobals());
test("transport failures are actionable and bounded", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(Error("internal connection failure")));
  await expect(reasonAbout({ question: "Inspect evidence" })).rejects.toThrow("Check Systems and retry");
});
test("aborted waiting is preserved instead of being relabeled a service failure", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new DOMException("Aborted", "AbortError")));
  await expect(reasonAbout({ question: "Inspect evidence" })).rejects.toMatchObject({ name: "AbortError" });
});
test("an unreadable successful response cannot become a reasoning report", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: true, json: async () => ({ reasoning: {} }) }));
  await expect(reasonAbout({ question: "Inspect evidence" })).rejects.toThrow("incomplete report");
});
test("bounded provider failures retain their operator-facing explanation", async () => {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue({ ok: false, json: async () => ({ detail: "Model credentials rejected. Update settings." }) }));
  await expect(reasonAbout({ question: "Inspect evidence" })).rejects.toThrow("Model credentials rejected");
});
