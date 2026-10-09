import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import Intelligence from "../Intelligence";
import Governance from "../Governance";
import Systems from "../Systems";
vi.mock("../../services/workspaceApi", () => ({ workspaceRequest: vi.fn() }));
vi.mock("../../context/useDomain", () => ({ useDomain: vi.fn() }));
import { workspaceRequest } from "../../services/workspaceApi";
import { useDomain } from "../../context/useDomain";
const graph = {
  nodes: [
    { id: "a", title: "Evidence doctrine", path: "a.md" },
    { id: "b", title: "Human authority", path: "b.md" },
  ],
  edges: [
    {
      source: "a",
      target: "b",
      relationship: "references",
      basis: "explicit Markdown link",
    },
  ],
  unresolved_references: [
    { source: "a", reference: "ADR-999", reason: "missing_document" },
  ],
  limitation: "References do not establish semantic truth.",
};
const catalog = [
  {
    id: "doc1",
    filename: "Evidence.pdf",
    collection: "engineering",
    status: "indexed",
    chunk_count: 2,
  },
];
const summary = {
  principles: {
    status: "warning",
    document_count: 42,
    warnings: ["One document is empty"],
    empty_documents: ["Rules.md"],
  },
  adr_037_status: "Proposed",
  proposition_inference_boundary: "closed",
  history_policy: "append_only",
  limitations: ["No execution authority"],
};
const systems = {
  status: "ready",
  observed_at: "2026-10-08T20:00:00Z",
  services: [
    {
      name: "Persistent history",
      status: "ready",
      detail: "Storage available",
    },
  ],
  model_features_configured: false,
  warnings: ["Model credentials missing"],
};
function respond(path) {
  if (path === "/intelligence/connections") return graph;
  if (path === "/governance/summary") return summary;
  if (path === "/documents") return catalog;
  if (path === "/systems/status") return systems;
  return [];
}
beforeEach(() => {
  vi.clearAllMocks();
  useDomain.mockReturnValue({
    activeDomain: { id: "engineering", name: "Engineering" },
  });
  workspaceRequest.mockImplementation(async (path) => respond(path));
});
test("Intelligence inspects references and unresolved provenance", async () => {
  render(<Intelligence />);
  fireEvent.click(
    await screen.findByRole("button", { name: /Evidence doctrine/ }),
  );
  expect(screen.getByText("Basis: explicit Markdown link")).toBeInTheDocument();
  expect(screen.getByText("ADR-999 · missing document")).toBeInTheDocument();
  expect(
    screen.getByText("References do not establish semantic truth."),
  ).toBeInTheDocument();
});
test("empty learning history cannot initiate fabricated reflection", async () => {
  render(<Intelligence />);
  await screen.findByText(/No Learning Events are recorded/);
  expect(
    screen.getByRole("button", { name: "Reflect on selected history" }),
  ).toBeDisabled();
});
test("reflection resolves selected recorded events and shows inadmissible outcomes", async () => {
  workspaceRequest.mockImplementation(async (path) => {
    if (path === "/intelligence/learning-events")
      return [
        {
          learning_event_id: "event-1",
          domain_ids: ["engineering"],
          summary: "Evidence indexed",
          learned_at: "2026-10-08",
          source: "source.pdf",
        },
      ];
    if (path === "/intelligence/reflection")
      return {
        status: "limited",
        pattern_count: 1,
        insight_count: 0,
        recommendation_count: 0,
        reflection_confidence_level: "low",
        admissible: false,
        formatted_reflection: "No independent constitutional verification.",
      };
    return respond(path);
  });
  render(<Intelligence />);
  fireEvent.click(await screen.findByRole("checkbox"));
  fireEvent.click(
    screen.getByRole("button", { name: "Reflect on selected history" }),
  );
  expect(
    await screen.findByText("No independent constitutional verification."),
  ).toBeInTheDocument();
  expect(workspaceRequest).toHaveBeenCalledWith(
    "/intelligence/reflection",
    expect.objectContaining({
      body: {
        title: "Patterns in recent learning",
        learning_event_ids: ["event-1"],
      },
    }),
  );
});
test("planning sends the domain and normalized constraints and preserves provider failures", async () => {
  workspaceRequest.mockImplementation(async (path) => {
    if (path === "/cognition/plan")
      throw new Error("Provider credentials rejected");
    return respond(path);
  });
  render(<Intelligence />);
  fireEvent.change(screen.getByLabelText("Objective"), {
    target: { value: "  Reduce incident risk  " },
  });
  fireEvent.change(screen.getByLabelText("Constraints, one per line"), {
    target: { value: "No production changes\n\n Human approval " },
  });
  fireEvent.click(screen.getByRole("button", { name: "Propose plan" }));
  await screen.findByText("Provider credentials rejected");
  expect(workspaceRequest).toHaveBeenCalledWith(
    "/cognition/plan",
    expect.objectContaining({
      method: "POST",
      body: {
        objective: "Reduce incident risk",
        constraints: ["No production changes", "Human approval"],
        workspace: "intelligence",
        module: "engineering",
      },
    }),
  );
});
test("Governance preserves gates and archives through the lifecycle API", async () => {
  let archived = false;
  workspaceRequest.mockImplementation(async (path) => {
    if (path === "/knowledge/doc1/archive") {
      archived = true;
      return { status: "archived" };
    }
    if (path === "/documents")
      return catalog.map((document) => ({
        ...document,
        status: archived ? "archived" : "indexed",
      }));
    return respond(path);
  });
  render(<Governance />);
  expect(
    await screen.findByText("Proposition → Inference: closed"),
  ).toBeInTheDocument();
  fireEvent.click(await screen.findByRole("button", { name: "Archive" }));
  await screen.findByRole("button", { name: "Restore" });
  expect(workspaceRequest).toHaveBeenCalledWith("/knowledge/doc1/archive", {
    method: "PUT",
  });
});
test("failed archive remains visible without a false successful change", async () => {
  workspaceRequest.mockImplementation(async (path) => {
    if (path === "/knowledge/doc1/archive")
      throw new Error("Memory unavailable");
    return respond(path);
  });
  render(<Governance />);
  fireEvent.click(await screen.findByRole("button", { name: "Archive" }));
  await screen.findByText("Memory unavailable");
  expect(
    screen.queryByRole("button", { name: "Restore" }),
  ).not.toBeInTheDocument();
});
test("verification delegates its objective without granting execution authority", async () => {
  workspaceRequest.mockImplementation(async (path) => {
    if (path === "/verification") throw new Error("Verification unavailable");
    return respond(path);
  });
  render(<Governance />);
  fireEvent.change(screen.getByLabelText("Objective"), {
    target: { value: "Check an incident response" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Verify proposed plan" }));
  await screen.findByText("Verification unavailable");
  expect(workspaceRequest).toHaveBeenCalledWith(
    "/verification",
    expect.objectContaining({
      body: expect.objectContaining({
        workspace: "governance",
        module: "engineering",
        objective: "Check an incident response",
      }),
    }),
  );
});
test("Systems separates measured readiness from provider and semantic acceptance", async () => {
  render(<Systems />);
  await screen.findByText("Storage ready");
  expect(screen.getByText(/Model credentials required/)).toBeInTheDocument();
  expect(
    screen.getByText(
      "Constitutional semantic evaluation: not independently verified",
    ),
  ).toBeInTheDocument();
  expect(screen.getByText("Storage available")).toBeInTheDocument();
});
test("Systems reports failures and supports retry", async () => {
  workspaceRequest.mockRejectedValueOnce(new Error("Service unavailable"));
  render(<Systems />);
  await screen.findByText("Service unavailable");
  fireEvent.click(
    screen.getByRole("button", { name: "Retry system condition" }),
  );
  await screen.findByText("Storage ready");
});

test("Governance scopes operational memory to the current domain", async () => {
  workspaceRequest.mockImplementation(async (path) => {
    if (path === "/documents")
      return [
        ...catalog,
        {
          id: "trading-doc",
          filename: "Trading.pdf",
          collection: "trading",
          module: "trading",
          status: "indexed",
          chunk_count: 3,
        },
      ];
    return respond(path);
  });
  render(<Governance />);
  await screen.findByText("Evidence.pdf");
  expect(screen.queryByText("Trading.pdf")).not.toBeInTheDocument();
});
