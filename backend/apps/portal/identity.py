"""Visitor identity is independent of Django's administrative authentication."""
import json
import time
from dataclasses import dataclass
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.utils.crypto import salted_hmac
from apps.accounts.providers import ProviderUnavailable
from apps.accounts.security import dummy_password_hash

SESSION_KEY = 'portal_visitor'


@dataclass(frozen=True)
class VisitorIdentity:
    identifier: str
    full_name: str
    user_type: str
    demo: bool = True

    def public(self):
        return {'identifier': self.identifier, 'full_name': self.full_name,
                'user_type': self.user_type, 'demo': self.demo, 'photo': None}


def demo_users():
    try:
        return json.loads(settings.PORTAL_DEMO_USERS_FILE.read_text(encoding='utf-8'))
    except (FileNotFoundError, ValueError):
        return {}


class DemoVisitorProvider:
    def authenticate(self, username, password):
        row = demo_users().get(username)
        valid = check_password(password, row['password_hash']) if row else check_password(password, dummy_password_hash())
        if valid and row and row.get('active', False):
            return VisitorIdentity(username, row['full_name'], row['user_type'])
        return None


class InstitutionalVisitorProvider:
    """Implement only after receiving the authorized AGA_AUTH/pfSense contract.

    Authentication must yield a server-verified identifier/name/type. A separate
    network adapter must grant/revoke access; identity alone never grants Internet.
    No endpoint, token format, photo source or firewall protocol is assumed here.
    """
    def authenticate(self, username, password):
        raise ProviderUnavailable('Integración institucional pendiente del contrato AGA_AUTH y pfSense.')


def provider():
    if settings.PORTAL_AUTH_MODE == 'demo' and not settings.PRODUCTION:
        return DemoVisitorProvider()
    return InstitutionalVisitorProvider()


def visitor(request):
    state = request.session.get(SESSION_KEY)
    if not isinstance(state, dict) or state.get('expires', 0) <= time.time():
        return None
    if settings.PORTAL_AUTH_MODE != 'demo' or settings.PRODUCTION:
        return None
    row = demo_users().get(state.get('identifier'))
    if not row or not row.get('active') or state.get('credential_stamp') != salted_hmac('portal-credential', row['password_hash']).hexdigest():
        return None
    return VisitorIdentity(state['identifier'], row['full_name'], row['user_type'])


def establish(request, identity, seconds):
    request.session.cycle_key()
    row = demo_users()[identity.identifier]
    request.session[SESSION_KEY] = {'identifier': identity.identifier, 'expires': time.time() + seconds,
        'credential_stamp': salted_hmac('portal-credential', row['password_hash']).hexdigest()}
    request.session.set_expiry(seconds)


def renew(request, seconds):
    state = dict(request.session[SESSION_KEY], expires=time.time() + seconds)
    request.session[SESSION_KEY] = state


def pseudonym(identity):
    return 'portal-demo:' + salted_hmac('portal-visitor', identity.identifier).hexdigest()
