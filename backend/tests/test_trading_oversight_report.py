import json
import os
from pathlib import Path

import pytest

from evaluation.trading_oversight.cli import inspect, main, review, write_bundle
from evaluation.trading_oversight.reader import read_local
from evaluation.trading_oversight.report import AUTHORITY, build_artifacts, parse_expectations, sha256

NOW = '2026-11-15T12:00:00.000Z'


def artifacts():
    return build_artifacts({'note': '</pre><script>alert(1)</script>', 'authority': AUTHORITY},
                           input_bytes=b'input', expectations_bytes=b'explicit', now=NOW)


def test_report_deterministic_and_escaped():
    assert artifacts() == artifacts()
    assert b'<script>' not in artifacts()['report.html']
    assert b'&lt;script&gt;' in artifacts()['report.html']
    assert b"default-src 'none'" in artifacts()['report.html']
    assert json.loads(artifacts()['report.json'])['human_review'] == 'PENDING'


def test_private_exclusive_bundle_and_receipt(tmp_path):
    target = tmp_path / 'report'
    write_bundle(target, artifacts())
    assert target.stat().st_mode & 0o777 == 0o700
    assert all(file.stat().st_mode & 0o777 == 0o600 for file in target.iterdir())
    with pytest.raises(FileExistsError):
        write_bundle(target, artifacts())
    before = (target / 'report.json').read_bytes()
    review(report_dir=str(target), decision='accept', reviewer='Rain', at=NOW)
    receipt = json.loads((target / 'human-review.json').read_bytes())
    assert receipt['authority'] == AUTHORITY
    assert receipt['decision'] == 'accept'
    assert (target / 'report.json').read_bytes() == before
    assert (target / 'human-review.json').stat().st_mode & 0o777 == 0o600
    with pytest.raises(FileExistsError):
        review(report_dir=str(target), decision='reject', reviewer='Rain', at=NOW)


@pytest.mark.parametrize('name', ['report.json', 'report.html'])
def test_tampered_reports_not_accepted(tmp_path, name):
    write_bundle(tmp_path / 'r', artifacts())
    (tmp_path / 'r' / name).write_bytes(b'tampered')
    with pytest.raises(ValueError):
        review(report_dir=str(tmp_path / 'r'), decision='accept', reviewer='Rain', at=NOW)
    assert not (tmp_path / 'r' / 'human-review.json').exists()


def test_failed_bundle_cleaned(tmp_path):
    with pytest.raises(ValueError):
        write_bundle(tmp_path / 'r', {'report.json': b'ok', '../escape.json': b'bad'})
    assert not (tmp_path / 'r').exists()
    assert not (tmp_path / 'escape.json').exists()


def test_bounded_regular_no_links(tmp_path):
    (tmp_path / 'f').write_bytes(b'12345')
    assert read_local(tmp_path / 'f', maximum=5) == b'12345'
    with pytest.raises(ValueError):
        read_local(tmp_path / 'f', maximum=4)
    (tmp_path / 'link').symlink_to(tmp_path / 'f')
    with pytest.raises(OSError):
        read_local(tmp_path / 'link')
    (tmp_path / 'parent').symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(OSError):
        read_local(tmp_path / 'parent' / 'f')
    os.mkfifo(tmp_path / 'fifo')
    with pytest.raises(ValueError):
        read_local(tmp_path / 'fifo')


def test_expectations_are_independent_closed_and_non_wildcard():
    data = {'scope': {'organization_id': 'org', 'account_id': 'account', 'environment': 'PAPER'},
            'policy_hashes': {name: 'a' * 64 for name in ('strategy', 'risk', 'imaf_definition', 'imaf_policy')}}
    assert parse_expectations(json.dumps(data).encode()) == data
    data['scope']['account_id'] = '*'
    with pytest.raises(ValueError):
        parse_expectations(json.dumps(data).encode())
    with pytest.raises(ValueError):
        parse_expectations(b'{"scope":{},"scope":{}}')


def test_review_clock_and_identity_rejected(tmp_path):
    write_bundle(tmp_path / 'r', artifacts())
    for reviewer, at in [('Rain', '2026-11-14T12:00:00.000Z'), ('<script>', NOW)]:
        with pytest.raises(ValueError):
            review(report_dir=str(tmp_path / 'r'), decision='accept', reviewer=reviewer, at=at)
    assert not (tmp_path / 'r' / 'human-review.json').exists()


def test_real_fixture_cli_round_trip(tmp_path):
    fixtures = Path(__file__).parents[1] / 'evaluation/trading_oversight/fixtures'
    expected = json.loads((fixtures / 'expectations.json').read_bytes())
    now = expected['now']
    for name in ('first', 'second'):
        inspect(input_path=str(fixtures / 'snapshot.json'),
                expectations_path=str(fixtures / 'expectations.json'), now=now,
                output_dir=str(tmp_path / name))
    assert (tmp_path / 'first/report.json').read_bytes() == (tmp_path / 'second/report.json').read_bytes()
    report = json.loads((tmp_path / 'first/report.json').read_bytes())
    assert report['assessment']['overall_status'] == 'BLOCKED'
    assert main(['review', '--report-dir', str(tmp_path / 'first'), '--decision', 'defer',
                 '--reviewer', 'Rain', '--at', now]) == 0


def test_cli_failure_has_no_payload_or_bundle(tmp_path, capsys):
    (tmp_path / 'invalid').write_text('{"private": "SECRET VALUE"}')
    assert main(['inspect', '--input', str(tmp_path / 'invalid'), '--expectations',
                 str(tmp_path / 'invalid'), '--now', NOW, '--output-dir', str(tmp_path / 'out')]) == 2
    assert 'SECRET VALUE' not in capsys.readouterr().err
    assert not (tmp_path / 'out').exists()


@pytest.mark.parametrize('location', ['manifest', 'report'])
def test_review_rejects_numeric_boolean_authority(tmp_path, location):
    files = artifacts()
    manifest = json.loads(files['manifest.json'])
    numeric = {'advisory_only': 1, 'execution_authorized': 0, 'live_authorized': 0}
    if location == 'manifest':
        manifest['authority'] = numeric
    else:
        report = json.loads(files['report.json'])
        report['authority'] = numeric
        files['report.json'] = json.dumps(report).encode()
        manifest['files']['report.json'] = sha256(files['report.json'])
    files['manifest.json'] = json.dumps(manifest).encode()
    write_bundle(tmp_path / 'r', files)
    with pytest.raises(ValueError):
        review(report_dir=str(tmp_path / 'r'), decision='accept', reviewer='Rain', at=NOW)
    assert not (tmp_path / 'r/human-review.json').exists()


def test_report_summary_and_findings_rendered_outside_details():
    page = artifacts()['report.html'].decode()
    primary, details = page.split('<details>', 1)
    assert 'Assessment summary' in primary
    assert 'Findings and human next steps' in primary
    assert 'not an all-clear' in primary
    assert 'Full evidence bindings' in details
