from datetime import datetime,time,timedelta
from django.utils import timezone
from rest_framework import serializers


class PeriodSerializer(serializers.Serializer):
    period=serializers.ChoiceField(choices=['today','7d','30d','month','custom'],default='7d')
    date_from=serializers.DateField(required=False)
    date_to=serializers.DateField(required=False)
    data_scope=serializers.ChoiceField(choices=['real','demo','all'],default='real')

    def validate(self,attrs):
        if attrs['period']=='custom' and (not attrs.get('date_from') or not attrs.get('date_to') or attrs['date_to']<attrs['date_from']):
            raise serializers.ValidationError('El rango requiere dos fechas, con fin igual o posterior al inicio.')
        if attrs.get('date_to') and attrs['date_to'].year>=9999:
            raise serializers.ValidationError('La fecha final está fuera del rango admitido.')
        return attrs


def period_from(params,now=None):
    serializer=PeriodSerializer(data=params);serializer.is_valid(raise_exception=True)
    data=serializer.validated_data
    today=timezone.localtime(now or timezone.now()).date()
    end=today+timedelta(days=1)
    if data['period']=='today': start=today
    elif data['period']=='7d': start=today-timedelta(days=6)
    elif data['period']=='30d': start=today-timedelta(days=29)
    elif data['period']=='month': start=today.replace(day=1)
    else:start=data['date_from'];end=data['date_to']+timedelta(days=1)
    tz=timezone.get_current_timezone()
    return {'name':data['period'],'start':timezone.make_aware(datetime.combine(start,time.min),tz),
        'end':timezone.make_aware(datetime.combine(end,time.min),tz),'timezone':str(tz),'data_scope':data['data_scope']}


def during(qs,period,field='created_at'):
    return qs.filter(**{field+'__gte':period['start'],field+'__lt':period['end']})


def data_scope(qs,period):
    return qs if period['data_scope']=='all' else qs.filter(demo=period['data_scope']=='demo')
