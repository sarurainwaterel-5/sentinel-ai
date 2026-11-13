import { afterEach, expect, test, vi } from "vitest";
import { submitTeachingMission } from "../knowledgeApi";
afterEach(() => vi.unstubAllGlobals());
test("optional relative metadata is omitted for existing single-file calls", async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ id: "one" }) }); vi.stubGlobal("fetch", fetch);
  const file = new File(["source"], "a.txt");
  await submitTeachingMission({ file, domainId: "trading" });
  expect(fetch.mock.calls[0][1].body.has("relative_path")).toBe(false);
  await submitTeachingMission({ file, domainId: "trading", relativePath: "folder/a.txt" });
  expect(fetch.mock.calls[1][1].body.get("relative_path")).toBe("folder/a.txt");
});
test("queue errors remain retryable while ambiguous transport errors require review", async () => {
  const fetch = vi.fn().mockResolvedValue({ ok: false, status: 429, json: async () => ({ detail: "Queue full" }) }); vi.stubGlobal("fetch", fetch);
  await expect(submitTeachingMission({ file: new File(["x"], "x.txt"), domainId: "trading" })).rejects.toMatchObject({ message: "Queue full" });
  fetch.mockRejectedValueOnce(Error("network"));
  await expect(submitTeachingMission({ file: new File(["x"], "x.txt"), domainId: "trading" })).rejects.toMatchObject({ submissionUnconfirmed: true });
});
