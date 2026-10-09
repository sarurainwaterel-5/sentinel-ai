import { useState } from "react";
import { useDomain } from "../context/useDomain";
import { useWorkspaceData } from "../components/workspaces/useWorkspaceData";
import {
  ResourceState,
  TextList,
  WorkspaceHeader,
  WorkspaceTabs,
  ToolPanel,
} from "../components/workspaces/WorkspaceParts";
import CognitiveOperation from "../components/workspaces/CognitiveOperation";
import { workspaceRequest } from "../services/workspaceApi";

export default function Governance({ onTeach }) {
  const { activeDomain } = useDomain();
  const summary = useWorkspaceData("/governance/summary");
  const documents = useWorkspaceData("/documents");
  const [query, setQuery] = useState("");
  const [active, setActive] = useState("Documents");
  const [filter, setFilter] = useState("active");
  const [sort, setSort] = useState("newest");
  const [inspected, setInspected] = useState(null);
  const [undo, setUndo] = useState(null);
  const [action, setAction] = useState({
    pending: null,
    error: null,
    message: null,
  });
  const visibleDocuments = (documents.data ?? [])
    .filter(
      (document) =>
        (filter === "all" ||
          (filter === "archived"
            ? document.status === "archived"
            : document.status !== "archived")) &&
        document.filename.toLowerCase().includes(query.toLowerCase()) &&
        (!activeDomain?.id ||
          activeDomain.id === "all" ||
          (document.module ?? document.collection) === activeDomain.id),
    )
    .sort((a, b) =>
      sort === "name"
        ? a.filename.localeCompare(b.filename)
        : (b.uploaded_at ?? "").localeCompare(a.uploaded_at ?? ""),
    );
  const inspectedDocument = (documents.data ?? []).find(
    (document) => document.id === inspected,
  );
  async function changeStatus(document) {
    if (action.pending) return;
    const operation = document.status === "archived" ? "restore" : "archive";
    setAction({ pending: document.id, error: null, message: null });
    try {
      await workspaceRequest(
        `/knowledge/${encodeURIComponent(document.id)}/${operation}`,
        { method: "PUT" },
      );
      setAction({
        pending: null,
        error: null,
        message:
          operation === "archive"
            ? "Document archived; excluded from recall."
            : "Document restored to recall.",
      });
      setUndo({
        ...document,
        status: operation === "archive" ? "archived" : "indexed",
      });
      documents.refresh();
    } catch (error) {
      setAction({ pending: null, error: error.message, message: null });
    }
  }
  function refresh() {
    summary.refresh();
    documents.refresh();
  }
  return (
    <div className="page workspace-page">
      <WorkspaceHeader
        title="Protect principles and preserve intellectual history"
        description="Inspect integrity, govern operational memory, and verify proposed actions without granting execution authority."
        onRefresh={refresh}
        loading={summary.loading || documents.loading}
      />
      <WorkspaceTabs
        tabs={["Documents", "Verify", "Principles"]}
        active={active}
        onChange={setActive}
      />
      <ToolPanel name="Principles" active={active}>
        <section className="panel">
          <h2>Principles and authority</h2>
          <ResourceState resource={summary} label="governance">
            <div className="workspace-grid">
              <div>
                <h3>Principle structure</h3>
                <p>
                  {summary.data?.principles.status} ·{" "}
                  {summary.data?.principles.document_count} documents
                </p>
                <TextList
                  items={summary.data?.principles.warnings}
                  empty="No structural warnings recorded."
                />
                {summary.data?.principles.empty_documents?.length > 0 && (
                  <details>
                    <summary>Principle documents awaiting instructions</summary>
                    <TextList
                      items={summary.data?.principles.empty_documents}
                      empty="No empty documents detected."
                    />
                  </details>
                )}
              </div>
              <div>
                <h3>Acceptance boundaries</h3>
                <p>Constitutional evaluation: not independently verified</p>
                <details>
                  <summary>Architecture and acceptance details</summary>
                  <p>ADR-037: {summary.data?.adr_037_status}</p>
                  <p>
                    Proposition → Inference:{" "}
                    {summary.data?.proposition_inference_boundary}
                  </p>
                  <p>
                    History: {summary.data?.history_policy.replaceAll("_", " ")}
                  </p>
                </details>
                <p>Execution authority: human</p>
              </div>
            </div>
            <details>
              <summary>Evaluation limitations</summary>
              <TextList items={summary.data?.limitations} />
            </details>
          </ResourceState>
        </section>
      </ToolPanel>
      <ToolPanel name="Documents" active={active}>
        <section className="panel">
          <h2>Govern operational memory</h2>
          <details>
            <summary>How archiving works</summary>
            <p className="muted">
              Archiving removes a document from retrieval while preserving its
              catalog and stored evidence. Restore it when it should participate
              again. Principle documents and cognitive history are not edited
              here.
            </p>
          </details>
          <div className="workspace-toolbar">
            <label>
              Status
              <select
                aria-label="Status"
                value={filter}
                onChange={(event) => setFilter(event.target.value)}
              >
                <option value="active">Active</option>
                <option value="archived">Archived</option>
                <option value="all">All documents</option>
              </select>
            </label>
            <label>
              Sort by
              <select
                aria-label="Sort by"
                value={sort}
                onChange={(event) => setSort(event.target.value)}
              >
                <option value="newest">Newest upload</option>
                <option value="name">Document name</option>
              </select>
            </label>
          </div>
          <label className="workspace-search">
            Find an operational document
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          {action.error && (
            <p role="alert" className="workspace-error">
              {action.error}
            </p>
          )}
          {action.message && (
            <div className="workspace-feedback" role="status">
              {action.message}{" "}
              {undo && (
                <button
                  className="secondary-action"
                  disabled={Boolean(action.pending)}
                  onClick={() => changeStatus(undo)}
                >
                  Undo
                </button>
              )}
              <button
                className="secondary-action"
                onClick={() => {
                  setUndo(null);
                  setAction({ ...action, message: null });
                }}
              >
                Dismiss
              </button>
            </div>
          )}
          <ResourceState resource={documents} label="document catalog">
            <div className="workspace-table-wrap">
              <table className="workspace-table">
                <caption>Operational document catalog</caption>
                <thead>
                  <tr>
                    <th>Document</th>
                    <th>Domain</th>
                    <th>Uploaded</th>
                    <th>Status</th>
                    <th>Memory chunks</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {visibleDocuments.map((document) => (
                    <tr key={document.id}>
                      <td>
                        <button
                          className="connection-link"
                          onClick={() => setInspected(document.id)}
                        >
                          {document.filename}
                        </button>
                      </td>
                      <td>{document.module ?? document.collection}</td>
                      <td>
                        {document.uploaded_at
                          ? new Date(document.uploaded_at).toLocaleDateString()
                          : "Unrecorded"}
                      </td>
                      <td>{document.status}</td>
                      <td>{document.chunk_count}</td>
                      <td>
                        <button
                          className="secondary-action"
                          disabled={
                            Boolean(action.pending) ||
                            !["indexed", "archived"].includes(document.status)
                          }
                          onClick={() => changeStatus(document)}
                        >
                          {action.pending === document.id
                            ? "Updating…"
                            : document.status === "archived"
                              ? "Restore"
                              : "Archive"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {visibleDocuments.length === 0 && (
              <p className="muted">
                No documents match these filters. Select another status or
                domain, or teach Sentinel new evidence.
              </p>
            )}
          </ResourceState>
          {visibleDocuments.length === 0 &&
            !documents.loading &&
            !documents.error && (
              <button className="secondary-action" onClick={onTeach}>
                Teach Sentinel a document
              </button>
            )}
          {inspectedDocument && (
            <aside
              className="document-inspector"
              aria-label="Document inspector"
            >
              <h3>{inspectedDocument.filename}</h3>
              <dl>
                <dt>Domain</dt>
                <dd>
                  {inspectedDocument.module ?? inspectedDocument.collection}
                </dd>
                <dt>Topic</dt>
                <dd>{inspectedDocument.topic ?? "Unrecorded"}</dd>
                <dt>Organization</dt>
                <dd>{inspectedDocument.organization_id ?? "Unrecorded"}</dd>
                <dt>Uploaded</dt>
                <dd>
                  {inspectedDocument.uploaded_at
                    ? new Date(inspectedDocument.uploaded_at).toLocaleString()
                    : "Unrecorded"}
                </dd>
                <dt>Status</dt>
                <dd>{inspectedDocument.status}</dd>
                <dt>Memory chunks</dt>
                <dd>{inspectedDocument.chunk_count}</dd>
              </dl>
              <button
                className="secondary-action"
                onClick={() => setInspected(null)}
              >
                Close inspector
              </button>
            </aside>
          )}
        </section>
      </ToolPanel>
      <ToolPanel name="Verify" active={active}>
        <CognitiveOperation kind="verify" />
      </ToolPanel>
    </div>
  );
}
