from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    entity=models.CharField(max_length=50,blank=True,db_index=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=100, db_index=True)
    resource = models.CharField(max_length=150, blank=True)
    ip = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=500, blank=True)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


def record(request, action, resource='', metadata=None):
    from .context import client_context
    context=client_context(request)
    return AuditEvent.objects.create(actor=request.user if request.user.is_authenticated else None,
        action=action, entity=action.split('.')[0], resource=resource, ip=context['ip'],
        user_agent=context['user_agent'], metadata=metadata or {})
