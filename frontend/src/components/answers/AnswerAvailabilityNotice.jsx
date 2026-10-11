import { useEffect, useState } from "react";
import { getGovernedAnswerReadiness } from "../../services/governedAnswerApi";

export default function AnswerAvailabilityNotice() {
  const [status, setStatus] = useState({ loading: true });
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      setStatus({ error: "Readiness timed out. Answering remains disabled." });
      controller.abort();
    }, 10000);
    getGovernedAnswerReadiness(controller.signal).then(result => {
      if (!controller.signal.aborted) setStatus({ result });
    }).catch(error => {
      if (!controller.signal.aborted) setStatus({ error: error.message });
    }).finally(() => clearTimeout(timer));
    return () => { clearTimeout(timer); controller.abort(); };
  }, [attempt]);
  return <aside className="panel" aria-label="Governed answer availability">
    <p className="eyebrow">Governed answers</p>
    <h2>Production answering is disabled</h2>
    <p>This Sprint 21 capability awaits semantic benchmark and answer presentation acceptance. Existing Reason remains a separate workflow.</p>
    <p role="status">{status.loading ? "Checking readiness…" : status.error || "Release gate is closed. No generated answer or execution is authorized."}</p>
    {status.result && <details><summary>Inspect release blockers</summary><ul>{status.result.blockers.map(value => <li key={value}>{value.replaceAll("_", " ")}</li>)}</ul></details>}
    {status.error && <button className="secondary-action" onClick={() => { setStatus({ loading: true }); setAttempt(value => value + 1); }}>Retry readiness</button>}
  </aside>;
}
