from django.conf import settings
from django.db import models


class Approval(models.Model):
    proposal=models.JSONField(default=dict,blank=True)
    version = models.PositiveIntegerField(default=1)
    content = models.ForeignKey('content.Content', on_delete=models.PROTECT, related_name='approvals')
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='approval_requests')
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name='reviews')
    state = models.CharField(max_length=12, choices=[('pending','Pendiente'),('approved','Aprobado'),('rejected','Rechazado')], default='pending')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
