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

export default function Companion({ client = companionClient }) {
  const [history, setHistory] = useState([]);
  const [conversation, setConversation] = useState(null);
  const [capabilities, setCapabilities] = useState([]);
  const [text, setText] = useState('');
  const [tone, setTone] = useState('direct');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
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
          <p>Incident investigation currently requires explicit selection through the local investigation API.</p>
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
