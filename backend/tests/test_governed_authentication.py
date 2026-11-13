import base64
from dataclasses import replace
import pytest
from app.services.governed_authentication import GovernedAuthenticationSession, password_record
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope

SCOPE = EvidenceScope(organization_id='org',collection='manuals',module='ir',topic='sre')


def headers(username='operator', password='synthetic-password'):
    return ('Basic '+base64.b64encode((username+':'+password).encode()).decode(),)


class Catalog:
    def __init__(self):
        salt, hashed = password_record('synthetic-password')
        self.row = dict(principal_id='principal',username='operator',credential_epoch=1,
                        permission_epoch=1,disabled=False,salt=salt,password_hash=hashed,
                        scopes=[SCOPE.model_dump()])
    def read_principal(self, username):
        return self.row.copy() if username == self.row['username'] else None


def test_authentication_owned_handle_and_no_secrets_in_handle():
    c=Catalog(); s=GovernedAuthenticationSession(c)
    p=s.authenticate(authorization_values=headers(),scope=SCOPE)
    assert p and s.recheck(p)
    assert 'salt' not in repr(p) and 'password' not in repr(p)
    assert not p.production_enabled and not p.release_authorized
    assert not s.recheck(replace(p))
    assert not s.recheck(p)


@pytest.mark.parametrize('mutation',[{'disabled':True},{'credential_epoch':2},{'permission_epoch':2},{'scopes':[]},{'salt':b'a'*16},{'password_hash':b'a'*32}])
def test_revocation_rotation_or_storage_change_is_terminal(mutation):
    c=Catalog(); s=GovernedAuthenticationSession(c)
    p=s.authenticate(authorization_values=headers(),scope=SCOPE)
    original=c.row.copy(); c.row.update(mutation)
    assert not s.recheck(p)
    c.row=original
    assert not s.recheck(p)


@pytest.mark.parametrize('values',[headers(password='wrong'),headers(username='unknown'),(),('X-Forwarded-User: operator',),headers()*2])
def test_bad_credentials_or_forwarded_identity_denied(values):
    s=GovernedAuthenticationSession(Catalog())
    assert s.authenticate(authorization_values=values,scope=SCOPE) is None
    assert s.authenticate(authorization_values=headers(),scope=SCOPE) is None


def test_scope_parameter_does_not_grant_permission():
    s=GovernedAuthenticationSession(Catalog())
    assert s.authenticate(authorization_values=headers(),scope=SCOPE.model_copy(update={'topic':'other'})) is None


def test_second_attempt_invalidates_issued_handle():
    s=GovernedAuthenticationSession(Catalog()); p=s.authenticate(authorization_values=headers(),scope=SCOPE)
    assert s.authenticate(authorization_values=headers(),scope=SCOPE) is None
    assert not s.recheck(p)


def test_record_changes_during_credential_verification_denied():
    c=Catalog(); original=c.read_principal; calls=[]
    def racing(username):
        calls.append(1)
        if len(calls)==2: c.row['permission_epoch']+=1
        return original(username)
    c.read_principal=racing
    assert GovernedAuthenticationSession(c).authenticate(authorization_values=headers(),scope=SCOPE) is None


@pytest.mark.parametrize('field,value',[('credential_epoch',True),('permission_epoch',0),('salt',b''),('disabled',1),('scopes',[{}])])
def test_malformed_storage_denied(field,value):
    c=Catalog();c.row[field]=value
    assert GovernedAuthenticationSession(c).authenticate(authorization_values=headers(),scope=SCOPE) is None
