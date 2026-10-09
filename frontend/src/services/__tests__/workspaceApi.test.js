import { vi } from "vitest";
import { workspaceRequest } from "../workspaceApi";

afterEach(() => vi.unstubAllGlobals());

test("preserves a bounded API error instead of displaying a false success", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({
        ok: false,
        status: 503,
        json: async () => ({ detail: "Memory is unavailable" }),
      }),
  );
  await expect(workspaceRequest("/systems/status")).rejects.toThrow(
    "Memory is unavailable",
  );
});

test("an HTTP success with a missing document is still a failed lifecycle change", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({
        ok: true,
        json: async () => ({ status: "not_found" }),
      }),
  );
  await expect(
    workspaceRequest("/knowledge/missing/archive", { method: "PUT" }),
  ).rejects.toThrow("no longer available");
});

test("network failures provide an operator recovery path", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
  );
  await expect(workspaceRequest("/systems/status")).rejects.toThrow(
    "Check Systems, then retry",
  );
});
