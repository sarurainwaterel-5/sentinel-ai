"""Explicit operator-run actual-corpus inspection; never an HTTP answer route.

Relationship descriptions are operator-supplied hypotheses assessed by the judge,
not automatically established semantic facts. Calls require an explicitly supplied
real transport. SQL publication and checked read precede any candidate rendering.
"""
import hashlib
import html

from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticRelationshipText
from app.services.governed_authentication import GovernedAuthenticationSession, AuthenticatedGovernedPrincipal
from .catalog_index_reconciler import CatalogIndexReconciler
from .live_provider_rehearsal import canonical
from .transactional_inspection_publication import InspectionPublicationBarrier, PublicationDenied


class CorpusInspectionWithheld(PublicationDenied):
    """Candidate-free operational outcome; never a partial review artifact."""
    def __init__(self, reason, attempted_calls):
        self.reason = reason
        self.attempted_calls = attempted_calls
        super().__init__('corpus_inspection_withheld:' + reason)


def extractive_case(*, question, verified, relationships):
    """Build only byte-identical premises; never summarize evidence in an adapter."""
    if type(question) is not str or not question.strip() or len(question.encode()) > 4096:
        raise ValueError('bounded_question_required')
    chunks = verified['chunks']
    if not 2 <= len(chunks) <= 16:
        raise ValueError('two_to_sixteen_selected_chunks_required')
    sources, premises, seen = [], [], set()
    document_id = verified['document']['document_id']
    for chunk in chunks:
        index, text = chunk['index'], chunk['text']
        if type(index) is not int or index < 0 or index in seen or type(text) is not str or not text.strip():
            raise ValueError('unique_nonempty_chunks_required')
        seen.add(index)
        data = text.encode()
        if len(data) != chunk['byte_length'] or hashlib.sha256(data).hexdigest() != chunk['sha256']:
            raise ValueError('chunk_bytes_mismatch')
        evidence_id, premise_id = f'evidence-{index}', f'premise-{index}'
        sources.append(dict(evidence_id=evidence_id, document_id=document_id,
                            chunk_index=index, text=text))
        premises.append(dict(premise_id=premise_id, statement=text, evidence_ids=[evidence_id]))
    ids = {p['premise_id'] for p in premises}
    if type(relationships) not in (list, tuple) or not 1 <= len(relationships) <= 32:
        raise ValueError('explicit_relationship_hypotheses_required')
    parsed, seen_relationships, covered = [], set(), set()
    for raw in relationships:
        relationship = SemanticRelationshipText.model_validate(raw, strict=True).model_dump(mode='json')
        source, target = relationship['source_premise_id'], relationship['target_premise_id']
        key = (source, target, relationship['kind'])
        basis = relationship['basis']
        if (source not in ids or target not in ids or source == target or key in seen_relationships
                or not basis.strip() or len(basis.encode()) > 2048):
            raise ValueError('invalid_relationship_hypothesis')
        seen_relationships.add(key)
        covered.update((source, target))
        parsed.append(relationship)
    if covered != ids:
        raise ValueError('every_premise_requires_explicit_relationship')
    case = dict(question=question, sources=sources, premises=premises, relationships=parsed)
    if len(canonical(case).encode()) > 60000:
        raise ValueError('context_byte_budget')
    return case


async def inspect_corpus(*, reconciler, session, principal, document_id, chunk_indices,
                         question, relationships, transport, current_gate_sha256,
                         timeout_seconds=90):
    """Return a checked SQL publication, with at most three paid provider calls.

    The caller explicitly provisions inspection tables and gate beforehand. This
    function does not install schema, rotate evidence gates, select sources,
    authorize release, or retry calls. Withheld evaluations raise without exposing
    the candidate. Retrieval performs complete manifest/index verification before
    selecting the bounded context; the SQL barrier checks identity after calls.
    """
    if type(reconciler) is not CatalogIndexReconciler:
        raise ValueError('explicit_catalog_reconciler_required')
    if (type(session) is not GovernedAuthenticationSession
            or type(principal) is not AuthenticatedGovernedPrincipal
            or not session.bound_to(reconciler.writer) or not session.recheck(principal)):
        raise PublicationDenied('authenticated_session_required')
    scope = principal.scope.model_dump(mode='json')
    verified = reconciler.retrieve_verified(document_id=document_id, scope=scope,
                                             chunk_indices=chunk_indices)
    case = extractive_case(question=question, verified=verified, relationships=relationships)
    context_sha256 = hashlib.sha256(canonical(case).encode()).hexdigest()
    gate_sha256 = current_gate_sha256()
    barrier = InspectionPublicationBarrier(reconciler.writer, session=session, principal=principal,
        chunk_store=reconciler.chunk_store, current_gate_sha256=current_gate_sha256,
        current_context_sha256=lambda: context_sha256)
    proof = barrier.capture(document_id=document_id, context_sha256=context_sha256,
                            gate_sha256=gate_sha256)
    if proof.catalog_epoch != verified['catalog_epoch'] or proof.manifest_sha256 != verified['manifest_sha256']:
        raise PublicationDenied('retrieval_binding_changed')

    def current_binding():
        # Existing barrier owns the full authority, gate, version and ack checks.
        # A fresh SQL transaction runs before each dispatch and after each reply.
        with reconciler.writer.transaction() as cursor:
            barrier._recheck(cursor, proof)
        return dict(question=question, context_sha256=context_sha256,
                    principal_id=proof.principal_id, permission_epoch=proof.permission_epoch,
                    credential_epoch=proof.credential_epoch, catalog_epoch=proof.catalog_epoch,
                    gate_sha256=proof.gate_sha256, eligible=True, scope=scope)

    async def retrieve():
        return case

    handle = await barrier.evaluate(proof, transport=transport, retrieve=retrieve,
                                    current_binding=current_binding, timeout_seconds=timeout_seconds)
    outcome = barrier._candidate.to_dict()
    if outcome.get('status') == 'withheld':
        # inspect_runtime withheld reports contain no candidate/context. Expose
        # only its fixed operational reason and bounded dispatch count.
        raise CorpusInspectionWithheld(outcome['reason'], outcome['attempted_calls'])
    publication_id = barrier.publish(proof, handle)
    checked = barrier.read(proof, publication_id)
    return publication_id, checked


def render_checked_inspection(report):
    """Escaped standalone private review; never accepted by the frozen UI contract.

    Caller must supply the result of the current authorized publication read.
    Export is an immutable historical review snapshot, not revocable live access.
    """
    value = report.to_dict()
    if (value.get('status') != 'inspection_only' or value.get('preview_allowed') is not True
            or value.get('production_enabled') is not False or value.get('release_authorized') is not False
            or value.get('proposition_to_inference') != 'closed'
            or value.get('inspection_publication_barrier_implemented') is not True):
        raise PublicationDenied('checked_inspection_report_required')
    escape = lambda text: html.escape(str(text), quote=True)
    context, candidate = value['context'], value['candidate']
    sources = ''.join(f'<section id="source-{i}"><h2>Source {i + 1}</h2>'
        f'<p>Document: {escape(source["document_id"])} · Chunk: {escape(source["chunk_index"])}</p>'
        f'<pre>{escape(source["text"])}</pre></section>'
        for i, source in enumerate(context['sources']))
    qualifications = ''.join(f'<li>{escape(text)}</li>' for text in candidate['qualifications'])
    provenance = escape(canonical(value['inspection_publication_binding']))
    assessments = escape(canonical({key: value[key] for key in
        ('configuration', 'statement_assessment', 'relevance_assessment')}))
    hypotheses = escape(canonical(context['relationships']))
    return ('<!doctype html><html lang="en"><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &apos;none&apos;; '
        'style-src &apos;unsafe-inline&apos;; base-uri &apos;none&apos;; form-action &apos;none&apos;">'
        '<title>Actual corpus runtime inspection</title>'
        '<style>body{font:17px system-ui;max-width:960px;margin:3rem auto;padding:0 1rem;line-height:1.6}'
        'pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f0f2f5;padding:1rem}'
        'section{border-top:1px solid #aaa;margin-top:2rem}</style>'
        '<h1>Actual corpus runtime inspection</h1>'
        '<p><strong>Production disabled. Release unauthorized. Proposition-to-inference closed.</strong></p>'
        '<p>This is a private historical inspection snapshot. Model assessments do not establish source truth '
        'or human acceptance. Relationship descriptions are operator-supplied hypotheses.</p>'
        f'<h2>{escape(context["question"])}</h2><h3>Candidate for owner review</h3>'
        f'<p>{escape(candidate["statement"])}</p><ul>{qualifications}</ul>{sources}'
        f'<section><h2>Relationship hypotheses</h2><pre>{hypotheses}</pre></section>'
        f'<section><h2>Recorded model assessments</h2><pre>{assessments}</pre></section>'
        f'<section><h2>Publication provenance</h2><pre>{provenance}</pre></section></html>')
