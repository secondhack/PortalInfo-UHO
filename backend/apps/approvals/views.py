from django.db import transaction
from django.db.models import F
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework import serializers,viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from apps.accounts.permissions import StaffAccess
from apps.content.models import Content
from apps.content.serializers import ContentSerializer,ReviewSerializer
from apps.content.services import review
from apps.content.queries import content_queryset
from .models import Approval


class ApprovalFilter(filters.FilterSet):
    category=filters.NumberFilter(field_name='content__category_id')
    author=filters.NumberFilter(field_name='requested_by_id')
    date_from=filters.IsoDateTimeFilter(field_name='created_at',lookup_expr='gte')
    date_to=filters.IsoDateTimeFilter(field_name='created_at',lookup_expr='lte')
    class Meta:model=Approval;fields=['state','category','author']


class ApprovalSerializer(serializers.ModelSerializer):
    title=serializers.CharField(source='content.title',read_only=True)
    category=serializers.CharField(source='content.category.name',read_only=True)
    author=serializers.CharField(source='requested_by.email',read_only=True)
    content_type=serializers.CharField(source='content.category.content_type',read_only=True)
    approved_version=serializers.SerializerMethodField()
    current_revision=serializers.IntegerField(source='content.revision',read_only=True)
    class Meta:
        model=Approval
        fields=['id','content','title','category','author','content_type','version','state','reason','reviewer','created_at','reviewed_at','proposal','approved_version','current_revision']
        read_only_fields=fields
    def get_approved_version(self,obj)->dict|None:
        return obj.content.live_publication.data if obj.content.live_publication_id else None


class ApprovalViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes=[StaffAccess]
    serializer_class=ApprovalSerializer
    queryset=Approval.objects.all()
    filterset_class=ApprovalFilter
    search_fields=['content__title','proposal__title']
    ordering_fields=['created_at','reviewed_at','content__title']
    ordering=['created_at','id']
    def get_queryset(self):
        qs=Approval.objects.select_related('content__category','content__live_publication','requested_by').filter(content__deleted_at__isnull=True)
        if self.action=='list' and 'state' not in self.request.query_params:qs=qs.filter(state='pending')
        return qs

    @extend_schema(request=ReviewSerializer,responses=ApprovalSerializer)
    @action(detail=True,methods=['post'])
    @transaction.atomic
    def decide(self,request,pk=None):
        approval=self.get_object()
        item=Content.objects.select_for_update().get(pk=approval.content_id,deleted_at__isnull=True)
        if item.revision!=approval.version:raise ValidationError('La solicitud corresponde a una revisión sustituida.')
        data=ReviewSerializer(data=request.data);data.is_valid(raise_exception=True)
        if data.validated_data['approved']:
            serializer=ContentSerializer(item,data={},partial=True,context={'request':request});serializer.is_valid(raise_exception=True)
        # Only the explicitly selected request can be decided, never a later resubmission.
        latest=item.approvals.filter(version=item.revision).order_by('-id').first()
        if not latest or latest.pk!=approval.pk:raise ValidationError('La solicitud fue sustituida.')
        review(item,request,**data.validated_data)
        approval.refresh_from_db()
        return Response(self.get_serializer(approval).data)

    @extend_schema(responses={200:dict})
    @action(detail=False,methods=['get'])
    def summary(self,request):
        return Response({'pending':Approval.objects.filter(state='pending',content__deleted_at__isnull=True).count()})

    @extend_schema(responses={200:dict})
    @action(detail=False,methods=['get'])
    def authors(self,request):
        rows=Approval.objects.filter(content__deleted_at__isnull=True).order_by('requested_by__email').values('requested_by_id','requested_by__email').distinct()
        return Response([{'id':row['requested_by_id'],'email':row['requested_by__email']} for row in rows])
