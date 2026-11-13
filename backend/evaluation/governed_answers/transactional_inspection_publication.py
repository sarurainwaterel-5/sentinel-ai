"""Durable isolated inspection publication, never production answer authority.

All lifecycle, grant and credential writers must obey the shared row-lock protocol.
The linearization point is the committed SQL insert/read, not later network delivery.
"""
from dataclasses import asdict, dataclass
import hashlib
import secrets

from app.services.governed_authentication import GovernedAuthenticationSession, AuthenticatedGovernedPrincipal
from .versioned_manifests import Version, Locator, manifest_digest, MAX_CHUNKS, PAGE_SIZE
from .live_provider_rehearsal import canonical
from .runtime_inspection_rehearsal import InspectionResult, inspect_runtime


@dataclass(frozen=True)
class PublicationProof:
    principal_id: str
    permission_epoch: int
    credential_epoch: int
    scope_sha256: str
    catalog_epoch: int
    document_id: str
    version_id: str
    lifecycle_epoch: int
    content_epoch: int
    index_epoch: int
    manifest_sha256: str
    context_sha256: str
    gate_sha256: str
    gate_epoch: int


@dataclass(frozen=True)
class InspectionCandidateHandle:
    nonce: str


class PublicationDenied(ValueError):
    pass


class InspectionPublicationBarrier:
    """Transaction-owning catalog plus trusted session verifier, no raw identity.

    The exact authentication session must own the supplied issued principal.
    Rechecks use its bounded synchronous catalog read before locked SQL checks.
    The read capability must not perform network I/O or block indefinitely.
    Immutable source verification and index reconciliation precede capture; the
    barrier rechecks their current version/ack identity, not external index bytes.
    """
    def __init__(self, writer, *, session, principal, chunk_store, current_gate_sha256, current_context_sha256):
        if (type(session) is not GovernedAuthenticationSession or type(principal) is not AuthenticatedGovernedPrincipal
                or not session.bound_to(writer)):
            raise PublicationDenied('authenticated_session_required')
        self.current_gate_sha256 = current_gate_sha256
        self.current_context_sha256 = current_context_sha256
        self._evaluation_used = False
        self.chunk_store = chunk_store
        self.writer = writer
        self.session = session
        self.principal = principal
        self._issued = None
        self._candidate = None
        self._candidate_handle = None

    def initialize(self):
        with self.writer.transaction() as cursor:
            cursor.execute('''CREATE TABLE IF NOT EXISTS inspection_publications (
                publication_id TEXT PRIMARY KEY, report_json TEXT NOT NULL,
                report_sha256 TEXT NOT NULL, proof_json TEXT NOT NULL)''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS inspection_gate (
                gate_id TEXT PRIMARY KEY CHECK(gate_id='current'),
                epoch BIGINT NOT NULL CHECK(epoch>=1),
                sha256 TEXT NOT NULL CHECK(sha256 ~ '^[a-f0-9]{64}$'))''')

    def set_gate(self, *, expected_epoch, sha256):
        """Explicit evidence identity rotation; never an approval or release grant."""
        if type(expected_epoch) is not int or not 0 <= expected_epoch < 2**63-1 or type(sha256) is not str or len(sha256) != 64 or any(c not in '0123456789abcdef' for c in sha256):
            raise PublicationDenied('invalid_gate_identity')
        with self.writer.transaction() as cursor:
            cursor.execute("SELECT epoch FROM inspection_gate WHERE gate_id='current' FOR UPDATE")
            row = cursor.fetchone()
            if row is None:
                if expected_epoch != 0: raise PublicationDenied('stale_gate_epoch')
                cursor.execute("INSERT INTO inspection_gate VALUES ('current',1,%s)",(sha256,))
                return 1
            if row['epoch'] != expected_epoch: raise PublicationDenied('stale_gate_epoch')
            cursor.execute("UPDATE inspection_gate SET epoch=epoch+1,sha256=%s WHERE gate_id='current' RETURNING epoch",(sha256,))
            return cursor.fetchone()['epoch']

    def _current(self, cursor, document_id, context_sha256, gate_sha256):
        cursor.execute("SELECT epoch,sha256 FROM inspection_gate WHERE gate_id='current' FOR UPDATE")
        gate = cursor.fetchone()
        if gate is None or gate['sha256'] != gate_sha256:
            raise PublicationDenied('gate_evidence_missing_or_changed')
        if self.current_gate_sha256() != gate_sha256 or self.current_context_sha256() != context_sha256:
            raise PublicationDenied('request_or_gate_changed')
        if not self.session.recheck(self.principal):
            raise PublicationDenied('session_recheck_denied')
        principal_id = self.principal.principal_id
        permission_epoch = self.principal.permission_epoch
        credential_epoch = self.principal.credential_epoch
        if (type(principal_id) is not str or not principal_id
                or type(permission_epoch) is not int or type(credential_epoch) is not int):
            raise PublicationDenied('invalid_authenticated_session')
        cursor.execute('SELECT permission_epoch,credential_epoch,disabled FROM principals WHERE principal_id=%s FOR UPDATE', (principal_id,))
        authority = cursor.fetchone()
        if authority is None or (authority['permission_epoch'],authority['credential_epoch'],authority['disabled']) != (permission_epoch,credential_epoch,False):
            raise PublicationDenied('session_changed')
        # Lock order: gate -> principal -> scope -> document. Gate updates lock
        # only gate; supported authority writers use principal -> scope -> document.
        cursor.execute('SELECT scope_sha256 FROM documents WHERE document_id=%s', (document_id,))
        row = cursor.fetchone()
        if row is None:
            raise PublicationDenied('missing_document')
        scope_sha256 = row['scope_sha256']
        cursor.execute('SELECT catalog_epoch,scope_json FROM scopes WHERE scope_sha256=%s FOR UPDATE', (scope_sha256,))
        scope = cursor.fetchone()
        if scope is None or canonical(scope['scope_json']) != canonical(self.principal.scope.model_dump(mode='json')):
            raise PublicationDenied('authenticated_scope_mismatch')
        cursor.execute('SELECT 1 FROM grants WHERE principal_id=%s AND scope_sha256=%s', (principal_id,scope_sha256))
        if scope is None or cursor.fetchone() is None:
            raise PublicationDenied('scope_grant_denied')
        cursor.execute('''SELECT scope_sha256,version_id,lifecycle_epoch,content_epoch,index_epoch,state
                          FROM documents WHERE document_id=%s FOR UPDATE''', (document_id,))
        document = cursor.fetchone()
        if document is None or document['scope_sha256'] != scope_sha256 or document['state'] != 'active':
            raise PublicationDenied('document_not_active')
        version_id, lifecycle, content, index = (document[k] for k in ('version_id','lifecycle_epoch','content_epoch','index_epoch'))
        cursor.execute('SELECT manifest_sha256,binding_json,source_sha256 FROM versions WHERE version_id=%s AND document_id=%s', (version_id,document_id))
        version = cursor.fetchone()
        if version is None:
            raise PublicationDenied('missing_version')
        immutable = dict(version['binding_json'])
        immutable['scope'] = tuple(immutable['scope'])
        parsed = Version(**immutable)
        parsed.validate()
        if (parsed.document_version_id != version_id
                or canonical(dict(zip(('organization_id','collection','module','topic'),parsed.scope))) != canonical(scope['scope_json'])
                or version['source_sha256'] != parsed.source_sha256):
            raise PublicationDenied('version_scope_or_source_mismatch')
        cursor.execute('SELECT byte_length,store_version FROM source_objects WHERE source_sha256=%s',(parsed.source_sha256,))
        source = cursor.fetchone()
        if source is None or source['byte_length'] != parsed.source_byte_length or source['store_version'] != 'source-cas-v2':
            raise PublicationDenied('source_reference_mismatch')
        cursor.execute('''SELECT 1 FROM outbox WHERE document_id=%s AND version_id=%s
                          AND lifecycle_epoch=%s AND content_epoch=%s AND index_epoch=%s
                          AND manifest_sha256=%s AND status='acknowledged' LIMIT 1''',
                       (document_id,version_id,lifecycle,content,index,version['manifest_sha256']))
        if cursor.fetchone() is None:
            raise PublicationDenied('index_not_reconciled')
        return PublicationProof(principal_id,permission_epoch,credential_epoch,scope_sha256,
            scope['catalog_epoch'],document_id,version_id,lifecycle,content,index,version['manifest_sha256'],context_sha256,gate_sha256,gate['epoch'])

    def capture(self, *, document_id, context_sha256, gate_sha256):
        if self._issued is not None:
            raise PublicationDenied('capture_already_used')
        for value in (context_sha256,gate_sha256):
            if type(value) is not str or len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
                raise PublicationDenied('invalid_digest')
        with self.writer.transaction() as cursor:
            proof = self._current(cursor,document_id,context_sha256,gate_sha256)
        self._issued = proof
        return proof

    def _recheck(self, cursor, proof):
        if proof is not self._issued or proof is None:
            raise PublicationDenied('unissued_proof')
        if self._current(cursor,proof.document_id,proof.context_sha256,proof.gate_sha256) != proof:
            raise PublicationDenied('publication_binding_changed')

    async def evaluate(self, proof, **kwargs):
        if proof is not self._issued or self._evaluation_used:
            raise PublicationDenied('unissued_or_used_proof')
        self._evaluation_used = True
        with self.writer.transaction() as cursor:
            self._recheck(cursor,proof)
        result = await inspect_runtime(**kwargs)
        with self.writer.transaction() as cursor:
            self._recheck(cursor,proof)
        self._candidate = result
        self._candidate_handle = InspectionCandidateHandle(secrets.token_hex(24))
        return self._candidate_handle

    def _verify_context(self, cursor, proof, report):
        cursor.execute('SELECT binding_json FROM versions WHERE version_id=%s', (proof.version_id,))
        binding = dict(cursor.fetchone()['binding_json'])
        binding['scope'] = tuple(binding['scope'])
        version = Version(**binding)
        version.validate()
        if not 1 <= version.chunk_count <= MAX_CHUNKS:
            raise PublicationDenied('bounded_inspection_manifest_required')
        locators=[]
        total=0
        for start in range(0,version.chunk_count,PAGE_SIZE):
            cursor.execute('SELECT * FROM chunks WHERE version_id=%s AND chunk_index>=%s ORDER BY chunk_index LIMIT %s',(proof.version_id,start,PAGE_SIZE))
            rows=cursor.fetchall()
            if len(rows)!=min(PAGE_SIZE,version.chunk_count-start):raise PublicationDenied('manifest_page_length')
            for offset,row in enumerate(rows):
                locator=Locator(row['chunk_index'],row['chunk_sha256'],row['byte_length'],row['storage_reference'])
                locator.validate()
                if locator.chunk_index!=start+offset:raise PublicationDenied('manifest_order')
                total+=locator.chunk_byte_length
                if total>64*1024*1024:raise PublicationDenied('text_byte_budget')
                locators.append(locator)
        cursor.execute('SELECT 1 FROM chunks WHERE version_id=%s AND chunk_index>=%s LIMIT 1',(proof.version_id,version.chunk_count))
        if cursor.fetchone() is not None or manifest_digest(version,locators)!=proof.manifest_sha256:
            raise PublicationDenied('manifest_mismatch')
        sources=report.get('context',{}).get('sources')
        if type(sources) is not list or not 1<=len(sources)<=128:
            raise PublicationDenied('bounded_selected_context_required')
        selected=[]
        for source in sources:
            index=source.get('chunk_index')
            if type(index) is not int or not 0<=index<version.chunk_count or index in selected or source.get('document_id')!=proof.document_id:
                raise PublicationDenied('source_locator_mismatch')
            selected.append(index)
            locator=locators[index]
            data=self.chunk_store.read(expected_sha256=locator.chunk_sha256,expected_byte_length=locator.chunk_byte_length)
            if type(source.get('text')) is not str or source['text'].encode()!=data:
                raise PublicationDenied('source_bytes_mismatch')
        premises = report['context'].get('premises')
        source_map = {source.get('evidence_id'):source for source in sources}
        if len(source_map) != len(sources) or type(premises) is not list or len(premises) != len(sources):
            raise PublicationDenied('extractive_premises_required')
        used = []
        for premise in premises:
            ids = premise.get('evidence_ids')
            if type(ids) is not list or len(ids) != 1 or ids[0] not in source_map or premise.get('statement') != source_map[ids[0]]['text']:
                raise PublicationDenied('extractive_premises_required')
            used.extend(ids)
        if len(set(used)) != len(sources):
            raise PublicationDenied('complete_premises_required')
        context_digest = hashlib.sha256(canonical(report['context']).encode()).hexdigest()
        if context_digest != proof.context_sha256:
            raise PublicationDenied('context_changed')

    def publish(self, proof, handle):
        if handle is not self._candidate_handle or handle is None:
            raise PublicationDenied('issued_candidate_handle_required')
        report = self._candidate.to_dict()
        binding = report.get('binding', {})
        if (report.get('status') != 'inspection_only' or report.get('preview_allowed') is not True
                or report.get('production_enabled') is not False or report.get('release_authorized') is not False
                or canonical(binding.get('scope')) != canonical(self.principal.scope.model_dump(mode='json'))
                or binding.get('principal_id') != proof.principal_id
                or binding.get('credential_epoch') != proof.credential_epoch
                or binding.get('permission_epoch') != proof.permission_epoch
                or binding.get('catalog_epoch') != proof.catalog_epoch
                or binding.get('context_sha256') != proof.context_sha256
                or binding.get('gate_sha256') != proof.gate_sha256):
            raise PublicationDenied('report_binding_mismatch')
        report['inspection_publication_binding'] = asdict(proof)
        report['selected_chunk_indices'] = [source.get('chunk_index') for source in report.get('context',{}).get('sources',[])]
        report['inspection_publication_barrier_implemented'] = True
        encoded = canonical(report)
        if len(encoded.encode()) > 262144:
            raise PublicationDenied('report_budget')
        publication_id = secrets.token_hex(24)
        with self.writer.transaction() as cursor:
            self._recheck(cursor,proof)
            self._verify_context(cursor,proof,report)
            cursor.execute('INSERT INTO inspection_publications VALUES (%s,%s,%s,%s)',
                           (publication_id,encoded,hashlib.sha256(encoded.encode()).hexdigest(),canonical(asdict(proof))))
        # Receipt contains no candidate. Subsequent display must call read().
        return publication_id

    def read(self, proof, publication_id):
        with self.writer.transaction() as cursor:
            self._recheck(cursor,proof)
            cursor.execute('SELECT report_json,report_sha256,proof_json FROM inspection_publications WHERE publication_id=%s', (publication_id,))
            row = cursor.fetchone()
            if row is None or row['proof_json'] != canonical(asdict(proof)) or hashlib.sha256(row['report_json'].encode()).hexdigest() != row['report_sha256']:
                raise PublicationDenied('publication_integrity_denied')
            report = InspectionResult(row['report_json'])
            self._verify_context(cursor,proof,report.to_dict())
        return report
