// Explicit local opt-in; never falls back to the production API URL.
const configuredBase = import.meta.env.VITE_COMPANION_API_URL;
export function createCompanionClient(base = configuredBase, transport = fetch) {
  if (!base) return null;
  const parsed = new URL(base, window.location.origin);
  if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password || parsed.search || parsed.hash)
    throw new Error('Invalid companion service configuration.');
  const prefix = `${parsed.href.replace(/\/+$/, '')}/companion/v1`;
  async function request(path, { method = 'GET', body, signal } = {}) {
    let response;
    try {
      response = await transport(`${prefix}${path}`, { method, signal, credentials: 'same-origin',
        ...(body ? { headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) } : {}) });
    } catch (error) {
      if (error.name === 'AbortError') throw error;
      throw new Error('Companion service could not be reached. Check the local service and retry.', { cause: error });
    }
    if (!response.ok) throw new Error(response.status === 401 || response.status === 403 ?
      'This conversation is unavailable for the current operator.' : 'Companion request failed. Refresh history before retrying.');
    if (response.status === 204) return null;
    try { return await response.json(); } catch { throw new Error('Companion returned an unreadable response.'); }
  }
  const sourcesValid = sources => Array.isArray(sources) && sources.length <= 256 && sources.every(source =>
    source && ['source_id', 'label', 'path', 'sha256'].every(key => typeof source[key] === 'string'));
  const conversationValid = value => value && typeof value.conversation_id === 'string' &&
    Number.isInteger(value.revision) && value.revision >= 0 &&
    (!value.messages || (Array.isArray(value.messages) && value.messages.length <= 1024 && value.messages.every(message =>
      ['user', 'assistant'].includes(message.role) && typeof message.content === 'string' &&
      (!message.sources || sourcesValid(message.sources)))));
  async function checked(promise, validate) {
    const value = await promise;
    if (!validate(value)) throw new Error('Companion response failed validation. Refresh history before retrying.');
    return value;
  }
  // Investigation reports are recommendation-only. A report that names a root cause, claims
  // execution authority, lacks its canonical hashes or covers another service is withheld.
  const HASH = /^[0-9a-f]{64}$/;
  const strings = (list, max) => Array.isArray(list) && list.length <= max && list.every(item => typeof item === 'string');
  const reportValid = (value, serviceId) => value && typeof value === 'object' &&
    HASH.test(value.report_sha256) && HASH.test(value.snapshot_sha256) &&
    value.affected_service === serviceId && typeof value.evaluated_at === 'string' &&
    value.root_cause?.status === 'WITHHELD' && value.execution_authority === 'NONE' &&
    Array.isArray(value.hypotheses) && value.hypotheses.length <= 64 && value.hypotheses.every(item =>
      item && typeof item.hypothesis_id === 'string' && typeof item.description === 'string' &&
      typeof item.assessment_status === 'string' && strings(item.supporting_observation_ids, 100) &&
      strings(item.contradictory_observation_ids, 100)) &&
    Array.isArray(value.evidence_inventory) && value.evidence_inventory.length <= 100 && value.evidence_inventory.every(item =>
      item && typeof item.observation_id === 'string' && HASH.test(item.record_sha256)) &&
    Array.isArray(value.timeline) && value.timeline.length <= 100 &&
    strings(value.unresolved_questions, 32) && strings(value.recommended_next_diagnostic_steps, 32);
  const path = id => `/conversations/${encodeURIComponent(id)}`;
  return {
    capabilities: signal => checked(request('/capabilities', { signal }), value =>
      Array.isArray(value?.capabilities) && value.capabilities.length <= 1024 && value.capabilities.every(item =>
        item && typeof item.capability_id === 'string' && (!item.sources || sourcesValid(item.sources)) &&
        (!item.evidence_references || sourcesValid(item.evidence_references)))),
    list: signal => checked(request('/conversations', { signal }), value =>
      Array.isArray(value?.conversations) && value.conversations.length <= 1024 && value.conversations.every(conversationValid)),
    create: (tone, signal) => checked(request('/conversations', { method: 'POST', body: { tone }, signal }), conversationValid),
    get: (id, signal) => checked(request(path(id), { signal }), value => conversationValid(value) && value.conversation_id === id),
    remove: (id, signal) => request(path(id), { method: 'DELETE', signal }),
    turn: (id, body, signal) => checked(request(`${path(id)}/turns`, { method: 'POST', body, signal }),
      value => conversationValid(value) && value.conversation_id === id),
    // Explicit selection only: a service, plus an incident or specific observations.
    investigate: (selection, signal) => checked(request('/investigations', { method: 'POST', body: selection, signal }),
      value => reportValid(value, selection.service_id)),
  };
}
export const companionClient = createCompanionClient();
