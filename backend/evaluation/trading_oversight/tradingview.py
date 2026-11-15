"""Manual TradingView paper CSV evidence capture, never an execution/data adapter.

No semantic mapping is inferred from unknown export columns. Raw artifacts remain
operator-supplied, unauthenticated evidence pending a separately reviewed mapping.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import os
import re
from pathlib import Path
from .contracts import utc_time
from .reader import read_local, open_directory

MAX_FILES = 8
MAX_TOTAL_BYTES = 4 * 1024 * 1024
MAX_ROWS = 10000


def summarize_csv(raw: bytes) -> dict:
    """Check CSV framing only; never interpret prices, trades or account state."""
    if not raw or len(raw) > 1024 * 1024 or b'\0' in raw:
        raise ValueError('bounded nonempty CSV required')
    text = raw.decode('utf-8-sig', errors='strict')
    try:
        rows = csv.reader(io.StringIO(text, newline=''), strict=True)
        headers = next(rows)
        if (not 1 <= len(headers) <= 128 or any(not h.strip() or len(h) > 256 for h in headers)
                or len(set(h.strip().casefold() for h in headers)) != len(headers)
                or any(re.search(r'password|secret|credential|cookie|authorization|api.?key|access.?token', h, re.I) for h in headers)):
            raise ValueError('ambiguous or credential-shaped CSV header')
        count = 0
        for row in rows:
            if not row:
                continue
            if len(row) != len(headers):
                raise ValueError('CSV row width mismatch')
            count += 1
            if count > MAX_ROWS:
                raise ValueError('CSV row count exceeded')
    except (csv.Error, StopIteration) as exc:
        raise ValueError('invalid CSV framing') from exc
    return {'byte_length': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(),
            'column_count': len(headers), 'data_rows': count,
            'header_sha256': hashlib.sha256(json.dumps(headers, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest(),
            'semantic_mapping': 'NOT_IMPLEMENTED', 'source_authenticated': False}


def capture(*, inputs, organization_id: str, account_id: str, captured_at: str, output_dir) -> dict:
    """Copy bounded original CSV bytes into a new private directory, exclusively.

    Account/time are operator labels, not independently verified platform facts.
    No normalized snapshot, inferred fills, ledger writes or approval is created.
    """
    utc_time(captured_at)
    for value in (organization_id, account_id):
        if type(value) is not str or not re.fullmatch(r'[A-Za-z0-9_.-]{1,100}', value):
            raise ValueError('explicit bounded local account identifiers required')
    if not 1 <= len(inputs) <= MAX_FILES:
        raise ValueError('one to eight CSV exports required')
    items = []
    for path in inputs:
        path = Path(path)
        if path.suffix.lower() != '.csv':
            raise ValueError('CSV files only')
        raw = read_local(path)
        summary = summarize_csv(raw)
        if any(item[1]['sha256'] == summary['sha256'] for item in items):
            raise ValueError('duplicate CSV content')
        items.append((raw, summary))
    if sum(len(raw) for raw, _ in items) > MAX_TOTAL_BYTES:
        raise ValueError('total evidence bytes exceeded')
    result = {'schema_version': 'sentinel.tradingview.paper.evidence.v0.1',
              'platform': 'TRADINGVIEW_PAPER_TRADING',
              'scope': {'organization_id': organization_id, 'account_id': account_id, 'environment': 'PAPER'},
              'captured_at': captured_at, 'capture_time_source': 'OPERATOR_SUPPLIED',
              'provenance': 'OPERATOR_SUPPLIED_UNVERIFIED', 'source_authenticated': False,
              'semantic_mapping': 'NOT_IMPLEMENTED', 'normalized_snapshot_created': False,
              'trade_count': None, 'position': {'status': 'UNKNOWN', 'quantity': None},
              'risk_configuration': 'UNVERIFIED', 'human_review': 'PENDING',
              'authority': {'advisory_only': True, 'execution_authorized': False, 'live_authorized': False},
              'limitation': 'CSV structure and bytes verified only. No account ownership, completeness, instrument metadata, clock domain, fills, risk compliance or strategy eligibility certified.',
              'files': [dict(summary, saved_as=f'evidence-{i:03d}.csv') for i, (_, summary) in enumerate(items, 1)]}
    output = Path(os.path.abspath(os.fspath(output_dir)))
    parent = open_directory(output.parent)
    directory = None
    created = []
    made = False
    try:
        os.mkdir(output.name, mode=0o700, dir_fd=parent)
        made = True
        directory = os.open(output.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        def write(name, data):
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            created.append(name)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        for i, (raw, _) in enumerate(items, 1):
            write(f'evidence-{i:03d}.csv', raw)
        write('evidence.json', (json.dumps(result, sort_keys=True, indent=2, ensure_ascii=False) + '\n').encode())
        os.fsync(directory)
        os.fsync(parent)
        return result
    except BaseException:
        if directory is not None:
            for name in reversed(created):
                os.unlink(name, dir_fd=directory)
        if made:
            os.rmdir(output.name, dir_fd=parent)
        raise
    finally:
        if directory is not None:
            os.close(directory)
        os.close(parent)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Capture manual TradingView paper CSV evidence locally; no trade mapping or execution.')
    parser.add_argument('command', choices=['capture'])
    parser.add_argument('--input', action='append', required=True)
    parser.add_argument('--organization-id', required=True)
    parser.add_argument('--account-id', required=True)
    parser.add_argument('--captured-at', required=True)
    parser.add_argument('--output-dir', required=True)
    args = parser.parse_args(argv)
    try:
        result = capture(inputs=args.input, organization_id=args.organization_id, account_id=args.account_id,
                         captured_at=args.captured_at, output_dir=args.output_dir)
    except (OSError, ValueError, UnicodeError):
        parser.exit(1, 'Evidence capture failed: inspect local input framing, bounds and output permissions. No trading action occurred.\n')
    print(json.dumps({'files_captured': len(result['files']), 'source_authenticated': False, 'normalized_snapshot_created': False, 'execution_authorized': False}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
