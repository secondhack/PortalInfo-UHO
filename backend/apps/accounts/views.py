from datetime import timedelta
from django.contrib.auth import login, logout
from django.db import transaction
from django.db.models import Q
from django.middleware.csrf import get_token
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.audit.models import AuditEvent, record
from apps.audit.context import audit_summary,client_context
from apps.settings_app.models import GlobalSettings
from .models import User, Role, Grant
from .serializers import UserSerializer, RoleSerializer, GrantSerializer, LoginSerializer
from .permissions import StaffAccess, SuperAccess, role_code
from .providers import get_provider
from .security import lock_login_ip


class CSRFView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(responses={200: dict})
    def get(self, request):
        return Response({'csrfToken': get_token(request)})


@method_decorator(csrf_protect, name='dispatch')
class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(request=LoginSerializer, responses={200: UserSerializer})
    @transaction.atomic
    def post(self, request):
        data = LoginSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        cfg = GlobalSettings.current()
        ip = client_context(request)['ip']
        lock_login_ip(ip, 'cms')
        since = timezone.now() - timedelta(seconds=cfg.lockout_seconds)
        attempts = AuditEvent.objects.filter(action='auth.failed', ip=ip, created_at__gte=since).count()
        if attempts >= cfg.login_attempts:
            record(request, 'auth.blocked')
            response = Response({'detail': 'Demasiados intentos. Espere antes de volver a intentarlo.'}, status=429)
            response['Retry-After'] = str(cfg.lockout_seconds)
            return response
        user = get_provider().authenticate(data.validated_data['email'].lower(), data.validated_data['password'])
        if not user:
            record(request, 'auth.failed')
            return Response({'detail': 'No tiene acceso a este sistema'}, status=403)
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        request.session.set_expiry(cfg.session_seconds)
        record(request, 'auth.login')
        return Response(UserSerializer(user).data)


@method_decorator(csrf_protect, name='dispatch')
class LogoutView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(request=None, responses={200: dict})
    def post(self, request):
        record(request, 'auth.logout')
        logout(request)
        return Response({'detail': 'Sesión cerrada.'})


class MeView(APIView):
    @extend_schema(responses=UserSerializer)
    def get(self, request):
        if not request.user.authorized:
            raise PermissionDenied('No tiene acceso a este sistema')
        cfg = GlobalSettings.current()
        request.session.set_expiry(cfg.session_seconds)
        return Response(UserSerializer(request.user).data)


class AuditedViewSet(viewsets.ModelViewSet):
    permission_classes = [StaffAccess]

    @transaction.atomic
    def perform_create(self, serializer):
        instance = serializer.save()
        record(self.request, f'{instance._meta.model_name}.create', str(instance.pk))

    @transaction.atomic
    def perform_update(self, serializer):
        before=audit_summary(serializer.instance,serializer.validated_data)
        instance = serializer.save()
        record(self.request, f'{instance._meta.model_name}.update', str(instance.pk),
            {'fields': [k for k in serializer.validated_data if k != 'password'],'before':before,'after':audit_summary(instance,serializer.validated_data)})

    @transaction.atomic
    def perform_destroy(self, instance):
        from django.db.models.deletion import ProtectedError
        resource = str(instance.pk)
        name = instance._meta.model_name
        try:
            instance.delete()
        except ProtectedError:
            raise ValidationError('El registro está en uso; desactívelo en lugar de eliminarlo.')
        record(self.request, f'{name}.delete', resource)


class UserViewSet(AuditedViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.select_related('role').prefetch_related('categories').order_by('id')
    search_fields = ['email']
    filterset_fields = ['role', 'is_active', 'authorized']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(role__code='gestor') if role_code(self.request.user) == 'admin' else qs

    def perform_destroy(self, instance):
        if instance.protected or role_code(instance) == 'superadmin':
            raise PermissionDenied('El Superadmin no puede eliminarse.')
        super().perform_destroy(instance)


class RoleViewSet(AuditedViewSet):
    queryset = Role.objects.order_by('id')
    serializer_class = RoleSerializer
    http_method_names = ['get', 'patch', 'head', 'options']

    def get_permissions(self):
        return [StaffAccess()] if self.action in ['list','retrieve'] else [SuperAccess()]


class GrantViewSet(AuditedViewSet):
    queryset = Grant.objects.order_by('id')
    serializer_class = GrantSerializer
    filterset_fields = ['user','role','category','operation']

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(user__role__code='gestor') if role_code(self.request.user) == 'admin' else qs
