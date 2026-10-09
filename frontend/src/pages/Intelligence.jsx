import { useMemo, useState } from "react";
import { useDomain } from "../context/useDomain";
import { useWorkspaceData } from "../components/workspaces/useWorkspaceData";
import {
  ResourceState,
  WorkspaceHeader,
} from "../components/workspaces/WorkspaceParts";
import CognitiveOperation from "../components/workspaces/CognitiveOperation";
import { workspaceRequest } from "../services/workspaceApi";

function Connections() {
  const resource = useWorkspaceData("/intelligence/connections");
  const [query, setQuery] = useState("");
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
    (edge) => edge.source === selected || edge.target === selected,
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
        <p className="workspace-notice">{resource.data?.limitation}</p>
        <label className="workspace-search">
          Find a principle document
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>
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
                {edges.map((edge, index) => (
                  <div className="connection-edge" key={index}>
                    <strong>{nodes.get(edge.source)?.title}</strong>
                    <span>{edge.relationship.replaceAll("_", " ")}</span>
                    <strong>{nodes.get(edge.target)?.title}</strong>
                    <small>Basis: {edge.basis}</small>
                  </div>
                ))}
                <h4>Unresolved references</h4>
                {unresolved.map((reference, index) => (
                  <p key={index}>
                    {reference.reference} ·{" "}
                    {reference.reason.replaceAll("_", " ")}
                  </p>
                ))}
                {!unresolved.length && (
                  <p className="muted">
                    No unresolved references recorded for this document.
                  </p>
                )}
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

function Reflection() {
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

export default function Intelligence() {
  return (
    <div className="page workspace-page">
      <WorkspaceHeader
        title="Connect knowledge, then consider what follows"
        description="Observe relationships, reflect on recorded learning, and propose evidence-aware plans."
      />
      <Connections />
      <Reflection />
      <CognitiveOperation kind="plan" />
    </div>
  );
}
