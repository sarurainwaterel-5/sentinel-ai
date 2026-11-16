"""Bounded versioned records; source claims are never self-validating."""
import hashlib
import json
import math
import re
from datetime import datetime, timezone

class SREError(ValueError):
    """Bounded public error codes, never raw collector/database exceptions."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def identifier(value):
    if type(value) is not str or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}', value) or value.lower() in {'all','admin-all'} or value.startswith(('sk-','ghp_')):
        raise SREError('INVALID_IDENTIFIER')
    return value


def timestamp(value):
    try:
        if type(value) is not str or len(value)>40: raise ValueError()
        t=datetime.fromisoformat(value.replace('Z','+00:00'))
        if t.tzinfo is None or t.utcoffset().total_seconds()!=0: raise ValueError()
        return t.astimezone(timezone.utc).isoformat(timespec='microseconds').replace('+00:00','Z')
    except (ValueError,TypeError,OverflowError): raise SREError('INVALID_UTC_TIMESTAMP') from None


def evidence(value):
    if type(value) is not str or not re.fullmatch('sha256:[a-f0-9]{64}',value): raise SREError('INVALID_EVIDENCE_REFERENCE')
    return value


def record(value, required, optional=()):
    if type(value) is not dict or set(value)-set(required)-set(optional) or not set(required)<=set(value): raise SREError('INVALID_RECORD_SCHEMA')
    try:
        text=canonical(value)
        if len(text)>8192: raise SREError('RECORD_BUDGET')
        if re.search(r'(?i)(bearer\s|password\s*[:=]|api[_-]?key\s*[:=]|-----BEGIN|sk-[a-z0-9]{12}|ghp_[a-z0-9]{12})',text): raise SREError('SENSITIVE_PAYLOAD_REJECTED')
        result=json.loads(text)
    except (TypeError,ValueError,RecursionError): raise SREError('INVALID_OR_SENSITIVE_RECORD') from None
    if result.get('schema_version')!=1 or type(result.get('schema_version')) is not int: raise SREError('UNSUPPORTED_RECORD_VERSION')
    for key in ('tenant_id','application_id'): identifier(result[key])
    return result


def policy(value):
    if type(value) is not dict or set(value)!={'required_checks','max_age_seconds'}: raise SREError('INVALID_HEALTH_POLICY')
    checks=value['required_checks']; age=value['max_age_seconds']
    if type(checks) is not list or not 1<=len(checks)<=32 or any(type(c) is not str for c in checks) or len(set(checks))!=len(checks) or type(age) is not int or not 1<=age<=86400: raise SREError('INVALID_HEALTH_POLICY')
    for x in checks: identifier(x)
    return json.loads(canonical(value))


def service_record(value):
    r=record(value,('schema_version','tenant_id','application_id','service_id','service_name','service_type','environment','monitoring_enabled','health_policy','registered_at','updated_at','configuration_ref'))
    identifier(r['service_id'])
    if type(r['service_name']) is not str or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9 ._-]{0,127}',r['service_name']): raise SREError('INVALID_SERVICE_NAME')
    if r['service_type'] not in ('API','WORKER','DATABASE','FRONTEND','QUEUE','AUTH','OTHER') or r['environment'] not in ('local','development','staging','production') or type(r['monitoring_enabled']) is not bool: raise SREError('INVALID_SERVICE_CONFIG')
    if r['monitoring_enabled'] and r['environment'] not in ('local','development'): raise SREError('EXTERNAL_MONITORING_DISABLED')
    r['health_policy']=policy(r['health_policy']);r['registered_at']=timestamp(r['registered_at']);r['updated_at']=timestamp(r['updated_at']); evidence(r['configuration_ref'])
    if r['updated_at']<r['registered_at']: raise SREError('CONFIGURATION_TIME_ORDER')
    return r


OBSERVATION_TYPES=('SERVICE_HEALTH','APPLICATION_ERROR','STRUCTURED_LOG','PERFORMANCE_METRIC','DEPENDENCY_FAILURE','DEPLOYMENT_EVENT','RESOURCE_USAGE','SECURITY_EVENT')

def observation_record(value):
    r=record(value,('schema_version','tenant_id','application_id','service_id','observation_id','observation_type','source_id','source_timestamp','ingested_at','evidence_ref','severity','data_quality','correlation_id','payload'))
    for k in ('service_id','observation_id','source_id','correlation_id'): identifier(r[k])
    if r['observation_type'] not in OBSERVATION_TYPES or r['severity'] not in ('INFO','WARNING','ERROR','CRITICAL') or r['data_quality'] not in ('SOURCE_CLAIM','INVALID'): raise SREError('UNTRUSTED_QUALITY_OR_TYPE')
    r['source_timestamp']=timestamp(r['source_timestamp']);r['ingested_at']=timestamp(r['ingested_at']);evidence(r['evidence_ref'])
    if r['source_timestamp']>r['ingested_at']: raise SREError('FUTURE_SOURCE_TIMESTAMP')
    p=r['payload']
    if type(p) is not dict: raise SREError('INVALID_PAYLOAD')
    if r['observation_type']=='SERVICE_HEALTH':
        if set(p)!={'check_id','outcome'} or p['outcome'] not in ('PASS','PARTIAL','FAIL','COLLECTOR_ERROR'): raise SREError('INVALID_HEALTH_PAYLOAD')
        identifier(p['check_id'])
    else:
        if not {'event_code'}<=set(p) or set(p)-{'event_code','metric_name','value','unit'}: raise SREError('FREEFORM_PAYLOAD_NOT_SUPPORTED')
        for k in set(p)-{'value'}: identifier(p[k])
        if 'value' in p and (type(p['value']) not in (int,float) or not math.isfinite(p['value']) or abs(p['value'])>1e15): raise SREError('INVALID_METRIC')
    return r
