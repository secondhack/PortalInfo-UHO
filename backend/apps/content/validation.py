from datetime import datetime, time, timedelta
from urllib.parse import urlsplit
from django.utils import timezone
from rest_framework import serializers
from apps.catalogs.models import CatalogItem


class SafeURL(serializers.URLField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if value:
            parsed=urlsplit(value)
            if parsed.scheme not in ('http','https') or parsed.username or parsed.password:
                raise serializers.ValidationError('Utilice un enlace http o https sin credenciales.')
        return value


class NewsDetails(serializers.Serializer):
    area = serializers.PrimaryKeyRelatedField(queryset=CatalogItem.objects.filter(active=True,catalog__slug__in=['areas','departamentos']))
    external_url = SafeURL(required=False,allow_blank=True,default='')


class EventDetails(serializers.Serializer):
    area = serializers.PrimaryKeyRelatedField(queryset=CatalogItem.objects.filter(active=True,catalog__slug__in=['areas','departamentos']))
    event_at = serializers.DateTimeField()
    contact = serializers.CharField(max_length=250)
    invitation_url = SafeURL(required=False,allow_blank=True,default='')


class ServiceDetails(serializers.Serializer):
    area = serializers.PrimaryKeyRelatedField(queryset=CatalogItem.objects.filter(active=True,catalog__slug__in=['areas','departamentos']))
    access_url = SafeURL()
    service_type = serializers.PrimaryKeyRelatedField(queryset=CatalogItem.objects.filter(active=True,catalog__slug='tipos-servicio'),required=False,allow_null=True)


class OptionInput(serializers.Serializer):
    text = serializers.CharField(max_length=300)


class QuestionInput(serializers.Serializer):
    text = serializers.CharField(max_length=500)
    kind = serializers.ChoiceField(choices=['single','multiple','open'])
    required = serializers.BooleanField(default=True)
    options = OptionInput(many=True,required=False,default=list)


class SurveyDetails(serializers.Serializer):
    external_url = SafeURL(required=False,allow_blank=True,default='')
    questions = QuestionInput(many=True,required=False,default=list)

    def validate(self, attrs):
        cfg=self.context['config']
        questions=attrs['questions']
        if attrs['external_url']:
            if questions:
                raise serializers.ValidationError('Una encuesta externa no debe contener preguntas internas.')
            return attrs
        if not 1<=len(questions)<=cfg.max_questions:
            raise serializers.ValidationError(f'Incluya entre 1 y {cfg.max_questions} preguntas.')
        for q in questions:
            if q['kind']=='open':
                if not cfg.allow_open_questions or q['options']:
                    raise serializers.ValidationError('Pregunta abierta deshabilitada o con opciones incompatibles.')
            elif not 2<=len(q['options'])<=cfg.max_options:
                raise serializers.ValidationError(f'Cada pregunta de selección requiere entre 2 y {cfg.max_options} opciones.')
            texts=[o['text'].casefold() for o in q['options']]
            if len(texts)!=len(set(texts)):
                raise serializers.ValidationError('No repita opciones dentro de una pregunta.')
        return attrs


def validity_dates(kind, starts=None, ends=None, now=None):
    now=now or timezone.now()
    local=timezone.localtime(now)
    tz=timezone.get_current_timezone()
    def midnight(day):
        return timezone.make_aware(datetime.combine(day,time.min),tz)
    if kind=='custom':
        if not starts or not ends or ends<=starts:
            raise serializers.ValidationError({'ends_at':'El rango requiere inicio y fin, con fin posterior al inicio.'})
        return starts,ends
    if kind=='always': return now,None
    if kind=='today': return now,midnight(local.date()+timedelta(days=1))
    if kind=='three_days': return now,now+timedelta(days=3)
    if kind=='week': return now,midnight(local.date()+timedelta(days=7-local.weekday()))
    if kind=='month':
        next_month=(local.date().replace(day=28)+timedelta(days=4)).replace(day=1)
        return now,midnight(next_month)
    raise serializers.ValidationError({'validity':'Modalidad de vigencia desconocida.'})
