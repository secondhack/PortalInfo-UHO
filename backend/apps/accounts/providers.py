from abc import ABC, abstractmethod
from django.conf import settings
from django.contrib.auth.hashers import check_password
from .security import dummy_password_hash
from rest_framework.exceptions import APIException
from .models import User


class IdentityProvider(ABC):
    @abstractmethod
    def authenticate(self, email, password):
        """Return an authorized local identity or None; never persist supplied credentials."""


class DemoAuthProvider(IdentityProvider):
    def authenticate(self, email, password):
        user = User.objects.filter(email=email, demo=True).first()
        valid = user.check_password(password) if user else check_password(password, dummy_password_hash())
        return user if valid and user and user.is_active and user.authorized and user.role_id else None


class ProviderUnavailable(APIException):
    status_code = 503
    default_detail = 'AGA_AUTH pendiente de contrato institucional de integración.'


class AGAAuthProvider(IdentityProvider):
    def authenticate(self, email, password):
        raise ProviderUnavailable()


def get_provider():
    if settings.AUTH_PROVIDER == 'demo' and not settings.PRODUCTION:
        return DemoAuthProvider()
    if settings.AUTH_PROVIDER == 'aga':
        return AGAAuthProvider()
    raise ProviderUnavailable('Proveedor de identidad desconocido.')
