import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import TeachSentinel from "../TeachSentinel";
import { workspaceRequest } from "../../services/workspaceApi";
import { submitTeachingMission } from "../../services/knowledgeApi";
const context = vi.hoisted(() => ({ activeDomain: { id: "trading", name: "Trading" } }));
vi.mock("../../context/useDomain", () => ({ useDomain: () => context }));
vi.mock("../../services/workspaceApi", () => ({ workspaceRequest: vi.fn() }));
vi.mock("../../services/knowledgeApi", () => ({ submitTeachingMission: vi.fn() }));
const mission = { id: "mission-1", domain_id: "trading", filename: "source.pdf", status: "completed", stage: "finished", created_at: "2026-10-09T00:00:00Z", events: [{ stage: "received", at: "2026-10-09T00:00:00Z" }], result: { characters: 100, chunks: 3, module: "trading", document_id: "doc", file_hash: "hash", learning_event_id: "event", embedding_model: "model" } };
const respond = async (path) => path === "/teach/config" ? { max_upload_bytes: 20 * 1024 * 1024 } : path.includes("/missions/") ? mission : [];
beforeEach(() => { vi.clearAllMocks(); sessionStorage.clear(); context.activeDomain = { id: "trading", name: "Trading" }; workspaceRequest.mockImplementation(respond); submitTeachingMission.mockResolvedValue({ ...mission, status: "queued" }); });
test("validates input and domain before submitting a background mission", async () => {
  context.activeDomain = { id: "all", name: "All Domains" };
  const { rerender } = render(<TeachSentinel />);
  await screen.findByText(/PDF only/);
  const file = new File(["%PDF-test"], "source.pdf", { type: "application/pdf" });
  fireEvent.change(screen.getByLabelText("PDF document"), { target: { files: [file] } });
  expect(screen.getByRole("button", { name: "Begin Teaching" })).toBeDisabled();
  context.activeDomain = { id: "trading", name: "Trading" }; rerender(<TeachSentinel />);
  fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "price action" } });
  fireEvent.change(screen.getByLabelText("Teaching context"), { target: { value: "Trusted manual" } });
  fireEvent.click(screen.getByRole("button", { name: "Begin Teaching" }));
  await screen.findByText(/Mission accepted/);
  expect(submitTeachingMission).toHaveBeenCalledWith({ file, domainId: "trading", topic: "price action", description: "Trusted manual" });
  await screen.findByText("Acquisition recorded as a Learning Event.");
});
test("rejects unsuitable files and clears a previous valid selection", async () => {
  render(<TeachSentinel />); await screen.findByText(/PDF only/);
  fireEvent.change(screen.getByLabelText("PDF document"), { target: { files: [new File(["%PDF"], "good.pdf")] } });
  fireEvent.change(screen.getByLabelText("PDF document"), { target: { files: [new File(["text"], "bad.txt")] } });
  expect(screen.getByText("Only PDF documents are supported.")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Begin Teaching" })).toBeDisabled();
});
test("reconnects to recorded active progress and stops at the completed result", async () => {
  let calls = 0;
  workspaceRequest.mockImplementation(async (path) => path === "/teach/config" ? respond(path) : [++calls === 1 ? { ...mission, status: "running", stage: "indexing", result: null } : mission]);
  render(<TeachSentinel />);
  await screen.findByText("running");
  await waitFor(() => expect(screen.getByText("completed")).toBeInTheDocument(), { timeout: 5000 });
  expect(screen.getByText("Memory chunks")).toBeInTheDocument();
  expect(screen.queryByText(/Connecting ideas/)).not.toBeInTheDocument();
});
test("history failure is retryable without blocking the upload controls", async () => {
  workspaceRequest.mockImplementation(async (path) => { if (path === "/teach/config") return respond(path); throw Error("Mission history unavailable"); });
  render(<TeachSentinel />); await screen.findByText("Mission history unavailable");
  expect(screen.getByLabelText("PDF document")).toBeEnabled();
  workspaceRequest.mockImplementation(respond);
  fireEvent.click(screen.getByRole("button", { name: "Retry teaching missions" }));
  await screen.findByText("No teaching missions recorded in this context yet.");
});
test("duplicate does not report unobserved ingestion stages as complete", async () => {
  workspaceRequest.mockImplementation(async (path) => path === "/teach/config" ? respond(path) : [{ ...mission, status: "duplicate", result: { existing_document: { module: "engineering" } } }]);
  render(<TeachSentinel />);
  await screen.findByText(/This PDF is already cataloged in engineering/);
  expect(screen.getAllByText("Not run").length).toBeGreaterThan(0);
  expect(screen.queryByRole("button", { name: "Open Recall" })).not.toBeInTheDocument();
});
