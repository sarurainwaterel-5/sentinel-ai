import { useState } from "react";
import { useDomain } from "../context/useDomain";
import { useWorkspaceData } from "../components/workspaces/useWorkspaceData";
import {
  ResourceState,
  TextList,
  WorkspaceHeader,
} from "../components/workspaces/WorkspaceParts";
import CognitiveOperation from "../components/workspaces/CognitiveOperation";
import { workspaceRequest } from "../services/workspaceApi";

export default function Governance() {
  const { activeDomain } = useDomain();
  const summary = useWorkspaceData("/governance/summary");
  const documents = useWorkspaceData("/documents");
  const [query, setQuery] = useState("");
  const [action, setAction] = useState({
    pending: null,
    error: null,
    message: null,
  });
  const visibleDocuments = (documents.data ?? []).filter(
    (document) =>
      document.filename.toLowerCase().includes(query.toLowerCase()) &&
      (!activeDomain?.id ||
        activeDomain.id === "all" ||
        (document.module ?? document.collection) === activeDomain.id),
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
        message: `${document.filename} ${operation === "archive" ? "archived and excluded from recall" : "restored to recall"}.`,
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
              <details>
                <summary>Principle documents awaiting instructions</summary>
                <TextList
                  items={summary.data?.principles.empty_documents}
                  empty="No empty documents detected."
                />
              </details>
            </div>
            <div>
              <h3>Acceptance boundaries</h3>
              <p>Constitutional evaluation: not independently verified</p>
              <p>ADR-037: {summary.data?.adr_037_status}</p>
              <p>
                Proposition → Inference:{" "}
                {summary.data?.proposition_inference_boundary}
              </p>
              <p>
                History: {summary.data?.history_policy.replaceAll("_", " ")}
              </p>
              <p>Execution authority: human</p>
            </div>
          </div>
          <TextList items={summary.data?.limitations} />
        </ResourceState>
      </section>
      <section className="panel">
        <h2>Govern operational memory</h2>
        <p className="muted">
          Archiving removes a document from retrieval while preserving its
          catalog and stored evidence. Restore it when it should participate
          again. Principle documents and cognitive history are not edited here.
        </p>
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
        {action.message && <p role="status">{action.message}</p>}
        <ResourceState resource={documents} label="document catalog">
          <div className="workspace-table-wrap">
            <table className="workspace-table">
              <caption>Operational document catalog</caption>
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Collection</th>
                  <th>Status</th>
                  <th>Memory chunks</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {visibleDocuments.map((document) => (
                  <tr key={document.id}>
                    <td>{document.filename}</td>
                    <td>{document.collection}</td>
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
              No documents match this domain and search. Select another scope or teach Sentinel new evidence.
            </p>
          )}
        </ResourceState>
      </section>
      <CognitiveOperation kind="verify" />
    </div>
  );
}
