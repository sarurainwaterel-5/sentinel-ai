import { BrainCircuit } from "lucide-react";
export default function ReasonQuestion({ question, setQuestion, isReasoning, onSubmit, error,
  topic, setTopic, limit, setLimit, scoreThreshold, setScoreThreshold, domainName, onCancel, onNavigate }) {
  return <article className="panel reason-mission-card">
    <div className="reason-section-heading"><div className="reason-section-icon"><BrainCircuit size={20} aria-hidden="true" /></div><div><p className="eyebrow">Reasoning Mission</p><h2>What should Sentinel reason about?</h2></div></div>
    <p className="muted">Examine taught evidence, inspect bounded inferences, and assess evidentiary confidence. Constitutional semantic evaluation remains independently unverified.</p>
    <p>Evidence scope: <strong>{domainName}</strong></p>
    <form className="reason-question-form" onSubmit={onSubmit}>
      <label htmlFor="reason-question">Question</label>
      <textarea id="reason-question" value={question} maxLength={10000} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask Sentinel to analyze an evidence-grounded question…" disabled={isReasoning} rows={5} required />
      <details><summary>Evidence retrieval settings</summary><div className="workspace-form">
        <label>Topic filter<input value={topic} maxLength={200} disabled={isReasoning} onChange={(event) => setTopic(event.target.value)} placeholder="Optional exact topic" /></label>
        <label>Maximum evidence chunks<input type="number" required min={1} max={25} step={1} value={limit} disabled={isReasoning} onChange={(event) => setLimit(event.target.value)} /></label>
        <label>Minimum retrieval similarity<input type="number" required min={0} max={1} step={0.01} value={scoreThreshold} disabled={isReasoning} onChange={(event) => setScoreThreshold(event.target.value)} /></label>
        <p className="muted">Similarity controls retrieval relevance; it is not confidence or semantic acceptance. Topic is an exact metadata filter. All Domains permits cross-domain retrieval.</p>
      </div></details>
      {error && <p className="reason-error" role="alert">{error}</p>}
      <div className="reason-question-actions"><button type="submit" className="primary-action" disabled={isReasoning || !question.trim()}><BrainCircuit size={18} aria-hidden="true" /><span>{isReasoning ? "Analyzing Evidence…" : "Analyze Evidence"}</span></button>
        {isReasoning && <button type="button" className="secondary-action" onClick={onCancel}>Stop waiting</button>}
      </div>
    </form>
    <p className="muted">Recommendations require human review and never grant execution authority.</p>
    <button className="secondary-action" onClick={() => onNavigate?.("systems")}>Inspect Systems</button>
  </article>;
}
