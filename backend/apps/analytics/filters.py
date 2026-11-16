from django.db.models import Q
from django_filters import rest_framework as filters
from .models import AccessLog,SecurityAlert
from apps.audit.models import AuditEvent


class AccessFilter(filters.FilterSet):
    class Meta:
        model=AccessLog;fields=['uid','user_type','device','event_type','section','content']


class AuditFilter(filters.FilterSet):
    class Meta:
        model=AuditEvent;fields=['actor','action','entity']


def access_rows(params,period):
    from .periods import during,data_scope
    qs=data_scope(during(AccessLog.objects.all(),period),period)
    f=AccessFilter(params,queryset=qs);f.is_valid()
    if f.errors:
        from rest_framework.exceptions import ValidationError
        raise ValidationError(f.errors)
    qs=f.qs
    if params.get('search'):qs=qs.filter(Q(uid__icontains=params['search'])|Q(section__icontains=params['search'])|Q(user_agent__icontains=params['search']))
    ordering=params.get('ordering','-created_at')
    return qs.order_by(ordering if ordering.lstrip('-') in ['created_at','uid','device','section'] else '-created_at','-pk')
