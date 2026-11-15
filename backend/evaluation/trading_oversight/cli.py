"""Offline local artifact inspection and explicitly requested human receipts."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import sys

from .contracts import canonical, parse_snapshot, utc_time
from .evaluator import assess_snapshot
from .reader import open_directory, read_local
from .report import AUTHORITY, build_artifacts, exact_authority, parse_expectations, sha256, strict_json


def write_bundle(path: str | Path, files: dict[str, bytes]) -> None:
    """Create a private, exclusive bundle, removing incomplete output on failure."""
    path = Path(os.path.abspath(os.fspath(path)))
    parent = open_directory(path.parent)
    directory = None
    created = False
    names = []
    try:
        os.mkdir(path.name, 0o700, dir_fd=parent)
        created = True
        directory = os.open(path.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
        for name, data in files.items():
            if not re.fullmatch(r'[a-z0-9-]+\.(json|html|csv)', name):
                raise ValueError('invalid bundle filename')
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            names.append(name)
            with os.fdopen(fd, 'wb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        os.fsync(directory)
        os.fsync(parent)
    except BaseException:
        if directory is not None:
            for name in names:
                os.unlink(name, dir_fd=directory)
        if created:
            os.rmdir(path.name, dir_fd=parent)
        raise
    finally:
        if directory is not None:
            os.close(directory)
        os.close(parent)


def inspect(*, input_path: str, expectations_path: str, now: str, output_dir: str) -> None:
    raw = read_local(input_path)
    expected_raw = read_local(expectations_path, maximum=16384)
    expected = parse_expectations(expected_raw)
    utc_time(now)
    if 'now' in expected and expected['now'] != now:
        raise ValueError('explicit clock differs from expectations clock')
    snapshot = parse_snapshot(raw)
    assessment = assess_snapshot(snapshot, expected_scope=expected['scope'],
                                 expected_policy_hashes=expected['policy_hashes'], now=now)
    write_bundle(output_dir, build_artifacts(assessment, input_bytes=raw,
                                            expectations_bytes=expected_raw, now=now))


def review(*, report_dir: str, decision: str, reviewer: str, at: str) -> None:
    if decision not in ('accept', 'reject', 'defer'):
        raise ValueError('invalid human decision')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9 _.@:-]{0,127}', reviewer):
        raise ValueError('explicit bounded reviewer identity required')
    reviewed_at = utc_time(at)
    base = Path(report_dir)
    manifest_raw = read_local(base / 'manifest.json', maximum=16384)
    manifest = strict_json(manifest_raw)
    if (set(manifest) != {'schema_version', 'input_sha256', 'expectations_sha256', 'files', 'authority'}
            or manifest['schema_version'] != 'sentinel.trading.oversight.bundle.v0.1'
            or not exact_authority(manifest['authority'])
            or not isinstance(manifest['files'], dict)
            or set(manifest['files']) != {'report.json', 'report.html'}):
        raise ValueError('invalid report bundle manifest')
    files = {name: read_local(base / name, maximum=4 * 1024 * 1024) for name in ('report.json', 'report.html')}
    if any(sha256(data) != manifest['files'][name] for name, data in files.items()):
        raise ValueError('report bundle hash mismatch')
    report = strict_json(files['report.json'])
    if (not exact_authority(report.get('authority')) or report.get('human_review') != 'PENDING'
            or report.get('input_sha256') != manifest['input_sha256']
            or report.get('expectations_sha256') != manifest['expectations_sha256']):
        raise ValueError('report evidence bindings differ')
    if reviewed_at < utc_time(report['assessed_at']):
        raise ValueError('review precedes assessment')
    receipt = {'schema_version': 'sentinel.trading.oversight.human-review.v0.1',
               'decision': decision, 'reviewer': reviewer, 'reviewed_at': at,
               'input_sha256': manifest['input_sha256'],
               'expectations_sha256': manifest['expectations_sha256'],
               'report_sha256': manifest['files']['report.json'],
               'html_sha256': manifest['files']['report.html'],
               'manifest_sha256': sha256(manifest_raw), 'authority': dict(AUTHORITY),
               'effect': 'Review of this exact advisory artifact only; no execution or policy effect.'}
    fd = open_directory(base)
    try:
        target = os.open('human-review.json', os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=fd)
        try:
            with os.fdopen(target, 'wb') as stream:
                stream.write(canonical(receipt).encode('utf-8'))
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(fd)
        except BaseException:
            os.unlink('human-review.json', dir_fd=fd)
            raise
    finally:
        os.close(fd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inspection = commands.add_parser('inspect')
    inspection.add_argument('--input', required=True)
    inspection.add_argument('--expectations', required=True)
    inspection.add_argument('--now', required=True)
    inspection.add_argument('--output-dir', required=True)
    human = commands.add_parser('review')
    human.add_argument('--report-dir', required=True)
    human.add_argument('--decision', choices=('accept', 'reject', 'defer'), required=True)
    human.add_argument('--reviewer', required=True)
    human.add_argument('--at', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'inspect':
            inspect(input_path=args.input, expectations_path=args.expectations,
                    now=args.now, output_dir=args.output_dir)
        else:
            review(report_dir=args.report_dir, decision=args.decision, reviewer=args.reviewer, at=args.at)
    except (ValueError, OSError) as exc:
        # No payload/validation exception details: those may contain private source text.
        print('Offline operation rejected: ' + type(exc).__name__, file=sys.stderr)
        return 2
    print('Private offline artifact created; no execution authority granted.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
