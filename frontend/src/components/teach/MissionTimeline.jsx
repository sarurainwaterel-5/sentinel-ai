const stages = [
  ["received", "Receive source"],
  ["fingerprinting", "Check duplicate knowledge"],
  ["extracting", "Extract document text"],
  ["transcribing", "Transcribe video speech"],
  ["chunking", "Prepare memory chunks"],
  ["indexing", "Embed and store memory"],
  ["cataloging", "Save document catalog"],
  ["recording", "Record acquisition history"],
];

export default function MissionTimeline({ mission }) {
  const current = stages.findIndex(([id]) => id === mission?.stage);
  const finished = ["completed", "duplicate", "failed", "interrupted", "stored"].includes(mission?.status);
  const events = mission?.events ?? [];
  return <section className="panel">
    <p className="eyebrow">Observed progress</p><h2>Mission Timeline</h2>
    {!mission ? <p className="muted">Select files and begin teaching to activate the timeline.</p> : <>
      <p><strong>{mission.filename}</strong> · {mission.domain_id} · <span role="status">{mission.status}</span></p>
      {mission.status === "stored" && <p>Source stored. It has not been indexed and does not establish learned knowledge.</p>}
      {mission.error && <p role="alert" className="workspace-error">{mission.error}</p>}
      {mission.status === "queued" && <p>Source received. Waiting for the local ingestion worker.</p>}
      {mission.status === "duplicate" && <p>This source is already cataloged in {mission.result?.existing_document?.module}. No new memories or Learning Event were created. Use Governance if it needs restoring.</p>}
      {mission.result?.relative_path && <p className="muted">Source folder: {mission.result.relative_path}</p>}
      {mission.result?.warnings?.length > 0 && <ul aria-label="Source processing notes" className="workspace-notice">{mission.result.warnings.map((warning, index) => <li key={index}>{String(warning).replaceAll("_", " ")}</li>)}</ul>}
      {mission.result?.history_warning && <p className="workspace-notice">{mission.result.history_warning}</p>}
    </>}
    <ol className="mission-steps">{stages.map(([id, title], index) => {
      const event = events.find((item) => item.stage === id);
      const observed = Boolean(event);
      const done = observed && (mission?.status === "completed" || (finished && index < current) || events.some((item) => stages.findIndex(([stage]) => stage === item.stage) > index) || (id === "received" && mission?.status === "duplicate"));
      const state = id === "recording" && mission?.result?.history_warning ? "Needs attention" : done ? "Complete" : mission?.stage === id && !finished ? "In progress" : observed ? "Reached" : finished ? "Not run" : "Waiting";
      return <li key={id} className={`mission-step ${done ? "mission-complete" : ""}`}><span className="timeline-dot">{index + 1}</span><div><strong>{title}</strong><p className="muted">{state}{event?.at ? ` · ${new Date(event.at).toLocaleTimeString()}` : ""}</p></div></li>;
    })}</ol>
    <p className="muted">Stages reflect server observations, not simulated percentages. Memory acquisition does not establish understanding or semantic acceptance.</p>
    {mission && <details><summary>Inspect recorded mission events</summary><ul className="workspace-list">{events.map((event, index) => <li key={index}>{event.stage} · {new Date(event.at).toLocaleString()}{event.detail && <p>{event.detail}</p>}</li>)}</ul><p className="muted">Mission ID: {mission.id}</p></details>}
  </section>;
}
