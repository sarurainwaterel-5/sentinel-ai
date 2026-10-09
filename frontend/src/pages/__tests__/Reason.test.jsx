import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import Reason from "../Reason";
import { reasonAbout } from "../../services/reasonApi";
const context = vi.hoisted(() => ({ activeDomain: { id: "trading", name: "Trading" } }));
vi.mock("../../context/useDomain", () => ({ useDomain: () => context }));
vi.mock("../../services/reasonApi", () => ({ reasonAbout: vi.fn() }));
const result = { mission_id: "mission-1", reasoning: { conclusion: "A bounded conclusion", evidence_summary: "One source supports this.", inference_summary: "A reported inference.", status: "complete", confidence: { score: 0.6, level: "moderate", basis: "Evidence support", factors: [{ name: "support", explanation: "Reported support factor", contribution: 0.2 }], uncertainty: ["Some uncertainty"] }, evidence: { source_count: 1, document_count: 1, domain_count: 1, sources: [], gaps: [] }, limitations: [], alternatives: [], missing_information: [], reasoning_trace: ["Evidence retrieved"], recommended_next_step: "Inspect the source." }, coherence: { evaluation_status: "not_evaluated", coherent: false, constitutional_score: 0, articles_consulted: [], conflicts: [], recommendations: [] } };
async function submit(question = "Investigate price behavior") {
  fireEvent.change(screen.getByLabelText("Question"), { target: { value: question } });
  fireEvent.click(screen.getByRole("button", { name: "Analyze Evidence" }));
  await screen.findByText("A bounded conclusion");
}
beforeEach(() => { vi.clearAllMocks(); sessionStorage.clear(); context.activeDomain = { id: "trading", name: "Trading" }; reasonAbout.mockResolvedValue(result); });
test("captures mission scope and retrieval controls; later domain changes do not relabel the report", async () => {
  const { rerender } = render(<Reason />);
  fireEvent.change(screen.getByLabelText("Topic filter"), { target: { value: "price_action" } });
  fireEvent.change(screen.getByLabelText("Maximum evidence chunks"), { target: { value: "8" } });
  await submit();
  expect(reasonAbout).toHaveBeenCalledWith(expect.objectContaining({ module: "trading", topic: "price_action", limit: 8, signal: expect.anything() }));
  context.activeDomain = { id: "engineering", name: "Engineering" }; rerender(<Reason />);
  expect(screen.getByText(/current domain differs from this report/)).toBeInTheDocument();
  expect(screen.getByText(/Trading · price_action/)).toBeInTheDocument();
  expect(screen.getByText("Unassessed")).toBeInTheDocument();
  expect(screen.queryByRole("progressbar", { name: "Constitutional coherence" })).not.toBeInTheDocument();
});
test("preserves the draft and completed report after leaving the page", async () => {
  const first = render(<Reason />); await submit(); first.unmount();
  render(<Reason />);
  expect(screen.getByLabelText("Question")).toHaveValue("Investigate price behavior");
  expect(screen.getByText("A bounded conclusion")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Clear report" }));
  expect(screen.queryByText("A bounded conclusion")).not.toBeInTheDocument();
});
test("a failed follow-up preserves the last report and permits retry", async () => {
  render(<Reason />); await submit();
  reasonAbout.mockRejectedValueOnce(Error("Provider unavailable"));
  fireEvent.change(screen.getByLabelText("Question"), { target: { value: "Follow-up" } });
  fireEvent.click(screen.getByRole("button", { name: "Analyze Evidence" }));
  await screen.findByText("Provider unavailable");
  expect(screen.getByText("A bounded conclusion")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Analyze Evidence" })).toBeEnabled();
});
test("stops local waiting and ignores late results from the abandoned request", async () => {
  let finish;
  reasonAbout.mockImplementation(({ signal }) => new Promise((resolve, reject) => { finish = resolve; signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError"))); }));
  render(<Reason />);
  fireEvent.change(screen.getByLabelText("Question"), { target: { value: "Pending request" } });
  fireEvent.click(screen.getByRole("button", { name: "Analyze Evidence" }));
  fireEvent.click(await screen.findByRole("button", { name: "Stop waiting" }));
  await screen.findByText(/Stopped waiting for this request/);
  finish(result);
  expect(screen.queryByText("A bounded conclusion")).not.toBeInTheDocument();
});
test("cross-domain requests remain unconstrained and insufficient evidence offers useful navigation", async () => {
  context.activeDomain = { id: "all", name: "All Domains" };
  reasonAbout.mockResolvedValue({ ...result, reasoning: { ...result.reasoning, conclusion: null, status: "insufficient_evidence" } });
  const navigate = vi.fn(); render(<Reason onNavigate={navigate} />);
  fireEvent.change(screen.getByLabelText("Question"), { target: { value: "Unanswered question" } });
  fireEvent.click(screen.getByRole("button", { name: "Analyze Evidence" }));
  await screen.findByText("No supported conclusion");
  expect(reasonAbout).toHaveBeenCalledWith(expect.objectContaining({ module: null }));
  fireEvent.click(screen.getByRole("button", { name: "Add evidence in Teach" }));
  expect(navigate).toHaveBeenCalledWith("teach");
});
test("aborts a pending request on navigation", async () => {
  reasonAbout.mockImplementation(({ signal }) => new Promise((resolve, reject) => signal.addEventListener("abort", () => reject(new DOMException("Aborted", "AbortError")))));
  const view = render(<Reason />);
  fireEvent.change(screen.getByLabelText("Question"), { target: { value: "Pending request" } });
  fireEvent.click(screen.getByRole("button", { name: "Analyze Evidence" }));
  const signal = reasonAbout.mock.calls[0][0].signal;
  view.unmount(); expect(signal.aborted).toBe(true);
});

test("whitespace-only questions never reach the reasoning service", () => {
  render(<Reason />);
  fireEvent.change(screen.getByLabelText("Question"), { target: { value: "   " } });
  expect(screen.getByRole("button", { name: "Analyze Evidence" })).toBeDisabled();
  expect(reasonAbout).not.toHaveBeenCalled();
});
test("corrupt saved reports do not crash the workspace", () => {
  sessionStorage.setItem("sentinel.reasonWorkspace", JSON.stringify({ question: "Preserved draft", report: { result: { reasoning: {} } } }));
  render(<Reason />);
  expect(screen.getByLabelText("Question")).toHaveValue("Preserved draft");
  expect(screen.queryByText("Last completed report")).not.toBeInTheDocument();
});
