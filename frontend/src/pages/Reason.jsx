import { useEffect, useRef, useState } from "react";
import ReasonLoading from "../components/reason/ReasonLoading";
import ReasonQuestion from "../components/reason/ReasonQuestion";
import ReasonResult from "../components/reason/ReasonResult";
import { useDomain } from "../context/useDomain";
import { reasonAbout } from "../services/reasonApi";

const storageKey = "sentinel.reasonWorkspace";
function savedWorkspace() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(storageKey) || "null");
    if (!saved || typeof saved.question !== "string") return {};
    if (saved.report && (!saved.report.request || typeof saved.report.request.question !== "string" || !saved.report.result?.reasoning)) saved.report = null;
    return saved;
  } catch { return {}; }
}

export default function Reason({ onNavigate }) {
  const { activeDomain } = useDomain();
  const [saved] = useState(savedWorkspace);
  const [question, setQuestion] = useState(saved.question ?? "");
  const [topic, setTopic] = useState(saved.topic ?? "");
  const [limit, setLimit] = useState(saved.limit ?? 5);
  const [scoreThreshold, setScoreThreshold] = useState(saved.scoreThreshold ?? 0.45);
  const [report, setReport] = useState(saved.report?.result?.reasoning ? saved.report : null);
  const [error, setError] = useState(null);
  const [isReasoning, setIsReasoning] = useState(false);
  const controllerRef = useRef(null);
  useEffect(() => () => { const controller = controllerRef.current; controllerRef.current = null; controller?.abort(); }, []);
  useEffect(() => {
    try { sessionStorage.setItem(storageKey, JSON.stringify({ question, topic, limit, scoreThreshold, report })); }
    catch { /* A full browser store must not prevent reasoning. */ }
  }, [question, topic, limit, scoreThreshold, report]);

  async function handleReason(event) {
    event.preventDefault();
    if (isReasoning) return;
    const normalized = question.trim();
    if (!normalized || normalized.length > 10000) { setError("Enter a question between 1 and 10,000 characters."); return; }
    if (!Number.isInteger(Number(limit)) || Number(limit) < 1 || Number(limit) > 25 || String(scoreThreshold).trim() === "" || !Number.isFinite(Number(scoreThreshold)) || Number(scoreThreshold) < 0 || Number(scoreThreshold) > 1) {
      setError("Choose 1–25 evidence chunks and a retrieval threshold between 0 and 1."); return;
    }
    const request = { question: normalized, workspace: "reason", module: activeDomain?.id !== "all" ? activeDomain?.id ?? null : null,
      topic: topic.trim() || null, limit: Number(limit), scoreThreshold: Number(scoreThreshold), missionId: crypto.randomUUID() };
    const controller = new AbortController(); controllerRef.current = controller;
    let timedOut = false;
    const timer = setTimeout(() => { timedOut = true; controller.abort(); }, 180000);
    setError(null); setIsReasoning(true);
    try {
      const response = await reasonAbout({ ...request, signal: controller.signal });
      if (!controller.signal.aborted) setReport({ result: response, request, domainName: activeDomain?.name ?? "All Domains", observedAt: new Date().toISOString() });
    } catch (err) {
      if (controllerRef.current === controller) setError(controller.signal.aborted
        ? timedOut ? "Reasoning exceeded the local waiting limit. The backend may still finish; review Systems before retrying." : "Stopped waiting for this request. Backend processing may still finish; no action was authorized."
        : err instanceof Error ? err.message : "Sentinel could not complete reasoning.");
    } finally {
      clearTimeout(timer);
      if (controllerRef.current === controller) { controllerRef.current = null; setIsReasoning(false); }
    }
  }
  const cancel = () => controllerRef.current?.abort();
  const differentScope = report && (report.request.module ?? "all") !== (activeDomain?.id ?? "all");
  return <section className="reason-workspace workspace-page">
    <ReasonQuestion question={question} setQuestion={setQuestion} isReasoning={isReasoning} onSubmit={handleReason} error={error}
      topic={topic} setTopic={setTopic} limit={limit} setLimit={setLimit} scoreThreshold={scoreThreshold} setScoreThreshold={setScoreThreshold}
      domainName={activeDomain?.name ?? "All Domains"} onCancel={cancel} onNavigate={onNavigate} />
    {isReasoning && <ReasonLoading />}
    {report && <>
      <article className="panel reason-report-context"><p className="eyebrow">Last completed report</p>
        <h2>{report.request.question}</h2><p>{report.domainName} · {report.request.topic || "All topics"} · {new Date(report.observedAt).toLocaleString()}</p>
        <p className="muted">This report uses the scope captured at submission. It is retained in this browser tab; submitting another question does not rewrite it until a new result arrives.</p>
        {differentScope && <p className="workspace-notice">The current domain differs from this report. Submit a new mission to reason in the current context.</p>}
        <details><summary>Inspect mission context</summary><p>Mission: {report.result.mission_id ?? report.request.missionId}</p><p>Evidence limit: {report.request.limit} · Minimum similarity: {report.request.scoreThreshold}</p></details>
        <button className="secondary-action" disabled={isReasoning} onClick={() => setReport(null)}>Clear report</button>
      </article>
      <ReasonResult result={report.result} onNavigate={onNavigate} />
    </>}
  </section>;
}
