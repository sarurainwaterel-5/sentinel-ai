import { useMemo, useState } from "react";
import { useDomain } from "../context/useDomain";
import { useWorkspaceData } from "../components/workspaces/useWorkspaceData";
import {
  ResourceState,
  WorkspaceHeader,
  WorkspaceTabs,
  ToolPanel,
} from "../components/workspaces/WorkspaceParts";
import CognitiveOperation from "../components/workspaces/CognitiveOperation";
import { workspaceRequest } from "../services/workspaceApi";

function Connections() {
  const resource = useWorkspaceData("/intelligence/connections");
  const [query, setQuery] = useState("");
  const [relationship, setRelationship] = useState("all");
  const [view, setView] = useState("List");
  const [selected, setSelected] = useState(null);
  const nodes = useMemo(
    () => new Map((resource.data?.nodes ?? []).map((node) => [node.id, node])),
    [resource.data],
  );
  const documents = (resource.data?.nodes ?? []).filter(
    (node) =>
      node.path &&
      `${node.title} ${node.path}`.toLowerCase().includes(query.toLowerCase()),
  );
  const edges = (resource.data?.edges ?? []).filter(
    (edge) =>
      (edge.source === selected || edge.target === selected) &&
      (relationship === "all" || relationship === edge.relationship),
  );
  const unresolved = (resource.data?.unresolved_references ?? []).filter(
    (reference) => reference.source === selected,
  );
  return (
    <section className="panel">
      <h2>Explore connections</h2>
      <p className="muted">
        Inspect documented relationships across Sentinel’s principles and
        architecture.
      </p>
      <ResourceState resource={resource} label="connections">
        <p>
          {resource.data?.nodes.filter((node) => node.path).length} principle
          documents · {resource.data?.edges.length} documented connections
        </p>
        <details>
          <summary>How connections are established</summary>
          <p>{resource.data?.limitation}</p>
        </details>
        <label className="workspace-search">
          Find a principle document
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
        <div className="workspace-toolbar">
          <label>
            Relationship
            <select
              aria-label="Relationship"
              value={relationship}
              onChange={(event) => setRelationship(event.target.value)}
            >
              <option value="all">All relationships</option>
              {[
                ...new Set(
                  (resource.data?.edges ?? []).map((edge) => edge.relationship),
                ),
              ].map((type) => (
                <option key={type} value={type}>
                  {type.replaceAll("_", " ")}
                </option>
              ))}
            </select>
          </label>
          <label>
            View
            <select
              aria-label="View"
              value={view}
              onChange={(event) => setView(event.target.value)}
            >
              <option>List</option>
              <option>Map</option>
            </select>
          </label>
        </div>
        <div className="connection-explorer">
          <div
            className="connection-documents"
            aria-label="Principle documents"
          >
            {documents.map((node) => (
              <button
                className="connection-item"
                aria-pressed={selected === node.id}
                key={node.id}
                onClick={() => setSelected(node.id)}
              >
                {node.title}
                <small>{node.path}</small>
              </button>
            ))}
            {!documents.length && <p>No matching principle documents.</p>}
          </div>
          <div className="connection-detail">
            {selected ? (
              <>
                <h3>{nodes.get(selected)?.title}</h3>
                <p className="muted">{nodes.get(selected)?.path}</p>
                <h4>Observed connections</h4>
                {view === "Map" && (
                  <div
                    className="connection-map"
                    aria-label="Local relationship map"
                  >
                    <strong>{nodes.get(selected)?.title}</strong>
                    {edges.map((edge, index) => {
                      const other =
                        edge.source === selected ? edge.target : edge.source;
                      return (
                        <div key={index}>
                          <span>
                            {edge.source === selected ? "→" : "←"}{" "}
                            {edge.relationship.replaceAll("_", " ")}
                          </span>
                          <button
                            className="secondary-action"
                            onClick={() => setSelected(other)}
                          >
                            {nodes.get(other)?.title}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                )}
                {!edges.length && (
                  <p className="muted">
                    No connections match this relationship filter.
                  </p>
                )}
                {view === "List" &&
                  edges.map((edge, index) => (
                    <div className="connection-edge" key={index}>
                      <button
                        className="connection-link"
                        onClick={() => setSelected(edge.source)}
                      >
                        {nodes.get(edge.source)?.title}
                      </button>
                      <span>{edge.relationship.replaceAll("_", " ")}</span>
                      <button
                        className="connection-link"
                        onClick={() => setSelected(edge.target)}
                      >
                        {nodes.get(edge.target)?.title}
                      </button>
                      <small>Basis: {edge.basis}</small>
                    </div>
                  ))}
                {unresolved.length > 0 && <h4>Unresolved references</h4>}
                {unresolved.map((reference, index) => (
                  <p key={index}>
                    {reference.reference} ·{" "}
                    {reference.reason.replaceAll("_", " ")}
                  </p>
                ))}
              </>
            ) : (
              <p className="muted">
                Select a document to inspect its connections and unresolved
                references.
              </p>
            )}
          </div>
        </div>
      </ResourceState>
    </section>
  );
}

function Reflection({ onTeach }) {
  const { activeDomain } = useDomain();
  const events = useWorkspaceData("/intelligence/learning-events");
  const history = useWorkspaceData("/reflection/history");
  const [selected, setSelected] = useState([]);
  const [title, setTitle] = useState("Patterns in recent learning");
  const [operation, setOperation] = useState({
    pending: false,
    error: null,
    result: null,
  });
  const visible = (events.data ?? []).filter(
    (event) =>
      activeDomain?.id === "all" ||
      !activeDomain?.id ||
      event.domain_ids.includes(activeDomain.id),
  );
  const visibleIds = new Set(visible.map((event) => event.learning_event_id));
  const ids = selected.filter((id) => visibleIds.has(id));
  async function reflect(event) {
    event.preventDefault();
    if (!ids.length || !title.trim() || operation.pending) return;
    setOperation({ pending: true, error: null, result: null });
    try {
      const result = await workspaceRequest("/intelligence/reflection", {
        method: "POST",
        body: { title: title.trim(), learning_event_ids: ids },
      });
      setOperation({ pending: false, error: null, result });
      history.refresh();
    } catch (error) {
      setOperation({ pending: false, error: error.message, result: null });
    }
  }
  return (
    <section className="panel">
      <h2>Reflect on recorded learning</h2>
      <p className="muted">
        Discover patterns from authoritative Learning Events. Historical
        reflections remain append-only, including rejected and insufficient
        outcomes.
      </p>
      <ResourceState resource={events} label="learning history">
        <form className="workspace-form" onSubmit={reflect}>
          <label>
            Reflection title
            <input
              required
              value={title}
              maxLength={500}
              onChange={(event) => setTitle(event.target.value)}
              disabled={operation.pending}
            />
          </label>
          {visible.map((event) => (
            <label className="event-choice" key={event.learning_event_id}>
              <input
                type="checkbox"
                checked={ids.includes(event.learning_event_id)}
                disabled={operation.pending}
                onChange={(change) =>
                  setSelected((values) =>
                    change.target.checked
                      ? [...values, event.learning_event_id]
                      : values.filter((id) => id !== event.learning_event_id),
                  )
                }
              />
              <span>
                <strong>{event.summary || event.source}</strong>
                <small>
                  {event.learned_at} · {event.domain_ids.join(", ")}
                </small>
              </span>
            </label>
          ))}
          {!visible.length && (
            <p className="muted">
              No Learning Events are recorded in this scope. Teach Sentinel a
              document before reflecting.
            </p>
          )}
          {!visible.length && (
            <button
              type="button"
              className="secondary-action"
              onClick={onTeach}
            >
              Teach Sentinel a document
            </button>
          )}
          <button
            className="primary-action"
            disabled={!ids.length || !title.trim() || operation.pending}
          >
            {operation.pending ? "Reflecting…" : "Reflect on selected history"}
          </button>
        </form>
      </ResourceState>
      {operation.error && (
        <p role="alert" className="workspace-error">
          {operation.error}
        </p>
      )}
      {operation.result && (
        <div className="workspace-result">
          <h3>{operation.result.status.replaceAll("_", " ")}</h3>
          <p>
            {operation.result.pattern_count} patterns ·{" "}
            {operation.result.insight_count} insights ·{" "}
            {operation.result.recommendation_count} recommendations
          </p>
          <p>
            Confidence: {operation.result.reflection_confidence_level} ·
            Constitutional admissibility:{" "}
            {operation.result.admissible
              ? "Reported admissible"
              : "Not verified"}
          </p>
          <pre className="reflection-report">
            {operation.result.formatted_reflection}
          </pre>
          <p className="workspace-notice">
            Recommendations do not grant execution authority.
          </p>
        </div>
      )}
      <h3>Recent reflection history</h3>
      <ResourceState resource={history} label="reflection history">
        {history.data?.map((record) => (
          <details key={record.reflection_id}>
            <summary>
              {record.reflected_at} · {record.status.replaceAll("_", " ")}
            </summary>
            <p>
              Confidence: {record.reflection_confidence_level} · Admissible:{" "}
              {record.admissible ? "Yes" : "No"}
            </p>
            <p>
              {record.pattern_ids.length} patterns · {record.insight_ids.length}{" "}
              insights
            </p>
            <p className="muted">
              Learning provenance: {record.learning_event_ids.join(", ")}
            </p>
            <p className="muted">Record: {record.reflection_id}</p>
          </details>
        ))}
        {history.data?.length === 0 && (
          <p className="muted">No reflections have been recorded yet.</p>
        )}
      </ResourceState>
    </section>
  );
}

export default function Intelligence({ onTeach }) {
  const [active, setActive] = useState("Connections");
  return (
    <div className="page workspace-page">
      <WorkspaceHeader
        title="Connect knowledge, then consider what follows"
        description="Observe relationships, reflect on recorded learning, and propose evidence-aware plans."
      />
      <WorkspaceTabs
        tabs={["Connections", "Reflection", "Planning"]}
        active={active}
        onChange={setActive}
      />
      <ToolPanel name="Connections" active={active}>
        <Connections />
      </ToolPanel>
      <ToolPanel name="Reflection" active={active}>
        <Reflection onTeach={onTeach} />
      </ToolPanel>
      <ToolPanel name="Planning" active={active}>
        <CognitiveOperation kind="plan" />
      </ToolPanel>
    </div>
  );
}
