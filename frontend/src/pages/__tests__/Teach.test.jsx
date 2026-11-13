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
  await screen.findByText(/PDF · Up to/);
  const file = new File(["%PDF-test"], "source.pdf", { type: "application/pdf" });
  fireEvent.change(screen.getByLabelText("Files"), { target: { files: [file] } });
  expect(screen.getByRole("button", { name: "Begin Teaching" })).toBeDisabled();
  context.activeDomain = { id: "trading", name: "Trading" }; rerender(<TeachSentinel />);
  fireEvent.change(screen.getByLabelText("Topic"), { target: { value: "price action" } });
  fireEvent.change(screen.getByLabelText("Teaching context"), { target: { value: "Trusted manual" } });
  fireEvent.click(screen.getByRole("button", { name: "Begin Teaching" }));
  await screen.findByText(/1 mission accepted/);
  expect(submitTeachingMission).toHaveBeenCalledWith({ file, domainId: "trading", topic: "price action", description: "Trusted manual" });
  await screen.findByText("Acquisition recorded as a Learning Event.");
});
test("rejects unsuitable files and clears a previous valid selection", async () => {
  render(<TeachSentinel />); await screen.findByText(/PDF · Up to/);
  fireEvent.change(screen.getByLabelText("Files"), { target: { files: [new File(["%PDF"], "good.pdf")] } });
  fireEvent.change(screen.getByLabelText("Files"), { target: { files: [new File(["text"], "bad.txt")] } });
  expect(screen.getByText(/bad.txt · invalid: Unsupported file format/)).toBeInTheDocument();
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
  expect(screen.getByLabelText("Files")).toBeEnabled();
  workspaceRequest.mockImplementation(respond);
  fireEvent.click(screen.getByRole("button", { name: "Retry teaching missions" }));
  await screen.findByText("No teaching missions recorded in this context yet.");
});
test("duplicate does not report unobserved ingestion stages as complete", async () => {
  workspaceRequest.mockImplementation(async (path) => path === "/teach/config" ? respond(path) : [{ ...mission, status: "duplicate", result: { existing_document: { module: "engineering" } } }]);
  render(<TeachSentinel />);
  await screen.findByText(/This source is already cataloged in engineering/);
  expect(screen.getAllByText("Not run").length).toBeGreaterThan(0);
  expect(screen.queryByRole("button", { name: "Open Recall" })).not.toBeInTheDocument();
});

test("uploads a mixed folder sequentially and retries only failed files", async () => {
  workspaceRequest.mockImplementation(async (path) => path === "/teach/config" ? { max_upload_bytes: 1000, supported_formats: ["pdf", "png", "mp4"], allow_other_files: true, max_batch_files: 100 } : []);
  submitTeachingMission.mockResolvedValueOnce({ ...mission, status: "queued" }).mockRejectedValueOnce(Error("Queue full (429)"));
  render(<TeachSentinel />);
  await screen.findByText(/PDF, PNG, MP4/);
  const image = new File(["image"], "image.png");
  const video = new File(["video"], "video.mp4");
  Object.defineProperty(image, "webkitRelativePath", { value: "folder/image.png" });
  Object.defineProperty(video, "webkitRelativePath", { value: "folder/video.mp4" });
  fireEvent.change(screen.getByLabelText("Choose folder"), { target: { files: [image, video] } });
  fireEvent.click(screen.getByRole("button", { name: "Begin Teaching" }));
  await screen.findByText(/folder\/video.mp4 · failed/);
  expect(submitTeachingMission.mock.calls[0][0].relativePath).toBe("folder/image.png");
  submitTeachingMission.mockResolvedValueOnce({ ...mission, id: "retry", status: "queued" });
  fireEvent.click(screen.getByRole("button", { name: "Begin Teaching" }));
  await waitFor(() => expect(submitTeachingMission).toHaveBeenCalledTimes(3));
  expect(submitTeachingMission.mock.calls[2][0].file).toBe(video);
});

test("validates empty, oversized, unsafe paths and batch bounds", async () => {
  workspaceRequest.mockImplementation(async (path) => path === "/teach/config" ? { max_upload_bytes: 10, supported_formats: ["png"], max_batch_files: 3 } : []);
  render(<TeachSentinel />); await screen.findByText(/PNG · Up to/);
  const unsafe = new File(["ok"], "a.png"); Object.defineProperty(unsafe, "webkitRelativePath", { value: "../a.png" });
  fireEvent.change(screen.getByLabelText("Files"), { target: { files: [new File([], "empty.png"), new File(["oversized-image"], "large.png"), unsafe] } });
  expect(screen.getByText(/Empty file/)).toBeInTheDocument();
  expect(screen.getByText(/exceeds the upload size/)).toBeInTheDocument();
  expect(screen.getByText(/Invalid folder-relative/)).toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Files"), { target: { files: Array(4).fill(unsafe) } });
  expect(screen.getByText(/at most 3 files per batch/)).toBeInTheDocument();
  expect(submitTeachingMission).not.toHaveBeenCalled();
});

test("stored sources never claim indexed memory", async () => {
  workspaceRequest.mockImplementation(async (path) => path === "/teach/config" ? respond(path) : [{ ...mission, status: "stored", result: { message: "Stored only" } }]);
  render(<TeachSentinel />);
  await screen.findByText(/Source preserved only/);
  expect(screen.queryByText("Memory chunks")).not.toBeInTheDocument();
  expect(screen.queryByRole("button", { name: "Open Recall" })).not.toBeInTheDocument();
});

test("locks selection during upload and does not retry ambiguous submissions", async () => {
  let rejectUpload;
  submitTeachingMission.mockImplementation(() => new Promise((resolve, reject) => { rejectUpload = reject; }));
  render(<TeachSentinel />); await screen.findByText(/PDF · Up to/);
  fireEvent.change(screen.getByLabelText("Files"), { target: { files: [new File(["pdf"], "a.pdf")] } });
  fireEvent.click(screen.getByRole("button", { name: "Begin Teaching" }));
  expect(screen.getByLabelText("Files")).toBeDisabled();
  expect(screen.getByLabelText("Choose folder")).toBeDisabled();
  expect(screen.getByLabelText("Topic")).toBeDisabled();
  const error = Error("Submission uncertain"); error.submissionUnconfirmed = true;
  rejectUpload(error);
  await screen.findByText(/a.pdf · unconfirmed/);
  expect(screen.getByRole("button", { name: "Begin Teaching" })).toBeDisabled();
  expect(screen.getByLabelText("Files")).toBeEnabled();
});

test("dropped directories direct users to the bounded folder picker", async () => {
  render(<TeachSentinel />); await screen.findByText(/PDF · Up to/);
  fireEvent.drop(screen.getByText("Teach Sentinel").closest("section"), { dataTransfer: { files: [], items: [{ webkitGetAsEntry: () => ({ isDirectory: true }) }] } });
  expect(screen.getByText(/For folders, use Choose folder/)).toBeInTheDocument();
});

test("reports local speech availability and observed transcription progress", async () => {
  workspaceRequest.mockImplementation(async (path) => path === "/teach/config" ? { max_upload_bytes: 1024**3, supported_formats: ["mp4"], audio_transcription_available: true } : [{ ...mission, filename: "lesson.mp4", status: "running", stage: "transcribing", events: [{ stage: "transcribing", at: "2026-11-12T00:00:00Z" }], result: null }]);
  render(<TeachSentinel />);
  await screen.findByText(/Video speech is transcribed locally with timestamps/);
  expect(screen.getByText("Transcribe video speech")).toBeInTheDocument();
  expect(screen.getByText(/In progress/)).toBeInTheDocument();
});

test("shows incomplete audio processing without claiming a transcript", async () => {
  workspaceRequest.mockImplementation(async (path) => path === "/teach/config" ? respond(path) : [{ ...mission, filename: "lesson.mp4", result: { ...mission.result, warnings: ["audio_not_transcribed", "local_speech_transcription_failed"] } }]);
  render(<TeachSentinel />);
  await screen.findByText("audio not transcribed");
  expect(screen.getByText("local speech transcription failed")).toBeInTheDocument();
});
