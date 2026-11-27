import { useEffect, useRef, useState } from 'react';
import { companionClient } from '../services/companionApi';
import '../styles/companion.css';

function Sources({ sources = [] }) {
  return sources.length > 0 && <details><summary>Inspect evidence ({sources.length})</summary><ul>
    {sources.map((source, index) => <li key={`${source.source_id}-${index}`}>
      <strong>{source.label || source.source_id}</strong><br />
      <code>{source.path}</code><br /><span>SHA-256: {source.sha256}</span>
    </li>)}
  </ul></details>;
}

const ID = /^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/;

function InvestigationReport({ report }) {
  const health = report.health || {};
  return <section className="companion-report" aria-label="Investigation report">
    <h3>Investigation report · {report.affected_service}</h3>
    <p>Recommendation only. Execution authority: {report.execution_authority}. Root cause: {report.root_cause.status}.</p>
    <dl>
      <dt>Report SHA-256</dt><dd><code>{report.report_sha256}</code></dd>
      <dt>Snapshot SHA-256</dt><dd><code>{report.snapshot_sha256}</code></dd>
      <dt>Evaluated at</dt><dd>{report.evaluated_at}</dd>
      {health.state && <><dt>Health</dt><dd>{health.state}{health.reason ? ` (${health.reason})` : ''}</dd></>}
    </dl>
    {report.incident_summary && <p>{report.incident_summary}</p>}
    <h4>Competing hypotheses ({report.hypotheses.length})</h4>
    {report.hypotheses.length ? <ul>{report.hypotheses.map(item => <li key={item.hypothesis_id}>
      <strong>{item.description}</strong> <small>{item.assessment_status}</small><br />
      <span>Supporting: {item.supporting_observation_ids.join(', ') || 'none'}</span><br />
      <span>Contradicting: {item.contradictory_observation_ids.join(', ') || 'none'}</span>
    </li>)}</ul> : <p>No hypothesis is supported by the selected evidence.</p>}
    <details><summary>Evidence inventory ({report.evidence_inventory.length})</summary><ul>
      {report.evidence_inventory.map(item => <li key={item.observation_id}>
        <strong>{item.observation_id}</strong> · {item.data_quality} · semantic truth {item.semantic_truth}<br />
        <span>SHA-256: {item.record_sha256}</span>
      </li>)}
    </ul></details>
    <h4>Unresolved questions</h4><ul>{report.unresolved_questions.map(text => <li key={text}>{text}</li>)}</ul>
    <h4>Recommended next diagnostic steps</h4><ul>{report.recommended_next_diagnostic_steps.map(text => <li key={text}>{text}</li>)}</ul>
    <p>Conversation follow-ups are not bound to this report: the Companion API does not yet accept a report reference.</p>
  </section>;
}

export default function Companion({ client = companionClient }) {
  const [history, setHistory] = useState([]);
  const [conversation, setConversation] = useState(null);
  const [capabilities, setCapabilities] = useState([]);
  const [text, setText] = useState('');
  const [tone, setTone] = useState('direct');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [selection, setSelection] = useState({ service: '', incident: '', observations: '' });
  const [report, setReport] = useState(null);
  const [investigating, setInvestigating] = useState(false);
  const pending = useRef(null);
  const epoch = useRef(0);

  useEffect(() => {
    if (!client) return;
    const controller = new AbortController();
    pending.current = controller;
    Promise.all([client.list(controller.signal), client.capabilities(controller.signal)]).then(([list, snapshot]) => {
      if (!controller.signal.aborted) { setHistory(list.conversations); setCapabilities(snapshot.capabilities); }
    }).catch(err => { if (!controller.signal.aborted) setError(err.message); });
    return () => { controller.abort(); pending.current?.abort(); epoch.current += 1; };
  }, [client]);

  async function perform(operation) {
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    const version = ++epoch.current;
    setBusy(true); setError(''); setNotice('');
    try {
      await operation(controller.signal, () => !controller.signal.aborted && version === epoch.current);
    } catch (err) {
      if (!controller.signal.aborted && version === epoch.current) setError(err.message);
    } finally {
      if (version === epoch.current) setBusy(false);
    }
  }
  async function refresh(signal, current) {
    const list = await client.list(signal);
    if (current()) setHistory(list.conversations);
  }
  function cancel() {
    pending.current?.abort(); epoch.current += 1; setBusy(false);
    setNotice('Request cancelled in this browser. A submitted turn may have completed; refresh history before retrying.');
  }
  function select(id) {
    setText(''); setConversation(null);
    perform(async (signal, current) => { const result = await client.get(id, signal); if (current()) setConversation(result); });
  }
  function send(event) {
    event.preventDefault();
    if (!conversation || !text.trim() || busy) return;
    const message = text.trim();
    perform(async (signal, current) => {
      const result = await client.turn(conversation.conversation_id, {
        turn_id: crypto.randomUUID(), text: message, expected_revision: conversation.revision,
      }, signal);
      if (current()) { setConversation(result); setText(''); }
      await refresh(signal, current);
    });
  }
  function investigate(event) {
    event.preventDefault();
    if (busy) return;
    const service = selection.service.trim(), incident = selection.incident.trim();
    const observations = selection.observations.split(/[\s,]+/).filter(Boolean);
    const invalid = [service, incident, ...observations].filter(Boolean).find(value => !ID.test(value));
    if (!service) { setError('Select a service identifier to investigate.'); return; }
    if (invalid) { setError(`Identifier is not valid: ${invalid.slice(0, 40)}`); return; }
    if (observations.length > 100) { setError('Select at most 100 observations.'); return; }
    setReport(null);
    perform(async (signal, current) => {
      const result = await client.investigate({ service_id: service, evaluated_at: new Date().toISOString(),
        ...(incident ? { incident_id: incident } : {}), ...(observations.length ? { observation_ids: observations } : {}) }, signal);
      if (current()) setReport(result);
    });
  }
  const field = key => event => setSelection(value => ({ ...value, [key]: event.target.value }));
  return <section className="workspace-page companion" aria-label="Sentinel companion">
    <article className="panel"><p className="eyebrow">Sentinel companion · local opt-in</p>
      <h2>Discuss, inspect, investigate</h2>
      <p>Evidence-grounded discussion and diagnostic recommendations. Conversation does not authorize execution.</p>
      <p>Responses appear after validation. Live model quality is not established by offline tests.</p>
    </article>
    {!client ? <article className="panel" role="status">Companion is disabled. Configure the approved local companion service to use conversations.</article> : <>
      {error && <p role="alert" className="workspace-error">{error}</p>}
      <p role="status" aria-live="polite">{busy ? 'Waiting for a governed response…' : notice}</p>
      {busy && <button className="secondary-action" type="button" onClick={cancel}>Cancel request</button>}
      <div className="companion-grid">
        <aside className="panel" aria-label="Conversation history">
          <h3>Conversations</h3>
          <p>Investigate explicitly selected evidence in the investigation panel.</p>
          <label htmlFor="companion-tone">New conversation tone</label>
          <select id="companion-tone" value={tone} onChange={event => setTone(event.target.value)} disabled={busy}>
            <option value="direct">Direct</option><option value="friendly">Friendly</option><option value="technical">Technical</option>
          </select>
          <button className="secondary-action" type="button" disabled={busy} onClick={() => perform(async (signal, current) => {
            const result = await client.create(tone, signal);
            if (current()) { setConversation(result); setText(''); }
            await refresh(signal, current);
          })}>New conversation</button>
          <button className="secondary-action" type="button" disabled={busy} onClick={() => perform(async (signal, current) => {
            setConversation(null); setText(''); await refresh(signal, current);
          })}>Refresh history</button>
          <ul>{history.map(item => <li key={item.conversation_id}><button type="button" disabled={busy}
            aria-current={conversation?.conversation_id === item.conversation_id ? 'true' : undefined}
            onClick={() => select(item.conversation_id)}>{item.title || 'Untitled conversation'}</button></li>)}</ul>
          {!history.length && <p>No conversations returned for this operator.</p>}
        </aside>
        <article className="panel companion-thread" aria-label="Current conversation">
          {!conversation ? <p>Select or create a conversation to begin.</p> : <>
            <h3>{conversation.title || 'Conversation'}</h3>
            {conversation.summary && <details><summary>Conversation context summary</summary><p>{conversation.summary}</p><p>Conversation context is not verified operational evidence.</p></details>}
            <ol className="companion-messages" aria-label="Messages">{(conversation.messages || []).map((message, index) =>
              <li key={`${message.turn_id}-${index}`} className={`companion-message companion-${message.role === 'user' ? 'user' : 'assistant'}`}>
                <h4>{message.role === 'user' ? 'You' : 'Sentinel'}</h4>
                <p>{message.content}</p><small>{message.status}</small><Sources sources={message.sources} />
              </li>)}</ol>
            <form className="workspace-form" onSubmit={send}><label htmlFor="companion-message">Message Sentinel
              <textarea id="companion-message" value={text} maxLength={4000} disabled={busy}
                onChange={event => setText(event.target.value)} placeholder="Ask about verified architecture and capabilities" /></label>
              <button className="primary-action" disabled={busy || !text.trim()} type="submit">Send message</button>
            </form>
            <button className="secondary-action" disabled={busy} type="button" onClick={() => perform(async (signal, current) => {
              await client.remove(conversation.conversation_id, signal);
              if (current()) { setConversation(null); setText(''); setNotice('Conversation deleted.'); }
              await refresh(signal, current);
            })}>Delete this conversation</button>
          </>}
        </article>
      </div>
      <article className="panel" aria-label="Investigate selected evidence">
        <h3>Investigate selected evidence</h3>
        <button className="secondary-action" type="button" aria-expanded={investigating}
          onClick={() => setInvestigating(open => !open)}>{investigating ? 'Close investigation' : 'Open investigation'}</button>
        {investigating && <>
        <p>Explicit selection only: name the service, then an incident or specific observations. Sentinel reviews only what you select and never declares a root cause.</p>
        <form className="workspace-form" onSubmit={investigate}>
          <label htmlFor="investigate-service">Service identifier
            <input id="investigate-service" value={selection.service} maxLength={128} disabled={busy} onChange={field('service')} /></label>
          <label htmlFor="investigate-incident">Incident identifier (optional)
            <input id="investigate-incident" value={selection.incident} maxLength={128} disabled={busy} onChange={field('incident')} /></label>
          <label htmlFor="investigate-observations">Observation identifiers (optional, comma or space separated)
            <textarea id="investigate-observations" value={selection.observations} maxLength={13000} disabled={busy} onChange={field('observations')} /></label>
          <button className="primary-action" type="submit" disabled={busy || !selection.service.trim()}>Run investigation</button>
        </form>
        {report && <InvestigationReport report={report} />}
        </>}
      </article>
      <details className="panel"><summary>Inspect capability evidence</summary><p>Implementation and authorization are separate. Listed capabilities are server-reported records.</p>
        {capabilities.map((capability, index) => <section key={capability.capability_id || index}>
          <h3>{capability.name || capability.capability_id}</h3><p>{capability.description}</p>
          <p>Implementation: {capability.implementation_status || 'UNKNOWN'} · Authorization: {capability.authorization_status || 'UNKNOWN'}</p>
          <Sources sources={capability.evidence_references || capability.sources || []} />
        </section>)}
      </details>
    </>}
  </section>;
}
