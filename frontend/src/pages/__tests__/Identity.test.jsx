import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import Identity from "../Identity";
import { workspaceRequest } from "../../services/workspaceApi";
vi.mock("../../services/workspaceApi", () => ({ workspaceRequest: vi.fn() }));
const health = {
  status: "warning",
  document_count: 12,
  layer_count: 3,
  types: { architecture_decision: 2, sprint_record: 4 },
  layers: { identity: 1, architecture: 2 },
  warnings: ["One document has no instructions"],
  empty_documents: ["empty.md"],
};
const library = {
  observed_at: "2026-10-09T00:00:00Z",
  documents: [
    { path: "IDENTITY.md", title: "Identity statement", layer: "identity" },
    {
      path: "architecture/RULES.md",
      title: "Architecture rules",
      layer: "architecture",
    },
  ],
};
const respond = async (path) =>
  path === "/canon/health"
    ? health
    : path === "/canon/library"
      ? library
      : {
          title: "Identity statement",
          path: "IDENTITY.md",
          content: "# Identity\nHuman authority remains explicit.",
        };
beforeEach(() => {
  vi.clearAllMocks();
  workspaceRequest.mockImplementation(respond);
});
test("reports observed warnings without manufactured understanding or version", async () => {
  render(<Identity />);
  await screen.findByText("Structure: warning");
  expect(
    screen.getByText("One document has no instructions"),
  ).toBeInTheDocument();
  expect(
    screen.queryByText(/No structural inconsistencies/),
  ).not.toBeInTheDocument();
  expect(screen.queryByText(/I understand myself/)).not.toBeInTheDocument();
  expect(screen.queryByText("Version")).not.toBeInTheDocument();
});
test("reads the identity source and filters the library", async () => {
  render(<Identity />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Read identity statement" }),
  );
  await screen.findByText("# Identity Human authority remains explicit.");
  expect(workspaceRequest).toHaveBeenCalledWith(
    "/canon/document?path=IDENTITY.md",
    expect.anything(),
  );
  fireEvent.change(screen.getByLabelText("Knowledge layer"), {
    target: { value: "architecture" },
  });
  expect(
    screen.getByRole("button", { name: /Architecture rules/ }),
  ).toBeInTheDocument();
  expect(
    screen.queryByRole("button", { name: /Identity statement identity/ }),
  ).not.toBeInTheDocument();
  fireEvent.change(screen.getByLabelText("Find a principle"), {
    target: { value: "missing" },
  });
  expect(
    screen.getByText("No principle documents match these filters."),
  ).toBeInTheDocument();
});
test("Canon failures support retry without healthy status", async () => {
  workspaceRequest.mockImplementation(async (path) => {
    if (path === "/canon/health") throw Error("Canon unavailable");
    return respond(path);
  });
  render(<Identity />);
  await screen.findAllByText("Canon unavailable");
  expect(screen.queryByText("Structure: healthy")).not.toBeInTheDocument();
  workspaceRequest.mockImplementation(respond);
  fireEvent.click(
    screen.getByRole("button", { name: "Retry Canon condition" }),
  );
  await screen.findByText("Structure: warning");
});
test("reader displays source HTML as inert text", async () => {
  workspaceRequest.mockImplementation(async (path) =>
    path.startsWith("/canon/document")
      ? {
          title: "Identity statement",
          path: "IDENTITY.md",
          content: "<script>unsafe()</script>",
        }
      : respond(path),
  );
  const { container } = render(<Identity />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Read identity statement" }),
  );
  await screen.findByText("<script>unsafe()</script>");
  expect(container.querySelector("script")).toBeNull();
});
test("operator navigation remains human-directed", () => {
  const navigate = vi.fn();
  render(<Identity onNavigate={navigate} />);
  fireEvent.click(screen.getByRole("button", { name: "Open Governance" }));
  expect(navigate).toHaveBeenCalledWith("governance");
});


test("refresh reloads the selected source rather than retaining stale content", async () => {
  let content = "Original source";
  workspaceRequest.mockImplementation(async path => path.startsWith("/canon/document") ? {title: "Identity statement", path: "IDENTITY.md", content} : respond(path));
  render(<Identity />);
  fireEvent.click(await screen.findByRole("button", {name: "Read identity statement"}));
  await screen.findByText("Original source");
  content = "Updated source";
  fireEvent.click(screen.getByRole("button", {name: "Refresh observations"}));
  await screen.findByText("Updated source");
  expect(screen.queryByText("Original source")).not.toBeInTheDocument();
});
