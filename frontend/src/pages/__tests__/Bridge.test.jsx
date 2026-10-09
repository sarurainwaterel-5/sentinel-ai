import { fireEvent, render, screen, within } from "@testing-library/react";
import { vi } from "vitest";
import Bridge from "../Bridge";
import { workspaceRequest } from "../../services/workspaceApi";
vi.mock("../../services/workspaceApi", () => ({ workspaceRequest: vi.fn() }));
vi.mock("../../context/useDomain", () => ({ useDomain: () => ({ activeDomain: { id: "trading", name: "Trading" } }) }));
const summary = { health: { overall: "Ready", observed_at: "2026-10-09T00:00:00Z", services: { Memory: "ready" }, model_features_configured: true, observations: ["Independent evaluation outstanding"] }, canon: { health: "healthy", documents: 12, layers: 3, warnings: [] }, graph: { nodes: 14, edges: 22 } };
const respond = async (path) => path === "/bridge/summary" ? summary : path.startsWith("/domains/memory") ? { domains: { trading: { indexed_documents: 4, archived_documents: 1, indexed_chunks: 119 }, engineering: { indexed_documents: 8, archived_documents: 0, indexed_chunks: 200 } } } : [];
beforeEach(() => { vi.clearAllMocks(); workspaceRequest.mockImplementation(respond); });
test("observes scoped catalog counts without inventing understanding or activity", async () => {
  render(<Bridge />);
  await screen.findByText("Storage ready");
  const context = screen.getByRole("heading", { name: "Trading" }).closest("section");
  expect(within(context).getByText("119")).toBeInTheDocument();
  expect(within(context).queryByText("200")).not.toBeInTheDocument();
  expect(screen.getByText(/No Learning Events recorded yet/)).toBeInTheDocument();
  expect(screen.queryByText(/System Coherent|understands itself/)).not.toBeInTheDocument();
});
test("keeps navigation and other observations available when memory fails; retry recovers", async () => {
  workspaceRequest.mockImplementation(async (path) => { if (path.startsWith("/domains/memory")) throw Error("Catalog unavailable"); return respond(path); });
  const navigate = vi.fn(); render(<Bridge onNavigate={navigate} />);
  await screen.findByText("Catalog unavailable");
  expect(screen.getByText("Storage ready")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Recall" })); expect(navigate).toHaveBeenCalledWith("recall");
  workspaceRequest.mockImplementation(respond);
  fireEvent.click(screen.getByRole("button", { name: "Retry knowledge counts" }));
  await screen.findByText("119");
});
test("refreshes all observations and displays factual learning activity", async () => {
  workspaceRequest.mockImplementation(async (path) => path.startsWith("/intelligence/learning-events") ? [{ learning_event_id: "event-1", source: "New PDF", learned_at: "2026-10-09T00:00:00Z", domain_ids: ["trading"], summary: "Recorded 3 memory chunks." }] : respond(path));
  render(<Bridge />); await screen.findByText("New PDF");
  fireEvent.click(screen.getByRole("button", { name: "Refresh observations" }));
  await screen.findByText("Recorded 3 memory chunks.");
  expect(workspaceRequest.mock.calls.filter(([path]) => path === "/bridge/summary")).toHaveLength(2);
});
