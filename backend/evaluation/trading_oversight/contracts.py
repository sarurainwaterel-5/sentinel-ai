"""Closed offline envelope; hashes establish consistency, never producer authenticity."""
from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

MAX_BYTES = 1024 * 1024
MAX_DEPTH = 16
SAFE_INT = 9007199254740991
Hash = Annotated[str, Field(pattern=r'^[0-9a-f]{64}$')]
Text = Annotated[str, Field(min_length=1, max_length=256)]
Time = Annotated[str, Field(pattern=r'^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$')]
Number = Annotated[int, Field(ge=-SAFE_INT, le=SAFE_INT)]
Count = Annotated[int, Field(ge=0, le=SAFE_INT)]


def utc_time(value: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z', value):
        raise ValueError('exact UTC milliseconds required')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%S.%fZ').replace(tzinfo=timezone.utc)


def _validate_json(value, depth=0):
    if depth > MAX_DEPTH:
        raise ValueError('JSON depth exceeded')
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if abs(value) > SAFE_INT:
            raise ValueError('unsafe integer')
        return
    if type(value) is str:
        if len(value) > 8192 or any(0xD800 <= ord(c) <= 0xDFFF for c in value):
            raise ValueError('invalid bounded Unicode string')
        if re.search(r'(?:sk-[A-Za-z0-9_-]{12,}|-----BEGIN .*PRIVATE KEY|Bearer\s+\S+)', value, re.I):
            raise ValueError('credential-shaped value rejected')
        return
    if type(value) is list:
        if len(value) > 128:
            raise ValueError('array bound exceeded')
        for item in value:
            _validate_json(item, depth + 1)
        return
    if type(value) is dict:
        if len(value) > 128:
            raise ValueError('object bound exceeded')
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError('string keys required')
            if re.search(r'password|secret|credential|api[_-]?key|cookie|authorization|access[_-]?token', key, re.I):
                raise ValueError('credential-bearing field rejected')
            _validate_json(key, depth + 1)
            _validate_json(item, depth + 1)
        return
    raise ValueError('only safe integer JSON values accepted')


def canonical(value) -> str:
    """Trading audit canonical form for bounded integer-only JSON, UTF-16 key order."""
    _validate_json(value)
    def encode(v):
        if isinstance(v, dict):
            return '{' + ','.join(json.dumps(k, ensure_ascii=False) + ':' + encode(v[k]) for k in sorted(v, key=lambda k: k.encode('utf-16-be'))) + '}'
        if isinstance(v, list):
            return '[' + ','.join(encode(x) for x in v) + ']'
        return json.dumps(v, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
    return encode(value)


def digest(value) -> str:
    return hashlib.sha256(canonical(value).encode('utf-8')).hexdigest()


class Closed(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, frozen=True)


class Scope(Closed):
    organization_id: Text
    account_id: Text
    environment: Literal['PAPER', 'LOCAL_SIMULATION']


class Source(Closed):
    producer_id: Text
    repository_commit: Annotated[str, Field(pattern=r'^[0-9a-f]{40}$')]
    build_id: Text
    export_version: Literal['0.1']
    dirty: bool


class Provenance(Closed):
    kind: Literal['synthetic', 'historical-replay', 'paper-ledger']
    capture_origin: Text
    authenticity: Literal['OPERATOR_SUPPLIED_UNVERIFIED']


class Clock(Closed):
    created_at: Time
    source_as_of: Time
    received_at: Time
    coverage_start: Time
    coverage_end: Time
    domain: Literal['WALL', 'REPLAY', 'SYNTHETIC']
    quote_as_of: Time | None


class Binding(Closed):
    account_revision: Count
    observation_epoch: Count
    prior_sequence: Count
    prior_head: Hash
    latest_sequence: Count
    latest_head: Hash
    context_sha256: Hash


class Policy(Closed):
    strategy: Hash
    risk: Hash
    imaf_definition: Hash
    imaf_policy: Hash


class Readiness(Closed):
    imaf_status: Literal['ENTRY_LOCK_PENDING_OPERATIONAL_DEFINITIONS']
    open_definition_ids: Annotated[list[Text], Field(min_length=1, max_length=16)]
    collection_ready: Literal[False]
    reconciliation: Literal['RECONCILED', 'REQUIRED', 'UNKNOWN']


class AccountState(Closed):
    position_status: Literal['KNOWN', 'UNKNOWN']
    position_quantity: Number | None
    as_of: Time
    pending_orders: Count | None
    reservations: Count | None
    session_entries: Count | None
    realized_pnl_cents: Number | None
    kill_active: bool | None
    frozen: bool | None
    protection: Literal['UNVERIFIED', 'MISSING', 'CLAIMED_PRESENT']
    profile_provenance: Literal['SYNTHETIC', 'OPERATOR_SUPPLIED_UNVERIFIED']

    @model_validator(mode='after')
    def exposure(self):
        if (self.position_status == 'KNOWN') != (self.position_quantity is not None):
            raise ValueError('position state and quantity disagree')
        return self


class Proposal(Closed):
    candidate_id: Text
    candidate_sha256: Hash
    direction: Literal['long', 'short']
    entry_ticks: Number
    stop_ticks: Number
    target_ticks: Number
    quantity: Annotated[int, Field(ge=1, le=SAFE_INT)]
    expected_costs_cents: Count
    imaf_decision_sha256: Hash | None
    evidence_refs: Annotated[list[Hash], Field(max_length=32)]


class Event(Closed):
    sequence: Count
    timestamp: Time
    type: Text
    payload: dict
    previousHash: Hash
    hash: Hash


class Audit(Closed):
    events: Annotated[list[Event], Field(max_length=128)]
    continuity: Literal['GENESIS', 'UNANCHORED_CHECKPOINT']


class Completeness(Closed):
    full_source_chain: bool
    omitted_sections: Annotated[list[Text], Field(max_length=32)]
    truncated: bool


class Authority(Closed):
    advisory_only: Literal[True]
    execution_authorized: Literal[False]
    live_authorized: Literal[False]


class Snapshot(Closed):
    schema_version: Literal['sentinel.trading.oversight.snapshot.v0.1']
    snapshot_id: Text
    source: Source
    scope: Scope
    provenance: Provenance
    clock: Clock
    state_binding: Binding
    policy_binding: Policy
    readiness: Readiness
    account_state: AccountState
    proposals: Annotated[list[Proposal], Field(max_length=128)]
    audit: Audit
    completeness: Completeness
    authority: Authority

    @model_validator(mode="before")
    @classmethod
    def exact_booleans(cls, value):
        if isinstance(value, dict):
            if not isinstance(value.get("authority"), dict) or not isinstance(value.get("readiness"), dict):
                raise ValueError("authority and readiness objects required")
            for key in ("advisory_only", "execution_authorized", "live_authorized"):
                if type(value.get("authority", {}).get(key)) is not bool:
                    raise ValueError("authority requires exact JSON booleans")
            if type(value.get("readiness", {}).get("collection_ready")) is not bool:
                raise ValueError("collection readiness requires exact JSON boolean")
        return value
    payload_sha256: Hash


def parse_snapshot(raw: bytes) -> Snapshot:
    if type(raw) is not bytes or not raw or len(raw) > MAX_BYTES:
        raise ValueError('snapshot byte bound exceeded')
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('duplicate JSON key')
            out[key] = value
        return out
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite JSON')))
        _validate_json(value)
        snapshot = Snapshot.model_validate(value)
        def times(v):
            if isinstance(v, dict):
                for k, x in v.items():
                    if k in {'created_at', 'source_as_of', 'received_at', 'coverage_start', 'coverage_end', 'quote_as_of', 'as_of', 'timestamp'} and x is not None:
                        utc_time(x)
                    times(x)
            elif isinstance(v, list):
                for x in v:
                    times(x)
        times(value)
        return snapshot
    except (RecursionError, UnicodeError) as exc:
        raise ValueError('invalid bounded JSON') from exc
