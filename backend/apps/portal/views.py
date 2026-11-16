from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound
from django.db import transaction
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.audit.context import client_context
from apps.audit.models import AuditEvent, record
from apps.analytics.services import record_activity
from apps.accounts.security import lock_login_ip
from apps.settings_app.models import GlobalSettings
from .identity import SESSION_KEY, provider, visitor, establish, renew, pseudonym


class VisitorLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, trim_whitespace=True)
    password = serializers.CharField(max_length=256, trim_whitespace=False, write_only=True)


@method_decorator(csrf_protect, name='dispatch')
class VisitorSessionView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # CMS identity never grants visitor identity or vice versa.

    @extend_schema(responses={200: dict})
    def get(self, request):
        identity = visitor(request)
        if identity:
            renew(request, GlobalSettings.current().session_seconds)
        else:
            request.session.pop(SESSION_KEY, None)
        response = Response({'authenticated': bool(identity), 'identity': identity.public() if identity else None,
            'mode': settings.PORTAL_AUTH_MODE, 'csrfToken': get_token(request),
            'network_access_granted': False})
        response['Cache-Control'] = 'no-store'
        return response

    @extend_schema(request=VisitorLoginSerializer, responses={200: dict, 403: dict, 429: dict, 503: dict})
    @transaction.atomic
    def post(self, request):
        serializer = VisitorLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cfg = GlobalSettings.current()
        context = client_context(request)
        # Serialize same-IP attempts across workers; never bypass N with parallel POSTs.
        lock_login_ip(context['ip'], 'portal')
        since = timezone.now() - timedelta(seconds=cfg.lockout_seconds)
        attempts = AuditEvent.objects.filter(action='portal_auth.failed', ip=context['ip'], created_at__gte=since).count()
        if attempts >= cfg.login_attempts:
            record(request, 'portal_auth.blocked')
            result = Response({'detail': 'Demasiados intentos. Espere antes de volver a intentarlo.'}, status=429)
            result['Retry-After'] = str(cfg.lockout_seconds)
            return result
        identity = provider().authenticate(**serializer.validated_data)
        if not identity:
            record(request, 'portal_auth.failed')
            return Response({'detail': 'Usuario o contraseña de demostración incorrectos.'}, status=403)
        establish(request, identity, cfg.session_seconds)
        record(request, 'portal_auth.login', metadata={'identity': pseudonym(identity), 'user_type': identity.user_type, 'demo': True})
        record_activity(request, 'login', event_type='access')
        return self.get(request)


@method_decorator(csrf_protect, name='dispatch')
class VisitorLogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=None, responses={200: dict})
    def post(self, request):
        if visitor(request):
            record(request, 'portal_auth.logout')
        request.session.pop(SESSION_KEY, None)
        # Rotation removes the old server session, preserving a separate CMS login.
        request.session.cycle_key()
        result = Response({'detail': 'Sesión del portal cerrada.', 'authenticated': False})
        result['Cache-Control'] = 'no-store'
        return result


def portal_html(request):
    path = Path(settings.PORTAL_HTML_FILE)
    if not path.exists():
        return HttpResponseNotFound('Compile el portal: node captive-portal/build.mjs')
    result = HttpResponse(path.read_bytes(), content_type='text/html; charset=utf-8')
    result['Cache-Control'] = 'no-cache'
    result['Referrer-Policy'] = 'no-referrer'
    result['Content-Security-Policy'] = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'none'; font-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    return result
