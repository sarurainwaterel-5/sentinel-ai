import { useState } from "react";
import { useWorkspaceData } from "../components/workspaces/useWorkspaceData";
import {
  ResourceState,
  TextList,
  WorkspaceHeader,
  WorkspaceTabs,
  ToolPanel,
} from "../components/workspaces/WorkspaceParts";
import KnowledgeLayers from "../components/identity/KnowledgeLayers";

function PrincipleReader({ path }) {
  const document = useWorkspaceData(
    `/canon/document?path=${encodeURIComponent(path)}`,
  );
  return (
    <section
      className="panel principle-reader"
      aria-label="Principle document reader"
    >
      <ResourceState resource={document} label="principle document">
        <h2>{document.data?.title}</h2>
        <p className="muted">{document.data?.path} · Read-only source</p>
        {document.data?.content?.trim() ? (
          <pre className="principle-source">{document.data.content}</pre>
        ) : (
          <p className="workspace-notice">
            This document contains no instructions.
          </p>
        )}
      </ResourceState>
    </section>
  );
}

export default function Identity({ onNavigate }) {
  const health = useWorkspaceData("/canon/health");
  const library = useWorkspaceData("/canon/library");
  const [active, setActive] = useState("Overview");
  const [query, setQuery] = useState("");
  const [layer, setLayer] = useState("all");
  const [selected, setSelected] = useState(null);
  const [readerRevision, setReaderRevision] = useState(0);
  const documents = library.data?.documents ?? [];
  const visible = documents.filter(
    (document) =>
      (layer === "all" || document.layer === layer) &&
      `${document.title} ${document.path}`
        .toLowerCase()
        .includes(query.toLowerCase()),
  );
  function refresh() {
    health.refresh();
    library.refresh();
    setReaderRevision(value => value + 1);
  }
  function open(path) {
    setSelected(path);
    setActive("Principles");
  }
  return (
    <div className="page workspace-page identity-workspace">
      <WorkspaceHeader
        title="Inspect the principles behind Sentinel"
        description="Identity is grounded in the Living Canon. Read source documents and inspect their structural condition without treating document presence as proof of understanding or semantic admissibility."
        onRefresh={refresh}
        loading={health.loading || library.loading}
      />
      <WorkspaceTabs
        tabs={["Overview", "Principles"]}
        active={active}
        onChange={setActive}
      />
      <ToolPanel name="Overview" active={active}>
        <section className="panel">
          <h2>Living Canon condition</h2>
          <ResourceState resource={health} label="Canon condition">
            <p className="workspace-condition">
              Structure: {health.data?.status ?? "Unreported"}
            </p>
            <p className="muted">
              Observed document organization and empty-file checks. This does
              not certify cognitive understanding or constitutional semantic
              accuracy.
            </p>
            <dl className="identity-metrics">
              {[
                ["Principle documents", health.data?.document_count],
                ["Knowledge layers", health.data?.layer_count],
                [
                  "Architecture decisions",
                  health.data?.types?.architecture_decision ?? 0,
                ],
                ["Sprint records", health.data?.types?.sprint_record ?? 0],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
            <h3>Structural observations</h3>
            <TextList
              items={health.data?.warnings}
              empty="No structural warnings observed."
            />
            {health.data?.empty_documents?.length > 0 && (
              <details>
                <summary>Documents without instructions</summary>
                <TextList items={health.data.empty_documents} />
              </details>
            )}
          </ResourceState>
        </section>
        <section className="panel">
          <h2>Identity and operator authority</h2>
          <p>
            Sentinel’s principles guide its work across domains. The source
            documents remain inspectable; this workspace does not edit or
            activate them.
          </p>
          <p className="workspace-notice">
            Constitutional semantic evaluation remains unverified. Confidence,
            principle availability, and permission to act are separate.
            Execution authority remains human.
          </p>
          <div className="identity-actions">
            {documents.some((document) => document.path === "IDENTITY.md") && (
              <button
                className="primary-action"
                onClick={() => open("IDENTITY.md")}
              >
                Read identity statement
              </button>
            )}
            <button
              className="secondary-action"
              onClick={() => setActive("Principles")}
            >
              Browse principles
            </button>
            <button
              className="secondary-action"
              onClick={() => onNavigate?.("governance")}
            >
              Open Governance
            </button>
            <button
              className="secondary-action"
              onClick={() => onNavigate?.("domains")}
            >
              Open Domains
            </button>
          </div>
        </section>
        <ResourceState resource={health} label="knowledge layers">
          <KnowledgeLayers layers={health.data?.layers ?? {}} />
        </ResourceState>
      </ToolPanel>
      <ToolPanel name="Principles" active={active}>
        <section className="panel">
          <h2>Principle library</h2>
          <p className="muted">
            Read the original Canon documents, including identity, philosophy,
            architecture, and cognitive doctrine.
          </p>
          <ResourceState resource={library} label="principle library">
            <p className="muted">
              Observed{" "}
              {library.data?.observed_at
                ? new Date(library.data.observed_at).toLocaleString()
                : "at an unreported time"}
            </p>
            <div className="workspace-toolbar">
              <label className="workspace-search">
                Find a principle
                <input
                  type="search"
                  value={query}
                  placeholder="Search titles or paths"
                  onChange={(event) => setQuery(event.target.value)}
                />
              </label>
              <label>
                Knowledge layer
                <select
                  aria-label="Knowledge layer"
                  value={layer}
                  onChange={(event) => setLayer(event.target.value)}
                >
                  <option value="all">All layers</option>
                  {[...new Set(documents.map((document) => document.layer))]
                    .sort()
                    .map((value) => (
                      <option key={value} value={value}>
                        {value}
                      </option>
                    ))}
                </select>
              </label>
            </div>
            <p>
              {visible.length} of {documents.length} documents
            </p>
            <div className="principle-list">
              {visible.map((document) => (
                <button
                  key={document.path}
                  className="connection-item"
                  aria-pressed={selected === document.path}
                  onClick={() => open(document.path)}
                >
                  {document.title}
                  <small>
                    {document.layer} · {document.path}
                  </small>
                </button>
              ))}
            </div>
            {!visible.length && (
              <p className="muted">
                No principle documents match these filters.
              </p>
            )}
          </ResourceState>
        </section>
        {selected ? (
          <PrincipleReader key={`${selected}:${readerRevision}`} path={selected} />
        ) : (
          <section className="panel">
            <p className="muted">
              Select a principle document to inspect its source.
            </p>
          </section>
        )}
      </ToolPanel>
    </div>
  );
}
