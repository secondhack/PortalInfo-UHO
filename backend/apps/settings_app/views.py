from django.conf import settings
from django.db import connection, transaction
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import StaffAccess, SuperAccess, role_code
from apps.audit.models import AuditEvent, record
from apps.audit.context import audit_summary
from apps.accounts.models import User
from apps.catalogs.models import Category
from apps.catalogs.serializers import CategorySerializer
from apps.content.models import Content
from .models import GlobalSettings


class SettingsSerializer(serializers.ModelSerializer):
    default_validity_days = serializers.IntegerField(min_value=1,max_value=3650)
    class Meta:
        model = GlobalSettings
        exclude = ['id']
        read_only_fields = ['updated_at']

    def validate_email_notifications(self, value):
        return value


class SettingsView(APIView):
    permission_classes = [StaffAccess]

    @extend_schema(responses=SettingsSerializer)
    def get(self, request):
        return Response(SettingsSerializer(GlobalSettings.current()).data)

    @extend_schema(request=SettingsSerializer, responses=SettingsSerializer)
    @transaction.atomic
    def patch(self, request):
        admin_fields = {'max_questions','max_options','allow_open_questions','vote_requires_auth','default_validity_days','portal_url'}
        if role_code(request.user) != 'superadmin' and set(request.data) - admin_fields:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Parámetros de seguridad reservados al Superadmin.')
        serializer = SettingsSerializer(GlobalSettings.current(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        before=audit_summary(serializer.instance,serializer.validated_data)
        serializer.save()
        record(request, 'configuration.update', metadata={'fields': list(serializer.validated_data),'before':before,'after':audit_summary(serializer.instance,serializer.validated_data)})
        return Response(serializer.data)


class HealthView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(responses={200: dict})
    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            return Response({'status':'ok','database':'postgresql','auth_provider':settings.AUTH_PROVIDER})
        except Exception:
            return Response({'status':'unavailable'},status=503)


class DashboardView(APIView):
    @extend_schema(responses={200: dict})
    def get(self, request):
        from apps.analytics.periods import period_from
        from apps.analytics.metrics import dashboard
        return Response(dashboard(request.user,period_from(request.query_params)))


class PublicConfigView(APIView):
    permission_classes = [AllowAny]
    @extend_schema(responses={200: dict})
    def get(self, request):
        categories = Category.objects.filter(active=True,visible=True)
        cfg=GlobalSettings.current()
        return Response({'sections': CategorySerializer(categories,many=True).data,
            'presentation':{'wifi_label':settings.PORTAL_WIFI_LABEL,'welcome_text':settings.PORTAL_WELCOME_TEXT},
            'survey':{'vote_requires_auth':cfg.vote_requires_auth,'max_questions':cfg.max_questions,'max_options':cfg.max_options,'allow_open_questions':cfg.allow_open_questions}})


class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = '__all__'


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [SuperAccess]
    serializer_class = AuditSerializer
    queryset = AuditEvent.objects.order_by('-id')
    from apps.analytics.filters import AuditFilter
    filterset_class = AuditFilter
    search_fields = ['resource','action']
    ordering_fields=['created_at','actor','action','entity']

    def get_queryset(self):
        qs=super().get_queryset()
        if 'period' in self.request.query_params:
            from apps.analytics.periods import period_from,during
            qs=during(qs,period_from(self.request.query_params))
        return qs
