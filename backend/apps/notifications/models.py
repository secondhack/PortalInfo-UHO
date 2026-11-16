from django.conf import settings
from django.db import models


class Notification(models.Model):
    title = models.CharField(max_length=200, blank=True)
    resource_type = models.CharField(max_length=40, blank=True)
    resource_id = models.PositiveBigIntegerField(null=True, blank=True)
    event_key = models.CharField(max_length=150, null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    demo = models.BooleanField(default=False)
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=40)
    message = models.TextField()
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints=[models.UniqueConstraint(fields=['recipient','event_key'],name='unique_notification_event')]
        indexes=[models.Index(fields=['recipient','read','created_at'])]


class MailDelivery(models.Model):
    notification=models.OneToOneField(Notification,on_delete=models.CASCADE,related_name='mail_delivery')
    state=models.CharField(max_length=12,choices=[('pending','Pendiente'),('sent','Enviado'),('failed','Fallido')],default='pending')
    attempts=models.PositiveIntegerField(default=0)
    error_code=models.CharField(max_length=100,blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    sent_at=models.DateTimeField(null=True,blank=True)
