from django.conf import settings
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema,extend_schema_view
from rest_framework import serializers,viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle
from rest_framework.views import APIView
from apps.accounts.permissions import StaffAccess
from apps.audit.context import client_context
from apps.audit.models import record
from apps.content.models import Content
from .models import AccessLog,SecurityAlert
from .services import record_activity
from .metrics import portal_metrics
from .periods import PeriodSerializer,period_from,during,data_scope
from .security import detect_alerts


class ViewInput(serializers.Serializer):
    section=serializers.SlugField(max_length=100)
    content=serializers.IntegerField(min_value=1,required=False,allow_null=True)
    def validate(self,attrs):
        if set(self.initial_data)-{'section','content'}:raise serializers.ValidationError('Solo se admiten sección y contenido; la identidad se obtiene en el servidor.')
        return attrs


class ViewThrottle(SimpleRateThrottle):
    scope='portal_views';rate='60/min'
    def get_cache_key(self,request,view):return self.cache_format%{'scope':self.scope,'ident':client_context(request)['ip']}


@method_decorator(csrf_protect,name='dispatch')
class RecordView(APIView):
    permission_classes=[AllowAny]
    throttle_classes=[ViewThrottle]
    @extend_schema(request=ViewInput,responses={201:dict})
    def post(self,request):
        serializer=ViewInput(data=request.data);serializer.is_valid(raise_exception=True)
        record_activity(request,serializer.validated_data['section'],serializer.validated_data.get('content'))
        return Response({'detail':'Visualización registrada.'},status=201)


class DemoPortalAccessView(APIView):
    @extend_schema(request=None,responses={201:dict})
    def post(self,request):
        if settings.PRODUCTION or settings.AUTH_PROVIDER!='demo':raise PermissionDenied('La simulación de acceso solo está disponible en demo.')
        record_activity(request,'login',event_type='access')
        return Response({'detail':'Acceso de prueba con identidad de la sesión demo; no concede acceso a Internet.'},status=201)


class StatisticsView(APIView):
    permission_classes=[StaffAccess]
    @extend_schema(parameters=[PeriodSerializer],responses={200:dict})
    def get(self,request):return Response(portal_metrics(period_from(request.query_params)))


class AccessLogSerializer(serializers.ModelSerializer):
    class Meta:
        model=AccessLog;fields='__all__'


@extend_schema_view(list=extend_schema(parameters=[PeriodSerializer]))
class AccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes=[StaffAccess]
    serializer_class=AccessLogSerializer
    queryset=AccessLog.objects.order_by('-created_at','-pk')
    filterset_fields=['uid','user_type','device','event_type','section','content']
    search_fields=['uid','section','user_agent']
    ordering_fields=['created_at','uid','device','section']
    ordering=['-created_at','-pk']
    def get_queryset(self):return data_scope(during(super().get_queryset(),period_from(self.request.query_params)),period_from(self.request.query_params))


class AlertFilter(filters.FilterSet):
    reviewed=filters.BooleanFilter(field_name='reviewed_at',lookup_expr='isnull',exclude=True)
    class Meta:
        model=SecurityAlert;fields=['priority','kind','uid','reviewed']


class SecurityAlertSerializer(serializers.ModelSerializer):
    class Meta:
        model=SecurityAlert;fields=['id','uid','kind','priority','window_start','window_end','evidence','reviewed_at','reviewed_by','demo','created_at']
        read_only_fields=fields


@extend_schema_view(list=extend_schema(parameters=[PeriodSerializer]))
class SecurityAlertViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes=[StaffAccess]
    serializer_class=SecurityAlertSerializer
    queryset=SecurityAlert.objects.order_by('-created_at','-id')
    filterset_class=AlertFilter
    search_fields=['uid','kind']
    ordering_fields=['created_at','priority','window_start']
    @extend_schema(request=None,parameters=[PeriodSerializer],responses={200:dict})
    @action(detail=False,methods=['post'])
    def scan(self,request):
        count=detect_alerts(period_from(request.query_params));record(request,'security.scan',metadata={'new_alerts':count})
        return Response({'created':count})

    @extend_schema(request=None,responses=SecurityAlertSerializer)
    @action(detail=True,methods=['post'])
    def mark_reviewed(self,request,pk=None):
        alert=self.get_object()
        if alert.reviewed_at is None:
            alert.reviewed_at=timezone.now();alert.reviewed_by=request.user;alert.save(update_fields=['reviewed_at','reviewed_by'])
            record(request,'security.review',str(alert.pk),{'before':'unreviewed','after':'reviewed'})
        return Response(self.get_serializer(alert).data)

    def get_queryset(self):
        period=period_from(self.request.query_params)
        return data_scope(super().get_queryset().filter(window_end__gt=period['start'],window_start__lt=period['end']),period)
