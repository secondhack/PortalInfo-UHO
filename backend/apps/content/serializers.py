from rest_framework import serializers
from datetime import timedelta
from django.utils import timezone
from apps.accounts.permissions import category_allowed, role_code
from apps.catalogs.models import Category
from apps.settings_app.models import GlobalSettings
from .models import Content
from .queries import is_public
from .services import details_data, save_content
from .validation import NewsDetails, EventDetails, ServiceDetails, SurveyDetails, validity_dates


class ContentSerializer(serializers.ModelSerializer):
    validity = serializers.ChoiceField(choices=['default','today','three_days','week','month','always','custom'], required=False)
    details = serializers.JSONField(required=False)
    category_name = serializers.CharField(source='category.name',read_only=True)
    content_type = serializers.CharField(source='category.content_type',read_only=True)
    public_visible = serializers.SerializerMethodField()
    has_published_version = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model=Content
        fields=['id','category','category_name','content_type','title','description','author','state','revision',
            'validity','starts_at','ends_at','manual_active','extra_fields','created_at','updated_at','submitted_at',
            'details','public_visible','has_published_version','permissions']
        read_only_fields=['author','state','revision','created_at','updated_at','submitted_at']

    def get_public_visible(self,item)->bool:
        ids=self.context.get('public_ids')
        return item.pk in ids if ids is not None else is_public(item)

    def get_has_published_version(self,item)->bool:
        return bool(item.live_publication_id)

    def get_permissions(self,item)->list[str]:
        if 'operations' in self.context:
            operations=self.context['operations']
            return ['view','create','edit','delete','submit'] if operations is None else sorted(operations.get(item.category_id,set()))
        user=self.context['request'].user
        return [op for op in ['view','create','edit','delete','submit'] if category_allowed(user,item.category,op)]

    def to_representation(self,instance):
        data=super().to_representation(instance)
        data['details']=details_data(instance)
        return data

    def validate(self,attrs):
        forbidden={'state','author','revision','live_publication','deleted_at','seed_key'} & set(self.initial_data)
        if forbidden: raise serializers.ValidationError('Estado y autor se gestionan mediante el flujo editorial.')
        instance=self.instance
        category=attrs.get('category',instance.category if instance else None)
        if not category: raise serializers.ValidationError({'category':'Seleccione una categoría.'})
        request=self.context['request']
        operation=self.context.get('operation','edit' if instance else 'create')
        if not category_allowed(request.user,category,operation):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No tiene permiso para operar en esta categoría.')
        if instance and category.pk!=instance.category_id and category.content_type!=instance.category.content_type:
            raise serializers.ValidationError({'category':'Solo puede trasladar contenido entre categorías del mismo tipo.'})
        attrs['category']=category
        for key,limit in [('title',category.title_limit),('description',category.description_limit)]:
            value=attrs.get(key,getattr(instance,key,'') if instance else '')
            if not value.strip() or len(value)>limit:
                raise serializers.ValidationError({key:f'El campo es obligatorio y admite hasta {limit} caracteres.'})
        extra=attrs.get('extra_fields',instance.extra_fields if instance else {})
        if not isinstance(extra,dict) or len(extra)>50 or any(not isinstance(v,str) or len(v)>category.description_limit for v in extra.values()):
            raise serializers.ValidationError({'extra_fields':'Utilice campos de texto dentro del límite de descripción (máximo 50 campos). '})
        if any(not extra.get(key,'').strip() for key in category.required_fields):
            raise serializers.ValidationError({'extra_fields':'Complete todos los campos requeridos por la categoría.'})
        if any(k in attrs for k in ['validity','starts_at','ends_at']) or not instance:
            validity=attrs.get('validity',instance.validity if instance else 'default')
            starts=attrs.get('starts_at',instance.starts_at if instance else None)
            ends=attrs.get('ends_at',instance.ends_at if instance else None)
            if validity=='default':
                attrs['validity']='custom'
                attrs['starts_at']=timezone.now()
                attrs['ends_at']=attrs['starts_at']+timedelta(days=GlobalSettings.current().default_validity_days)
            else:
                attrs['starts_at'],attrs['ends_at']=validity_dates(validity,starts,ends)
        kind=category.content_type
        raw=attrs.pop('details',None)
        if raw is None: raw=details_data(instance) if instance else {}
        detail_class={'news':NewsDetails,'event':EventDetails,'service':ServiceDetails,'survey':SurveyDetails}.get(kind)
        if detail_class:
            validator=detail_class(data=raw,context={'config':GlobalSettings.current()})
            validator.is_valid(raise_exception=True)
            attrs['details']=dict(validator.validated_data)
        else:
            if raw: raise serializers.ValidationError({'details':'Use extra_fields para categorías genéricas.'})
            attrs['details']={}
        return attrs

    def create(self,validated_data):
        return save_content(self,self.context['request'])

    def update(self,instance,validated_data):
        return save_content(self,self.context['request'])


class SubmitResultSerializer(serializers.Serializer):
    content=ContentSerializer()
    warning=serializers.CharField(allow_blank=True)


class ReviewSerializer(serializers.Serializer):
    approved=serializers.BooleanField()
    reason=serializers.CharField(required=False,allow_blank=True,max_length=2000,default='')


class VisibilitySerializer(serializers.Serializer):
    manual_active=serializers.BooleanField()


class PublicContentSerializer(serializers.Serializer):
    id=serializers.IntegerField()
    category=serializers.IntegerField()
    category_slug=serializers.CharField()
    type=serializers.CharField()
    title=serializers.CharField()
    description=serializers.CharField()
    starts_at=serializers.DateTimeField()
    ends_at=serializers.DateTimeField(allow_null=True)
    version=serializers.IntegerField()
    details=serializers.JSONField()
    extra_fields=serializers.JSONField()


class PublicCategorySerializer(serializers.Serializer):
    id=serializers.IntegerField()
    name=serializers.CharField()
    slug=serializers.CharField()
    content_type=serializers.CharField()
    dynamic=serializers.BooleanField()
    description=serializers.CharField()
    max_visible=serializers.IntegerField()
    contents=PublicContentSerializer(many=True)
