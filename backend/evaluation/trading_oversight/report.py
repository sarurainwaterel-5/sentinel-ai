"""Deterministic advisory artifacts, deliberately without execution capabilities."""
from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path

from .reader import read_local

from .contracts import canonical, utc_time

AUTHORITY = {'advisory_only': True, 'execution_authorized': False, 'live_authorized': False}


def exact_authority(value: object) -> bool:
    return (isinstance(value, dict) and set(value) == set(AUTHORITY)
            and all(type(value[key]) is bool and value[key] is expected for key, expected in AUTHORITY.items()))


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def invalid(_):
        raise ValueError('nonfinite JSON number')
    try:
        value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=invalid)
    except (UnicodeError, RecursionError) as exc:
        raise ValueError('invalid JSON encoding or nesting') from exc
    if not isinstance(value, dict):
        raise ValueError('JSON object required')
    return value


def parse_expectations(raw: bytes) -> dict:
    value = strict_json(raw)
    if set(value) not in ({'scope', 'policy_hashes'}, {'scope', 'policy_hashes', 'now'}):
        raise ValueError('expectations require explicit scope and policy_hashes')
    scope, policies = value['scope'], value['policy_hashes']
    if not isinstance(scope, dict) or set(scope) != {'organization_id', 'account_id', 'environment'}:
        raise ValueError('invalid independently supplied scope')
    for key in ('organization_id', 'account_id'):
        if not isinstance(scope[key], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}', scope[key]):
            raise ValueError('scope requires exact bounded identifiers')
    if scope['environment'] not in ('PAPER', 'LOCAL_SIMULATION'):
        raise ValueError('only paper or local simulation permitted')
    if not isinstance(policies, dict) or set(policies) != {'strategy', 'risk', 'imaf_definition', 'imaf_policy'}:
        raise ValueError('invalid expected policy identities')
    if any(not isinstance(v, str) or not re.fullmatch('[0-9a-f]{64}', v) for v in policies.values()):
        raise ValueError('expected policy hashes must be lowercase SHA-256')
    if 'now' in value:
        utc_time(value['now'])
    return value


def render_report(report: dict) -> bytes:
    def escaped(value):
        if isinstance(value, (dict, list)):
            value = json.dumps(value, ensure_ascii=True, sort_keys=True)
        return html.escape(str(value))
    assessment = report.get('assessment', {})
    if not isinstance(assessment, dict):
        assessment = {}
    scope = assessment.get('scope', {})
    if not isinstance(scope, dict):
        scope = {}
    fields = [('Advisory status', assessment.get('overall_status', 'UNKNOWN')),
              ('Organization / account', str(scope.get('organization_id', 'Unknown')) + ' / ' + str(scope.get('account_id', 'Unknown'))),
              ('Environment', scope.get('environment', 'UNKNOWN')),
              ('Source as of', assessment.get('source_as_of', 'UNKNOWN')),
              ('Assessed at', report.get('assessed_at', 'UNKNOWN')),
              ('Human review', report.get('human_review', 'PENDING'))]
    fields.extend((label.title(), assessment.get(label, 'UNKNOWN'))
                  for label in ('integrity', 'strategy', 'risk', 'source', 'reconciliation'))
    summary = ''.join('<dt>' + escaped(label) + '</dt><dd>' + escaped(value) + '</dd>' for label, value in fields)
    rows = []
    findings = assessment.get('findings', [])
    for finding in findings if isinstance(findings, list) else []:
        if not isinstance(finding, dict):
            continue
        rows.append('<tr><td><strong>' + escaped(finding.get('code', 'UNKNOWN')) + '</strong><br>'
                    + escaped(finding.get('severity', 'UNKNOWN')) + '</td><td>'
                    + escaped(finding.get('observation', 'No observation supplied'))
                    + '<p><strong>Next step:</strong> ' + escaped(finding.get('human_next_step', 'Human review required'))
                    + '</p><p><strong>Missing evidence:</strong> ' + escaped(finding.get('missing_evidence', []))
                    + '</p><p><strong>Limitation:</strong> ' + escaped(finding.get('limitation', 'Unverified')) + '</p></td></tr>')
    if not rows:
        rows.append('<tr><td>UNKNOWN</td><td>No structured findings supplied. This is not an all-clear.</td></tr>')
    limitations = ''.join('<li>' + escaped(item) + '</li>' for item in report.get('limitations', []))
    encoded = html.escape(json.dumps(report, ensure_ascii=True, indent=2, sort_keys=True))
    return ("<!doctype html><html lang='en'><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<meta http-equiv='Content-Security-Policy' content=\"default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
            "<title>Offline paper oversight report</title><style>"
            "body{font:16px/1.55 system-ui,sans-serif;margin:0;background:#f2f5f8;color:#152536}"
            "main{max-width:1060px;margin:auto;padding:28px}h1{line-height:1.2}"
            ".notice{background:#fff0cc;border-left:5px solid #986600;padding:16px}"
            "section,details{background:white;border:1px solid #d5dfe7;border-radius:8px;padding:20px;margin:20px 0}"
            "dl{display:grid;grid-template-columns:minmax(140px,1fr) 3fr;gap:10px 20px}dt{font-weight:650}dd{margin:0;overflow-wrap:anywhere}"
            "table{border-collapse:collapse;width:100%;table-layout:fixed}td,th{text-align:left;vertical-align:top;padding:14px;border-bottom:1px solid #d5dfe7;overflow-wrap:anywhere}"
            "th:first-child{width:30%}td p{margin:.5em 0}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:13px}"
            "summary{cursor:pointer;font-weight:650}@media(max-width:600px){main{padding:12px}section,details{padding:12px}dl{grid-template-columns:1fr;gap:3px}dd{margin-bottom:12px}td,th{padding:8px}}"
            "</style><main><h1>Offline paper oversight report</h1>"
            "<p class='notice'><strong>Advisory only.</strong> Operator-supplied evidence; provider authenticity is unverified. "
            "This report grants no trading, broker, production or remediation authority.</p>"
            "<section><h2>Assessment summary</h2><dl>" + summary + '</dl></section>'
            '<section><h2>Findings and human next steps</h2><table><thead><tr><th>Finding / severity</th><th>Observation and response</th></tr></thead><tbody>'
            + ''.join(rows) + '</tbody></table></section><section><h2>Evidence and limitations</h2>'
            '<p>Input SHA-256: <code>' + escaped(report.get('input_sha256', 'UNKNOWN'))
            + '</code></p><ul>' + limitations + '</ul><p>Execution authorized: false. Live authorized: false. '
            'Human acceptance records review of this artifact only.</p></section>'
            '<details><summary>Full evidence bindings and assessment JSON</summary><pre>'
            + encoded + '</pre></details></main></html>').encode('utf-8')


def build_artifacts(assessment: dict, *, input_bytes: bytes, expectations_bytes: bytes, now: str) -> dict[str, bytes]:
    utc_time(now)
    report = {
        'schema_version': 'sentinel.trading.oversight.report.v0.1',
        'input_sha256': sha256(input_bytes), 'expectations_sha256': sha256(expectations_bytes),
        'assessed_at': now, 'assessment': assessment, 'human_review': 'PENDING',
        'checker_source_sha256': {
            name: sha256(read_local(Path(__file__).parent / name))
            for name in ('contracts.py', 'evaluator.py', 'reader.py', 'report.py', 'cli.py')
        },
        'authority': dict(AUTHORITY),
        'limitations': ['Offline operator-supplied artifact; provider authenticity is not established.',
                        'Human review records accuracy only and cannot authorize trading.'],
    }
    files = {'report.json': canonical(report).encode('utf-8'), 'report.html': render_report(report)}
    manifest = {'schema_version': 'sentinel.trading.oversight.bundle.v0.1',
                'input_sha256': report['input_sha256'],
                'expectations_sha256': report['expectations_sha256'],
                'files': {name: sha256(data) for name, data in files.items()},
                'authority': dict(AUTHORITY)}
    files['manifest.json'] = canonical(manifest).encode('utf-8')
    return files
