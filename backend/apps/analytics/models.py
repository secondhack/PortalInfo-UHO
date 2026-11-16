from django.db import models


class AccessLog(models.Model):
    event_type=models.CharField(max_length=12,choices=[('access','Acceso'),('view','Visualización')],default='access',db_index=True)
    device=models.CharField(max_length=20,default='unknown')
    demo=models.BooleanField(default=False)
    seed_key=models.CharField(max_length=120,null=True,blank=True,unique=True)
    uid = models.CharField(max_length=150, blank=True)
    user_type = models.CharField(max_length=30, blank=True)
    ip = models.GenericIPAddressField()
    user_agent = models.CharField(max_length=500)
    section = models.CharField(max_length=100, blank=True)
    content = models.ForeignKey('content.Content', null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes=[models.Index(fields=['uid','created_at']),models.Index(fields=['event_type','created_at'])]


class ContentView(models.Model):
    access_log=models.OneToOneField(AccessLog,null=True,blank=True,on_delete=models.SET_NULL)
    category=models.ForeignKey('catalogs.Category',null=True,blank=True,on_delete=models.SET_NULL)
    uid=models.CharField(max_length=150,blank=True)
    user_type=models.CharField(max_length=30,default='anonimo')
    demo=models.BooleanField(default=False)
    seed_key=models.CharField(max_length=120,null=True,blank=True,unique=True)
    content = models.ForeignKey('content.Content', null=True, blank=True, on_delete=models.SET_NULL)
    section = models.CharField(max_length=100)
    ip = models.GenericIPAddressField()
    device = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)


class SecurityAlert(models.Model):
    uid=models.CharField(max_length=150,db_index=True)
    kind=models.CharField(max_length=30,choices=[('multiple_ips','Varias IP'),('device_churn','Cambio de dispositivos'),('activity_spike','Actividad inusual')])
    priority=models.CharField(max_length=10,choices=[('low','Baja'),('medium','Media'),('high','Alta')])
    window_start=models.DateTimeField()
    window_end=models.DateTimeField()
    evidence=models.JSONField(default=dict)
    event_key=models.CharField(max_length=64,unique=True)
    reviewed_at=models.DateTimeField(null=True,blank=True)
    reviewed_by=models.ForeignKey('accounts.User',null=True,blank=True,on_delete=models.SET_NULL)
    demo=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True,db_index=True)

    class Meta:
        indexes=[models.Index(fields=['priority','reviewed_at','created_at'])]
