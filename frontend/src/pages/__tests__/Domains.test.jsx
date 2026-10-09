import { fireEvent, render, screen, within } from "@testing-library/react";
import { vi } from "vitest";
import Domains from "../Domains";
import { useDomain } from "../../context/useDomain";
import { workspaceRequest } from "../../services/workspaceApi";
vi.mock("../../context/useDomain", () => ({ useDomain: vi.fn() }));
vi.mock("../../services/workspaceApi", () => ({ workspaceRequest: vi.fn() }));
const trading = {
  domain_id: "trading",
  name: "Trading",
  kind: "system",
  status: "developing",
  description: "Market evidence",
  evidence: [
    {
      evidence_id: "adr",
      title: "Trading architecture",
      description: "Registry basis",
      source: "trading.md",
    },
  ],
};
const custom = {
  domain_id: "custom",
  name: "Research",
  kind: "user",
  status: "planned",
  description: "Research evidence",
  evidence: [],
};
const model = {
  system_domains: [trading],
  user_domains: [custom],
  summary: { total_domains: 2 },
  validation: {
    status: "valid",
    checks: [],
    passed: 2,
    warnings: 0,
    errors: 0,
  },
};
let context;
beforeEach(() => {
  vi.clearAllMocks();
  context = {
    domainModel: model,
    activeDomain: { id: "all", name: "All Domains" },
    selectDomain: vi.fn(),
    refreshDomains: vi.fn(),
    domainError: null,
    isLoadingDomains: false,
  };
  useDomain.mockImplementation(() => context);
  workspaceRequest.mockResolvedValue({
    observed_at: "2026-10-08T12:00:00Z",
    domains: {
      trading: {
        indexed_documents: 4,
        indexed_chunks: 119,
        archived_documents: 1,
        other_documents: 0,
      },
    },
    basis: "Catalog counts only",
  });
});
test("shows real memory separately from maturity and architecture evidence", async () => {
  render(<Domains />);
  const card = within(screen.getByRole("article", { name: "Trading domain" }));
  await card.findByText("119");
  expect(card.getByText("Maturity: developing")).toBeInTheDocument();
  expect(card.getByText("4")).toBeInTheDocument();
  expect(card.getByText("Architecture references (1)")).toBeInTheDocument();
});
test("domain shortcuts select scope before entering Recall", () => {
  const navigate = vi.fn();
  render(<Domains onNavigate={navigate} />);
  fireEvent.click(
    within(screen.getByRole("article", { name: "Trading domain" })).getByRole(
      "button",
      { name: "Recall", exact: true },
    ),
  );
  expect(context.selectDomain).toHaveBeenCalledWith("trading");
  expect(navigate).toHaveBeenCalledWith("recall");
  expect(context.selectDomain.mock.invocationCallOrder[0]).toBeLessThan(
    navigate.mock.invocationCallOrder[0],
  );
});
test("renders user domains and filters without inventing domains", async () => {
  render(<Domains />);
  await screen.findByText("119");
  fireEvent.change(screen.getByLabelText("Domain type"), {
    target: { value: "user" },
  });
  expect(
    screen.getByRole("article", { name: "Research domain" }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole("article", { name: "Trading domain" }),
  ).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Find a domain"), {
    target: { value: "missing" },
  });
  expect(screen.getByText("No matching domains")).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Clear filters" }));
  expect(screen.getAllByRole("article")).toHaveLength(2);
});
test("memory failures do not show false zero counts and can retry", async () => {
  workspaceRequest.mockRejectedValueOnce(new Error("Storage unavailable"));
  render(<Domains />);
  await screen.findByText("Storage unavailable");
  expect(screen.getAllByText("Memory counts unavailable.")).toHaveLength(2);
  expect(
    screen.queryByText(
      "Teach a PDF in this domain to add evidence for Recall.",
    ),
  ).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: "Retry domain memory" }));
  await screen.findByText("119");
});
test("registry failure is retryable and does not render stale cards", () => {
  context.domainError = "Registry unavailable";
  render(<Domains />);
  expect(screen.queryByRole("article")).not.toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Retry domain registry" }),
  );
  expect(context.refreshDomains).toHaveBeenCalledOnce();
});
test("current domain and explicit all-domain selection work", () => {
  context.activeDomain = { id: "trading", name: "Trading" };
  render(<Domains />);
  expect(
    screen.getByRole("button", { name: "Current domain" }),
  ).toHaveAttribute("aria-pressed", "true");
  fireEvent.click(screen.getByRole("button", { name: "Use All Domains" }));
  expect(context.selectDomain).toHaveBeenCalledWith("all");
});
