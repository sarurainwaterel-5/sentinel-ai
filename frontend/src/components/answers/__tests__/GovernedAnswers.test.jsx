import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import GovernedAnswerPanel from "../GovernedAnswerPanel";
import AnswerAvailabilityNotice from "../AnswerAvailabilityNotice";
import { getGovernedAnswerReadiness } from "../../../services/governedAnswerApi";
vi.mock("../../../services/governedAnswerApi", () => ({ getGovernedAnswerReadiness: vi.fn() }));
function fixture() {
  return { execution_source: "unit_test", empirical_acceptance: false, public_response: {
    schema_version: "21.v1", outcome: "disabled", answer_text: null, claims: [], question: "What do the reports say?",
    snapshot_id: "snap", scope: { organization_id: "default", module: "engineering" },
    validation: { release_status: "disabled", semantic_grounding_verified: false, coverage_status: "passed", citation_status: "passed", rejection_reasons: [] },
    evidence: [{ evidence_id: "e", document_id: "d", collection: "knowledge", chunk_index: 0, status: "indexed", snapshot_id: "snap", organization_id: "default", module: "engineering", text: "<script>execute()</script>", filename: "Synthetic PDF" }],
    premises: [{ premise_id: "p1" }, { premise_id: "p2" }], conflicts: ["Reports disagree."], uncertainty: ["Source truth is unknown."] },
    fixture_claim: { kind: "attributed_synthesis", premise_ids: ["p1", "p2"], statement: "The supplied reports disagree.", qualifications: ["No source truth is established."], evidence_ids: ["e"],
      validation: { structural_status: "passed", statement_status: "admissible", semantic_grounding_verified: false,
        statement_result: { admissible: true, validation_scope: "independent_model_semantic_admissibility", rejection_reasons: [] } } } };
}
beforeEach(() => vi.clearAllMocks());
test("inspectable preview keeps citations, conflicts and independent status explicit", () => {
  render(<GovernedAnswerPanel report={fixture()} />);
  expect(screen.getByText("The supplied reports disagree.")).toBeInTheDocument();
  const link = screen.getByRole("link", { name: "Inspect source 1" });
  expect(document.getElementById(link.getAttribute("href").slice(1))).toHaveTextContent("Source 1");
  fireEvent.click(screen.getByText("Inspect source 1 provenance and quote"));
  expect(screen.getByText("<script>execute()</script>")).toBeInTheDocument();
  expect(document.querySelector("script")).toBeNull();
  expect(screen.getByText("Reports disagree.")).toBeInTheDocument();
  expect(screen.getByText(/Semantic grounding verified: false/)).toBeInTheDocument();
});
test.each(["unknown", "missingCitation", "wrongScope", "verified", "production"]) ("invalid %s withholds preview", mode => {
  const report = fixture();
  if (mode === "unknown") report.public_response.outcome = "answered";
  if (mode === "missingCitation") report.fixture_claim.evidence_ids = ["unknown"];
  if (mode === "wrongScope") report.public_response.evidence[0].organization_id = "other";
  if (mode === "verified") report.fixture_claim.validation.semantic_grounding_verified = true;
  if (mode === "production") report.empirical_acceptance = true;
  render(<GovernedAnswerPanel report={report} />);
  expect(screen.getByRole("alert")).toBeInTheDocument();
  expect(screen.queryByText("The supplied reports disagree.")).not.toBeInTheDocument();
});
test.each(["insufficient_evidence", "blocked_provenance", "blocked_relationships", "blocked_validation", "rejected", "provider_failure"])("%s shows withheld candidate", outcome => {
  const report = fixture(); report.public_response.outcome = outcome; report.fixture_claim = null;
  render(<GovernedAnswerPanel report={report} />);
  expect(screen.getByText(/entire candidate was withheld/)).toBeInTheDocument();
});
test("readiness failure stays disabled and permits retry", async () => {
  getGovernedAnswerReadiness.mockRejectedValueOnce(Error("Readiness unavailable")).mockResolvedValueOnce({ blockers: ["production_release_disabled"] });
  render(<AnswerAvailabilityNotice />);
  await screen.findByText("Readiness unavailable");
  fireEvent.click(screen.getByRole("button", { name: "Retry readiness" }));
  await screen.findByText(/Release gate is closed/);
  expect(screen.queryByRole("button", { name: /answer question/i })).not.toBeInTheDocument();
});
test("unmount aborts readiness request", () => {
  getGovernedAnswerReadiness.mockImplementation(() => new Promise(() => {}));
  const view = render(<AnswerAvailabilityNotice />);
  const signal = getGovernedAnswerReadiness.mock.calls[0][0]; view.unmount();
  expect(signal.aborted).toBe(true);
});
