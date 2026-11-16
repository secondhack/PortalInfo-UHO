from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.accounts.permissions import AuthorizedAccess, category_allowed, role_code
from apps.audit.models import record
from apps.catalogs.models import CatalogItem
from apps.settings_app.models import GlobalSettings
from .models import Content,Response as SurveyResponse
from .queries import content_queryset, allowed_categories, visible_publications, is_public, operation_map, public_data
from .serializers import ContentSerializer, SubmitResultSerializer, ReviewSerializer, VisibilitySerializer, PublicContentSerializer, PublicCategorySerializer
from .services import submit, review
from .surveys import survey_results,survey_submissions


class ContentFilter(filters.FilterSet):
    area=filters.NumberFilter(method='filter_area')
    date_from=filters.IsoDateTimeFilter(field_name='starts_at',lookup_expr='gte')
    date_to=filters.IsoDateTimeFilter(field_name='starts_at',lookup_expr='lte')
    event_from=filters.IsoDateTimeFilter(field_name='event__event_at',lookup_expr='gte')
    event_to=filters.IsoDateTimeFilter(field_name='event__event_at',lookup_expr='lte')
    visibility=filters.ChoiceFilter(choices=[('active','Activos'),('hidden','Ocultos'),('expired','Vencidos'),('future','Futuros')],method='filter_visibility')

    class Meta:
        model=Content
        fields=['category','state','manual_active','category__content_type']

    def filter_area(self,qs,name,value):
        return qs.filter(Q(news__area_id=value)|Q(event__area_id=value)|Q(service__area_id=value))

    def filter_visibility(self,qs,name,value):
        ids=visible_publications().values('content_id')
        if value=='active': return qs.filter(pk__in=ids)
        if value=='hidden': return qs.exclude(pk__in=ids)
        if value=='expired': return qs.filter(ends_at__lte=timezone.now())
        return qs.filter(starts_at__gt=timezone.now())


class ContentViewSet(viewsets.ModelViewSet):
    permission_classes=[AuthorizedAccess]
    serializer_class=ContentSerializer
    queryset=Content.objects.all()
    filterset_class=ContentFilter
    search_fields=['title','description']
    ordering_fields=['title','created_at','updated_at','starts_at','ends_at','event__event_at']
    ordering=['-updated_at','-id']

    def get_queryset(self):
        qs=content_queryset().filter(category__in=allowed_categories(self.request.user))
        if self.request.method not in ('GET','HEAD','OPTIONS'):
            qs=qs.select_for_update(of=('self',))
        return qs

    def get_serializer_context(self):
        context=super().get_serializer_context()
        context['public_ids']=set(visible_publications().values_list('content_id',flat=True))
        context['operations']=operation_map(self.request.user)
        return context

    @transaction.atomic
    def create(self,request,*args,**kwargs): return super().create(request,*args,**kwargs)

    @transaction.atomic
    def update(self,request,*args,**kwargs):
        item=self.get_object()
        self.check_operation(item,'edit')
        return super().update(request,*args,**kwargs)

    def check_operation(self,item,operation):
        if not category_allowed(self.request.user,item.category,operation):
            raise PermissionDenied('No tiene permiso para esta operación en la categoría.')

    @transaction.atomic
    def destroy(self,request,*args,**kwargs):
        item=self.get_object(); self.check_operation(item,'delete')
        item.deleted_at=timezone.now(); item.save(update_fields=['deleted_at','updated_at'])
        item.approvals.filter(state='pending').update(state='rejected',reason='Contenido eliminado.',reviewed_at=timezone.now())
        record(request,'content.delete',str(item.pk),{'version':item.revision})
        return Response(status=204)

    @extend_schema(request=None,responses=SubmitResultSerializer)
    @action(detail=True,methods=['post'])
    @transaction.atomic
    def submit(self,request,pk=None):
        item=self.get_object()
        # Revalidate current text, limits and nested data before sending.
        serializer=self.get_serializer(item,data={},partial=True,context={**self.get_serializer_context(),'operation':'submit'}); serializer.is_valid(raise_exception=True)
        warning=submit(item,request)
        return Response({'content':self.get_serializer(item).data,'warning':'Se alcanzó el máximo visible. Se permite enviar para aprobación; la API mantendrá el límite.' if warning else ''})

    @extend_schema(request=ReviewSerializer,responses=ContentSerializer)
    @action(detail=True,methods=['post'])
    @transaction.atomic
    def review(self,request,pk=None):
        item=self.get_object()
        data=ReviewSerializer(data=request.data); data.is_valid(raise_exception=True)
        if data.validated_data['approved']:
            validator=self.get_serializer(item,data={},partial=True); validator.is_valid(raise_exception=True)
        review(item,request,**data.validated_data)
        return Response(self.get_serializer(item).data)

    @extend_schema(request=VisibilitySerializer,responses=ContentSerializer)
    @action(detail=True,methods=['post'])
    @transaction.atomic
    def visibility(self,request,pk=None):
        item=self.get_object(); self.check_operation(item,'edit')
        data=VisibilitySerializer(data=request.data); data.is_valid(raise_exception=True)
        item.manual_active=data.validated_data['manual_active']; item.save(update_fields=['manual_active','updated_at'])
        record(request,'content.visibility',str(item.pk),{'manual_active':item.manual_active})
        return Response(self.get_serializer(item).data)

    @extend_schema(responses={200:dict})
    @action(detail=True,methods=['get'])
    def results(self,request,pk=None):
        item=self.get_object()
        if role_code(request.user) not in ('admin','superadmin'): raise PermissionDenied('Resultados reservados a Admin/Superadmin.')
        if item.category.content_type!='survey': raise ValidationError('Este contenido no es una encuesta.')
        from apps.analytics.periods import period_from
        period=period_from(request.query_params) if any(k in request.query_params for k in ['period','date_from','date_to','data_scope']) else None
        return Response(survey_results(item,period))

    @extend_schema(responses={200:dict})
    @action(detail=True,methods=['get'])
    def open_answers(self,request,pk=None):
        item=self.get_object()
        if role_code(request.user) not in ['admin','superadmin']:raise PermissionDenied('Respuestas abiertas reservadas a Admin/Superadmin.')
        from apps.analytics.periods import period_from
        period=period_from(request.query_params) if any(k in request.query_params for k in ['period','date_from','date_to','data_scope']) else None
        rows=SurveyResponse.objects.filter(submission__in=survey_submissions(item,period),question__kind='open').order_by('-created_at','-pk')
        question=request.query_params.get('question')
        if question:
            if not question.isdigit():raise ValidationError('Pregunta inválida.')
            rows=rows.filter(question_id=int(question))
        page=self.paginate_queryset(rows.values('id','question_id','value','created_at','submission__publication__version'))
        return self.get_paginated_response(page)

    @extend_schema(responses={200:dict})
    @action(detail=True,methods=['get'])
    def comparison(self,request,pk=None):
        from .services import snapshot
        item=self.get_object()
        return Response({'approved':item.live_publication.data if item.live_publication_id else None,'proposed':snapshot(item),
            'current_revision':item.revision,'state':item.state})

    @extend_schema(responses={200:dict})
    @action(detail=True,methods=['get'])
    def history(self,request,pk=None):
        item=self.get_object()
        return Response({'publications':list(item.publications.values('version','created_at','starts_at','ends_at')),
            'approvals':list(item.approvals.order_by('-id').values('version','state','reason','created_at','reviewed_at','reviewer_id'))})


class ContentMetadataView(APIView):
    @extend_schema(responses={200:dict})
    def get(self,request):
        cfg=GlobalSettings.current()
        categories=allowed_categories(request.user)
        return Response({'categories':[{'id':c.pk,'name':c.name,'slug':c.slug,'content_type':c.content_type,'active':c.active,
            'title_limit':c.title_limit,'description_limit':c.description_limit,'max_visible':c.max_visible,
            'required_fields':c.required_fields,'permissions':[op for op in ['view','create','edit','delete','submit'] if category_allowed(request.user,c,op)]} for c in categories],
            'areas':list(CatalogItem.objects.filter(active=True,catalog__slug__in=['areas','departamentos']).values('id','name')),
            'service_types':list(CatalogItem.objects.filter(active=True,catalog__slug='tipos-servicio').values('id','name')),
            'survey':{'max_questions':cfg.max_questions,'max_options':cfg.max_options,'allow_open_questions':cfg.allow_open_questions,'vote_requires_auth':cfg.vote_requires_auth}})


class PublicContentsView(APIView):
    permission_classes=[AllowAny]
    @extend_schema(responses=PublicContentSerializer(many=True))
    def get(self,request,slug):
        from apps.catalogs.models import Category
        get_object_or_404(Category,slug=slug)
        qs=visible_publications().filter(category__slug=slug)
        return Response([public_data(p) for p in qs])


class PublicCategoriesView(APIView):
    permission_classes=[AllowAny]
    @extend_schema(parameters=[OpenApiParameter(
        'include_contents',bool,description='false devuelve solo metadatos; true conserva el contrato completo.')],
        responses=PublicCategorySerializer(many=True))
    def get(self,request):
        from apps.catalogs.models import Category
        publications={}
        if request.query_params.get('include_contents','true').lower()!='false':
            for p in visible_publications(): publications.setdefault(p.category_id,[]).append(public_data(p))
        return Response([{'id':c.pk,'name':c.name,'slug':c.slug,'content_type':c.content_type,'dynamic':c.dynamic,'description':c.description,
            'max_visible':c.max_visible,'contents':publications.get(c.pk,[])} for c in Category.objects.filter(active=True,visible=True).order_by('id')])
